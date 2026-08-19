from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fde_platform.workflow import (
    DurableWorkflowEngine,
    InMemoryWorkflowQueue,
    InMemoryWorkflowStore,
    RetryPolicy,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowStatus,
    WorkflowStep,
)
from fde_platform.workflow.engine import WorkflowWait
from fde_platform.workflow.queue import WorkflowTask


def build_engine(activities):
    definition = WorkflowDefinition(
        workflow_id="order-flow",
        version="1",
        steps=(
            WorkflowStep(step_id="first", activity="first"),
            WorkflowStep(step_id="second", activity="second"),
        ),
    )
    return (
        DurableWorkflowEngine(
            store=InMemoryWorkflowStore(),
            queue=InMemoryWorkflowQueue(),
            definitions={(definition.workflow_id, definition.version): definition},
            activities=activities,
        ),
        definition,
    )


def start(engine, definition, instance="instance-1"):
    return engine.start(
        definition,
        request_id="req-1",
        tenant_id="tenant-a",
        environment="staging",
        workflow_instance_id=instance,
        input={"order": "123"},
    )


def test_workflow_completes_and_is_replayable():
    engine, definition = build_engine(
        {
            "first": lambda run, step, state: {**state, "first": True},
            "second": lambda run, step, state: {**state, "done": True},
        }
    )
    run = start(engine, definition)

    engine.run_once()
    completed = engine.run_once()

    assert completed is not None
    assert completed.status == WorkflowStatus.COMPLETED
    assert completed.current_step == 2
    assert completed.state["done"] is True
    replayed = engine.replay(run.workflow_run_id)
    assert replayed.status == WorkflowStatus.COMPLETED
    assert replayed.current_step == 2
    assert [event.sequence for event in engine.store.list_events(run.workflow_run_id)] == list(range(6))


def test_retry_is_bounded_and_dead_letters_after_max_attempts():
    attempts = 0

    def failing(run: WorkflowRun, step: str, state):
        nonlocal attempts
        attempts += 1
        raise RuntimeError("provider unavailable")

    definition = WorkflowDefinition(
        workflow_id="retry-flow",
        version="1",
        steps=(WorkflowStep(
            step_id="one",
            activity="fail",
            retry_policy=RetryPolicy(max_attempts=2, initial_backoff_seconds=0, max_backoff_seconds=0),
        ),),
    )
    engine = DurableWorkflowEngine(
        store=InMemoryWorkflowStore(),
        queue=InMemoryWorkflowQueue(),
        definitions={(definition.workflow_id, definition.version): definition},
        activities={"fail": failing},
    )
    run = engine.start(
        definition,
        request_id="req-2",
        tenant_id="tenant-a",
        environment="staging",
        workflow_instance_id="retry-1",
    )
    engine.run_once()
    final = engine.run_once()

    assert final is not None
    assert final.status == WorkflowStatus.DEAD_LETTERED
    assert attempts == 2
    assert len(engine.dead_letters) == 1


def test_wait_signal_resumes_same_step():
    waiting = True

    def wait_or_finish(run, step, state):
        nonlocal waiting
        if waiting:
            waiting = False
            raise WorkflowWait("external approval", signal_name="approval")
        return {**state, "approved": True}

    engine, definition = build_engine({"first": wait_or_finish, "second": lambda r, s, st: st})
    run = start(engine, definition)
    first = engine.run_once()
    assert first is not None and first.status == WorkflowStatus.WAITING

    engine.signal(run.workflow_run_id, signal_name="approval", payload={"approved_by": "user-1"})
    engine.run_once()
    final = engine.run_once()
    assert final is not None and final.status == WorkflowStatus.COMPLETED
    assert final.state["approved"] is True


def test_cancel_is_terminal():
    engine, definition = build_engine({"first": lambda r, s, st: st, "second": lambda r, s, st: st})
    run = start(engine, definition, instance="cancel-1")
    cancelled = engine.cancel(run.workflow_run_id, reason="operator stop")
    assert cancelled.status == WorkflowStatus.CANCELLED
    assert engine.run_once() is None


def test_queue_lease_can_expire_and_be_reclaimed():
    queue = InMemoryWorkflowQueue()
    task = WorkflowTask(
        workflow_run_id=uuid4(),
        step_id="step",
        available_at=datetime.now(timezone.utc),
        idempotency_key="stable-key",
    )
    queue.enqueue(task)
    claimed = queue.claim(lease_seconds=1)
    assert claimed is not None
    assert queue.claim() is None
    expired = claimed.lease_until + timedelta(seconds=1)
    reclaimed = queue.claim(now=expired)
    assert reclaimed is not None
    assert reclaimed.task_id == task.task_id
    queue.ack(reclaimed.task_id)
    assert queue.claim(now=expired) is None
