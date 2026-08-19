"""Durable-task queue contracts with an in-memory reference implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from uuid import UUID


@dataclass(frozen=True, slots=True)
class WorkflowTask:
    workflow_run_id: UUID
    step_id: str
    available_at: datetime
    attempt: int = 1
    idempotency_key: str = ""


class WorkflowQueue(ABC):
    """Queue boundary; production adapters must provide durable delivery."""

    @abstractmethod
    def enqueue(self, task: WorkflowTask) -> None:
        raise NotImplementedError

    @abstractmethod
    def claim(self, *, now: datetime | None = None) -> WorkflowTask | None:
        raise NotImplementedError


class InMemoryWorkflowQueue(WorkflowQueue):
    """Deterministic FIFO-by-due-time queue used by tests and local development."""

    def __init__(self) -> None:
        self._tasks: list[WorkflowTask] = []
        self._lock = RLock()

    def enqueue(self, task: WorkflowTask) -> None:
        if not task.idempotency_key:
            raise ValueError("workflow task requires an idempotency key")
        with self._lock:
            if any(existing.idempotency_key == task.idempotency_key for existing in self._tasks):
                return
            self._tasks.append(task)
            self._tasks.sort(key=lambda item: item.available_at)

    def claim(self, *, now: datetime | None = None) -> WorkflowTask | None:
        current = now or datetime.now(timezone.utc)
        with self._lock:
            for index, task in enumerate(self._tasks):
                if task.available_at <= current:
                    return self._tasks.pop(index)
        return None
