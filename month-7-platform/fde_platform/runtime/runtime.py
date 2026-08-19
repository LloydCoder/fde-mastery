"""Bounded, cancellable execution runtime for domain and custom agents."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections.abc import Callable, Mapping
from typing import Any
from uuid import UUID

from ..contracts.execution import ExecutionContext
from .models import AgentRun, AgentRunStatus, ExecutionBudget, RunCheckpoint
from .store import InMemoryRunStore, RunStore


class AgentRuntimeError(RuntimeError):
    """Base exception for runtime-level failures."""


class RunCancelled(AgentRuntimeError):
    """Raised when execution is cancelled before completion."""


class RunLimitExceeded(AgentRuntimeError):
    """Raised when a hard runtime budget is exceeded."""


class AgentRuntime:
    """Execute an agent under explicit lifecycle, deadline, cancellation and budget controls.

    The runtime is deliberately synchronous in Build 3. It establishes the execution
    contract and safety invariants while leaving distributed workflow scheduling to Build 4.
    """

    def __init__(self, store: RunStore | None = None) -> None:
        self.store = store or InMemoryRunStore()
        self._cancellation: dict[UUID, threading.Event] = {}
        self._lock = threading.RLock()

    def create_run(
        self,
        *,
        request_id: str,
        tenant_id: str,
        environment: str,
        agent_id: str,
        agent_version: str = "current",
        budget: ExecutionBudget | None = None,
    ) -> AgentRun:
        run = AgentRun(
            request_id=request_id,
            tenant_id=tenant_id,
            environment=environment,
            agent_id=agent_id,
            agent_version=agent_version,
            budget=budget or ExecutionBudget(),
        )
        with self._lock:
            self.store.create(run)
            self._cancellation[run.run_id] = threading.Event()
        return run

    def cancel(self, run_id: UUID) -> AgentRun:
        with self._lock:
            run = self._require(run_id)
            if run.terminal:
                return run
            self._cancellation.setdefault(run_id, threading.Event()).set()
            if run.status == AgentRunStatus.CREATED:
                run.transition(AgentRunStatus.CANCELLED)
                return self.store.save(run)
            return run

    def get_run(self, run_id: UUID) -> AgentRun:
        return self._require(run_id)

    def checkpoint(self, run_id: UUID, state: Mapping[str, Any]) -> RunCheckpoint:
        run = self._require(run_id)
        if run.terminal:
            raise AgentRuntimeError("cannot checkpoint a terminal run")
        previous = self.store.latest_checkpoint(run_id)
        sequence = 0 if previous is None else previous.sequence + 1
        payload = self._canonical_json(state)
        checkpoint = RunCheckpoint(
            run_id=run_id,
            sequence=sequence,
            state=dict(state),
            state_hash=hashlib.sha256(payload).hexdigest(),
        )
        return self.store.save_checkpoint(checkpoint)

    def execute(
        self,
        run_id: UUID,
        agent: Callable[[Mapping[str, Any], ExecutionContext], Any],
        payload: Mapping[str, Any],
    ) -> AgentRun:
        run = self._require(run_id)
        if run.terminal:
            raise AgentRuntimeError("cannot execute a terminal run")
        cancellation = self._cancellation.setdefault(run_id, threading.Event())
        if cancellation.is_set():
            run.transition(AgentRunStatus.CANCELLED)
            return self.store.save(run)

        run.transition(AgentRunStatus.RUNNING)
        self.store.save(run)
        started = time.monotonic()
        context = ExecutionContext(
            request_id=run.request_id,
            tenant_id=run.tenant_id,
            environment=run.environment,
            attributes={"run_id": str(run.run_id), "agent_id": run.agent_id},
        )

        try:
            self._guard(run, cancellation, started)
            if run.step_count >= run.budget.max_steps:
                raise RunLimitExceeded("execution step budget exceeded")
            run.increment_step()
            result = agent(payload, context)
            self._guard(run, cancellation, started)
            if self._serialized_size(result) > run.budget.max_output_bytes:
                raise RunLimitExceeded("execution output byte budget exceeded")
            run.result = result
            run.transition(AgentRunStatus.COMPLETED)
        except RunCancelled as exc:
            run.error_type = type(exc).__name__
            run.error_message = str(exc)
            run.transition(AgentRunStatus.CANCELLED)
        except RunLimitExceeded as exc:
            run.error_type = type(exc).__name__
            run.error_message = str(exc)
            run.transition(
                AgentRunStatus.TIMED_OUT if "time" in str(exc).lower() else AgentRunStatus.LIMIT_EXCEEDED
            )
        except Exception as exc:  # noqa: BLE001 - runtime records the failure envelope deliberately.
            run.error_type = type(exc).__name__
            run.error_message = str(exc)[:1024]
            run.transition(AgentRunStatus.FAILED)
        finally:
            self.store.save(run)
        return run

    def execute_domain(self, run_id: UUID, agent: Any, payload: Mapping[str, Any]) -> AgentRun:
        """Run an existing DomainAgent without coupling the runtime to domain implementations."""

        if not callable(getattr(agent, "evaluate", None)):
            raise TypeError("agent must expose evaluate(payload)")
        return self.execute(run_id, lambda data, _context: agent.evaluate(dict(data)), payload)

    def _guard(self, run: AgentRun, cancellation: threading.Event, started: float) -> None:
        if cancellation.is_set():
            raise RunCancelled("execution cancelled")
        if time.monotonic() - started >= run.budget.max_seconds:
            raise RunLimitExceeded("execution time budget exceeded")
        if run.step_count > run.budget.max_steps:
            raise RunLimitExceeded("execution step budget exceeded")

    def _require(self, run_id: UUID) -> AgentRun:
        run = self.store.get(run_id)
        if run is None:
            raise KeyError(f"unknown run: {run_id}")
        return run

    @staticmethod
    def _canonical_json(value: Mapping[str, Any]) -> bytes:
        try:
            return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise AgentRuntimeError("checkpoint state is not serializable") from exc

    @staticmethod
    def _serialized_size(value: Any) -> int:
        return len(json.dumps(value, sort_keys=True, default=str).encode("utf-8"))
