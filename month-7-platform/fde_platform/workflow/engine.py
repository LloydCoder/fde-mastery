"""Durable workflow engine using append-only history and at-least-once activities."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from .models import WorkflowDefinition, WorkflowEvent, WorkflowRun, WorkflowStatus
from .queue import WorkflowQueue, WorkflowTask
from .store import WorkflowStore

Activity = Callable[[WorkflowRun, str, Mapping[str, Any]], Any]


class WorkflowWait(Exception):
    """Raised by an activity when durable external input is required."""

    def __init__(self, reason: str, *, signal_name: str) -> None:
        super().__init__(reason)
        self.signal_name = signal_name
        self.reason = reason


class DurableWorkflowEngine:
    """Small durable-execution kernel suitable for later queue/DB adapters.

    Workflow decisions are reconstructed from committed events. Activities are
    intentionally at-least-once: callers must make external side effects
    idempotent using the supplied workflow/step identity.
    """

    def __init__(
        self,
        store: WorkflowStore,
        queue: WorkflowQueue,
        definitions: Mapping[tuple[str, str], WorkflowDefinition],
        activities: Mapping[str, Activity],
    ) -> None:
        self.store = store
        self.queue = queue
        self.definitions = definitions
        self.activities = activities
        self.dead_letters: list[WorkflowTask] = []

    def start(
        self,
        definition: WorkflowDefinition,
        *,
        request_id: str,
        tenant_id: str,
        environment: str,
        workflow_instance_id: str,
        input: Mapping[str, Any] | None = None,
    ) -> WorkflowRun:
        if (definition.workflow_id, definition.version) not in self.definitions:
            raise ValueError("workflow definition is not registered")
        run = WorkflowRun(
            workflow_instance_id=workflow_instance_id,
            request_id=request_id,
            tenant_id=tenant_id,
            environment=environment,
            workflow_id=definition.workflow_id,
            workflow_version=definition.version,
            input=dict(input or {}),
        )
        self.store.create_run(run)
        self._append(run, "WorkflowStarted", payload={"input": dict(run.input)})
        run.transition(WorkflowStatus.RUNNING)
        self.store.save_run(run)
        self._enqueue_current(run, attempt=1)
        return run

    def run_once(self, *, now: datetime | None = None) -> WorkflowRun | None:
        task = self.queue.claim(now=now)
        if task is None:
            return None
        run = self.store.get_run(task.workflow_run_id)
        if run is None or run.terminal:
            return run
        definition = self._definition(run)
        step = next((item for item in definition.steps if item.step_id == task.step_id), None)
        if step is None:
            return self._fail(run, "WorkflowDefinitionError", "queued step is not in pinned definition")
        if run.status == WorkflowStatus.WAITING:
            run.transition(WorkflowStatus.RUNNING)
        if run.status == WorkflowStatus.CREATED:
            run.transition(WorkflowStatus.RUNNING)
        self._append(run, "StepStarted", step_id=step.step_id, payload={"attempt": task.attempt})
        self.store.save_run(run)
        activity = self.activities.get(step.activity)
        if activity is None:
            return self._fail(run, "ActivityNotFound", f"activity not registered: {step.activity}")
        try:
            result = activity(run.model_copy(deep=True), step.step_id, dict(run.state))
        except WorkflowWait as exc:
            run.transition(WorkflowStatus.WAITING)
            self._append(
                run,
                "WorkflowWaiting",
                step_id=step.step_id,
                payload={"signal_name": exc.signal_name, "reason": exc.reason, "attempt": task.attempt},
            )
            self.store.save_run(run)
            return run
        except Exception as exc:  # activity boundary deliberately captures worker failures
            if task.attempt < step.retry_policy.max_attempts:
                delay = step.retry_policy.delay_for_attempt(task.attempt)
                run.step_attempt = task.attempt
                self._append(
                    run,
                    "StepRetryScheduled",
                    step_id=step.step_id,
                    payload={"attempt": task.attempt, "next_attempt": task.attempt + 1, "delay_seconds": delay},
                )
                self.store.save_run(run)
                self.queue.enqueue(
                    WorkflowTask(
                        workflow_run_id=run.workflow_run_id,
                        step_id=step.step_id,
                        attempt=task.attempt + 1,
                        available_at=datetime.now(timezone.utc) + timedelta(seconds=delay),
                        idempotency_key=f"{run.workflow_run_id}:{step.step_id}:{task.attempt + 1}",
                    )
                )
                return run
            self.dead_letters.append(task)
            return self._fail(run, type(exc).__name__, str(exc), dead_lettered=True)

        run.state = dict(result) if isinstance(result, Mapping) else dict(run.state)
        self._append(run, "StepCompleted", step_id=step.step_id, payload={"attempt": task.attempt, "result": result})
        run.current_step += 1
        run.step_attempt = 0
        if run.current_step >= len(definition.steps):
            run.result = result
            run.transition(WorkflowStatus.COMPLETED)
            self._append(run, "WorkflowCompleted", payload={"result": result})
            return self.store.save_run(run)
        self.store.save_run(run)
        self._enqueue_current(run, attempt=1)
        return run

    def cancel(self, workflow_run_id: UUID, *, reason: str = "cancelled by operator") -> WorkflowRun:
        run = self._require_run(workflow_run_id)
        if not run.terminal:
            run.transition(WorkflowStatus.CANCELLED)
            run.error_type = "Cancelled"
            run.error_message = reason
            self._append(run, "WorkflowCancelled", payload={"reason": reason})
            self.store.save_run(run)
        return run

    def signal(self, workflow_run_id: UUID, *, signal_name: str, payload: Mapping[str, Any] | None = None) -> WorkflowRun:
        run = self._require_run(workflow_run_id)
        if run.status != WorkflowStatus.WAITING:
            raise ValueError("workflow is not waiting for an external signal")
        self._append(run, "SignalReceived", payload={"signal_name": signal_name, "payload": dict(payload or {})})
        run.state = {**run.state, f"signal:{signal_name}": dict(payload or {})}
        run.transition(WorkflowStatus.RUNNING)
        self.store.save_run(run)
        self._enqueue_current(run, attempt=max(1, run.step_attempt))
        return run

    def replay(self, workflow_run_id: UUID) -> WorkflowRun:
        """Reconstruct the durable projection from its immutable event history."""
        run = self._require_run(workflow_run_id)
        events = self.store.list_events(workflow_run_id)
        if not events:
            raise ValueError("workflow has no durable history")
        expected = 0
        projection = run.model_copy(deep=True)
        for event in events:
            if event.sequence != expected:
                raise ValueError("workflow history sequence is corrupt")
            expected += 1
            if event.event_type == "WorkflowCompleted":
                projection.status = WorkflowStatus.COMPLETED
                projection.result = event.payload.get("result")
            elif event.event_type == "WorkflowCancelled":
                projection.status = WorkflowStatus.CANCELLED
            elif event.event_type == "WorkflowWaiting":
                projection.status = WorkflowStatus.WAITING
            elif event.event_type == "StepCompleted":
                projection.current_step += 1
            elif event.event_type in {"WorkflowFailed", "WorkflowDeadLettered"}:
                projection.status = WorkflowStatus.DEAD_LETTERED if event.event_type.endswith("DeadLettered") else WorkflowStatus.FAILED
                projection.error_type = str(event.payload.get("error_type", "WorkflowFailure"))
                projection.error_message = str(event.payload.get("error_message", ""))
            elif event.event_type == "WorkflowStarted":
                projection.input = dict(event.payload.get("input", {}))
        return projection

    def _enqueue_current(self, run: WorkflowRun, *, attempt: int) -> None:
        definition = self._definition(run)
        if run.current_step >= len(definition.steps):
            return
        step = definition.steps[run.current_step]
        self.queue.enqueue(
            WorkflowTask(
                workflow_run_id=run.workflow_run_id,
                step_id=step.step_id,
                attempt=attempt,
                available_at=datetime.now(timezone.utc),
                idempotency_key=f"{run.workflow_run_id}:{step.step_id}:{attempt}:{uuid4()}",
            )
        )

    def _definition(self, run: WorkflowRun) -> WorkflowDefinition:
        try:
            return self.definitions[(run.workflow_id, run.workflow_version)]
        except KeyError as exc:
            raise ValueError("pinned workflow definition is unavailable") from exc

    def _append(self, run: WorkflowRun, event_type: str, *, step_id: str | None = None, payload: Mapping[str, Any] | None = None) -> None:
        sequence = len(self.store.list_events(run.workflow_run_id))
        self.store.append_event(
            WorkflowEvent(
                workflow_run_id=run.workflow_run_id,
                sequence=sequence,
                event_type=event_type,
                step_id=step_id,
                payload=dict(payload or {}),
            ),
            expected_sequence=sequence,
        )

    def _fail(self, run: WorkflowRun, error_type: str, message: str, *, dead_lettered: bool = False) -> WorkflowRun:
        target = WorkflowStatus.DEAD_LETTERED if dead_lettered else WorkflowStatus.FAILED
        run.transition(target)
        run.error_type = error_type
        run.error_message = message[:1000]
        self._append(
            run,
            "WorkflowDeadLettered" if dead_lettered else "WorkflowFailed",
            payload={"error_type": error_type, "error_message": message[:1000]},
        )
        return self.store.save_run(run)

    def _require_run(self, workflow_run_id: UUID) -> WorkflowRun:
        run = self.store.get_run(workflow_run_id)
        if run is None:
            raise KeyError(f"unknown workflow run: {workflow_run_id}")
        return run
