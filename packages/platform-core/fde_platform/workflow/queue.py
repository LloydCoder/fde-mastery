"""Leased durable-task queue contracts with a deterministic reference adapter."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from threading import RLock
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class WorkflowTask:
    workflow_run_id: UUID
    step_id: str
    available_at: datetime
    attempt: int = 1
    idempotency_key: str = ""
    task_id: UUID = field(default_factory=uuid4)
    lease_until: datetime | None = None


class WorkflowQueue(ABC):
    """Queue boundary with explicit lease/ack semantics for crash recovery."""

    @abstractmethod
    def enqueue(self, task: WorkflowTask) -> None:
        raise NotImplementedError

    @abstractmethod
    def claim(self, *, now: datetime | None = None, lease_seconds: float = 60.0) -> WorkflowTask | None:
        raise NotImplementedError

    @abstractmethod
    def ack(self, task_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    def release(self, task_id: UUID, *, available_at: datetime) -> None:
        raise NotImplementedError


class InMemoryWorkflowQueue(WorkflowQueue):
    """Thread-safe FIFO-by-due-time queue with lease expiry and acknowledgements."""

    def __init__(self) -> None:
        self._tasks: dict[UUID, WorkflowTask] = {}
        self._lock = RLock()

    def enqueue(self, task: WorkflowTask) -> None:
        if not task.idempotency_key:
            raise ValueError("workflow task requires an idempotency key")
        with self._lock:
            if any(existing.idempotency_key == task.idempotency_key for existing in self._tasks.values()):
                return
            self._tasks[task.task_id] = task

    def claim(self, *, now: datetime | None = None, lease_seconds: float = 60.0) -> WorkflowTask | None:
        current = now or datetime.now(timezone.utc)
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        with self._lock:
            candidates = sorted(self._tasks.values(), key=lambda item: item.available_at)
            for task in candidates:
                if task.available_at > current:
                    continue
                if task.lease_until is not None and task.lease_until > current:
                    continue
                leased = replace(task, lease_until=current + timedelta(seconds=lease_seconds))
                self._tasks[task.task_id] = leased
                return leased
        return None

    def ack(self, task_id: UUID) -> None:
        with self._lock:
            self._tasks.pop(task_id, None)

    def release(self, task_id: UUID, *, available_at: datetime) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is not None:
                self._tasks[task_id] = replace(task, available_at=available_at, lease_until=None)
