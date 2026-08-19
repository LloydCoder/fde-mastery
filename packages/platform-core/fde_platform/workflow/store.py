"""Workflow event-history and run persistence ports plus a deterministic reference store."""

from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock
from uuid import UUID

from .models import WorkflowEvent, WorkflowRun


class WorkflowStore(ABC):
    """Durable boundary for workflow projections and append-only history."""

    @abstractmethod
    def create_run(self, run: WorkflowRun) -> WorkflowRun:
        raise NotImplementedError

    @abstractmethod
    def get_run(self, workflow_run_id: UUID) -> WorkflowRun | None:
        raise NotImplementedError

    @abstractmethod
    def save_run(self, run: WorkflowRun) -> WorkflowRun:
        raise NotImplementedError

    @abstractmethod
    def append_event(self, event: WorkflowEvent, *, expected_sequence: int) -> WorkflowEvent:
        raise NotImplementedError

    @abstractmethod
    def list_events(self, workflow_run_id: UUID) -> tuple[WorkflowEvent, ...]:
        raise NotImplementedError


class InMemoryWorkflowStore(WorkflowStore):
    """Thread-safe reference implementation with optimistic event sequencing."""

    def __init__(self) -> None:
        self._runs: dict[UUID, WorkflowRun] = {}
        self._events: dict[UUID, list[WorkflowEvent]] = {}
        self._lock = RLock()

    def create_run(self, run: WorkflowRun) -> WorkflowRun:
        with self._lock:
            if run.workflow_run_id in self._runs:
                raise ValueError("workflow run already exists")
            if any(r.workflow_instance_id == run.workflow_instance_id for r in self._runs.values()):
                raise ValueError("workflow instance already exists")
            self._runs[run.workflow_run_id] = run.model_copy(deep=True)
            self._events[run.workflow_run_id] = []
            return run.model_copy(deep=True)

    def get_run(self, workflow_run_id: UUID) -> WorkflowRun | None:
        with self._lock:
            run = self._runs.get(workflow_run_id)
            return run.model_copy(deep=True) if run else None

    def save_run(self, run: WorkflowRun) -> WorkflowRun:
        with self._lock:
            if run.workflow_run_id not in self._runs:
                raise KeyError(f"unknown workflow run: {run.workflow_run_id}")
            self._runs[run.workflow_run_id] = run.model_copy(deep=True)
            return run.model_copy(deep=True)

    def append_event(self, event: WorkflowEvent, *, expected_sequence: int) -> WorkflowEvent:
        with self._lock:
            events = self._events.setdefault(event.workflow_run_id, [])
            actual = len(events)
            if actual != expected_sequence or event.sequence != expected_sequence:
                raise ValueError(
                    f"workflow history conflict: expected={expected_sequence}, actual={actual}"
                )
            events.append(event)
            return event

    def list_events(self, workflow_run_id: UUID) -> tuple[WorkflowEvent, ...]:
        with self._lock:
            return tuple(self._events.get(workflow_run_id, ()))
