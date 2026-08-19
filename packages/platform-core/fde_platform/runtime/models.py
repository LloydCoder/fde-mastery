"""Immutable and validated state models for agent execution."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentRunStatus(str, Enum):
    """Explicit lifecycle for a single agent execution."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    LIMIT_EXCEEDED = "limit_exceeded"


_TERMINAL = frozenset(
    {
        AgentRunStatus.COMPLETED,
        AgentRunStatus.FAILED,
        AgentRunStatus.CANCELLED,
        AgentRunStatus.TIMED_OUT,
        AgentRunStatus.LIMIT_EXCEEDED,
    }
)

_ALLOWED_TRANSITIONS = {
    AgentRunStatus.CREATED: frozenset({AgentRunStatus.RUNNING, AgentRunStatus.CANCELLED}),
    AgentRunStatus.RUNNING: frozenset(
        {
            AgentRunStatus.COMPLETED,
            AgentRunStatus.FAILED,
            AgentRunStatus.CANCELLED,
            AgentRunStatus.TIMED_OUT,
            AgentRunStatus.LIMIT_EXCEEDED,
        }
    ),
    AgentRunStatus.COMPLETED: frozenset(),
    AgentRunStatus.FAILED: frozenset(),
    AgentRunStatus.CANCELLED: frozenset(),
    AgentRunStatus.TIMED_OUT: frozenset(),
    AgentRunStatus.LIMIT_EXCEEDED: frozenset(),
}


class ExecutionBudget(BaseModel):
    """Hard limits applied by the runtime, independent of model/provider behavior."""

    model_config = ConfigDict(frozen=True)

    max_steps: int = Field(default=1, ge=1, le=1000)
    max_seconds: float = Field(default=60.0, gt=0, le=86_400)
    max_output_bytes: int = Field(default=1_048_576, ge=1, le=10_485_760)


class RunCheckpoint(BaseModel):
    """Versioned, integrity-addressable execution checkpoint."""

    model_config = ConfigDict(frozen=True)

    run_id: UUID
    sequence: int = Field(ge=0)
    state: Mapping[str, Any] = Field(default_factory=dict)
    state_hash: str = Field(min_length=64, max_length=64)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentRun(BaseModel):
    """First-class execution record shared across runtime boundaries."""

    model_config = ConfigDict(validate_assignment=True)

    run_id: UUID = Field(default_factory=uuid4)
    request_id: str = Field(min_length=1, max_length=128)
    tenant_id: str = Field(min_length=1, max_length=128)
    environment: str = Field(min_length=1, max_length=32)
    agent_id: str = Field(min_length=1, max_length=128)
    agent_version: str = Field(default="current", min_length=1, max_length=128)
    status: AgentRunStatus = AgentRunStatus.CREATED
    step_count: int = Field(default=0, ge=0)
    budget: ExecutionBudget = Field(default_factory=ExecutionBudget)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_type: str | None = None
    error_message: str | None = None
    result: Any = None

    @property
    def terminal(self) -> bool:
        return self.status in _TERMINAL

    def transition(self, target: AgentRunStatus) -> None:
        if target not in _ALLOWED_TRANSITIONS[self.status]:
            raise ValueError(f"invalid run transition: {self.status.value} -> {target.value}")
        self.status = target
        now = datetime.now(timezone.utc)
        if target == AgentRunStatus.RUNNING and self.started_at is None:
            self.started_at = now
        if target in _TERMINAL:
            self.completed_at = now

    @field_validator("request_id", "tenant_id", "agent_id", "agent_version", "environment")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value

    def increment_step(self) -> None:
        if self.step_count >= self.budget.max_steps:
            raise ValueError("execution step budget exceeded")
        self.step_count += 1
