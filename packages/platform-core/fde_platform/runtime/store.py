"""Storage ports and in-memory reference adapter for execution state."""

from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock
from typing import Dict
from uuid import UUID

from .models import AgentRun, RunCheckpoint


class RunStore(ABC):
    """Port for run and checkpoint persistence.

    Production adapters may back this port with PostgreSQL or another durable store.
    The runtime never depends on a concrete database implementation.
    """

    @abstractmethod
    def create(self, run: AgentRun) -> AgentRun:
        raise NotImplementedError

    @abstractmethod
    def get(self, run_id: UUID) -> AgentRun | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, run: AgentRun) -> AgentRun:
        raise NotImplementedError

    @abstractmethod
    def save_checkpoint(self, checkpoint: RunCheckpoint) -> RunCheckpoint:
        raise NotImplementedError

    @abstractmethod
    def latest_checkpoint(self, run_id: UUID) -> RunCheckpoint | None:
        raise NotImplementedError


class InMemoryRunStore(RunStore):
    """Thread-safe reference adapter used for tests and local development."""

    def __init__(self) -> None:
        self._runs: Dict[UUID, AgentRun] = {}
        self._checkpoints: Dict[UUID, RunCheckpoint] = {}
        self._lock = RLock()

    def create(self, run: AgentRun) -> AgentRun:
        with self._lock:
            if run.run_id in self._runs:
                raise ValueError("run already exists")
            self._runs[run.run_id] = run.model_copy(deep=True)
            return self._runs[run.run_id].model_copy(deep=True)

    def get(self, run_id: UUID) -> AgentRun | None:
        with self._lock:
            run = self._runs.get(run_id)
            return run.model_copy(deep=True) if run else None

    def save(self, run: AgentRun) -> AgentRun:
        with self._lock:
            if run.run_id not in self._runs:
                raise KeyError(f"unknown run: {run.run_id}")
            self._runs[run.run_id] = run.model_copy(deep=True)
            return self._runs[run.run_id].model_copy(deep=True)

    def save_checkpoint(self, checkpoint: RunCheckpoint) -> RunCheckpoint:
        with self._lock:
            current = self._checkpoints.get(checkpoint.run_id)
            if current and checkpoint.sequence <= current.sequence:
                raise ValueError("checkpoint sequence must increase monotonically")
            self._checkpoints[checkpoint.run_id] = checkpoint
            return checkpoint

    def latest_checkpoint(self, run_id: UUID) -> RunCheckpoint | None:
        with self._lock:
            return self._checkpoints.get(run_id)
