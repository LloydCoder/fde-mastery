"""Deterministic, versioned workflow state and event contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkflowStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    DEAD_LETTERED = "dead_lettered"


class WorkflowStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class RetryPolicy(BaseModel):
    """Explicit retry policy for side-effecting activities."""

    model_config = ConfigDict(frozen=True)

    max_attempts: int = Field(default=3, ge=1, le=20)
    initial_backoff_seconds: float = Field(default=1.0, ge=0, le=86_400)
    max_backoff_seconds: float = Field(default=300.0, ge=0, le=86_400)
    multiplier: float = Field(default=2.0, ge=1, le=10)

    def delay_for_attempt(self, attempt: int) -> float:
        if attempt < 1:
            raise ValueError("attempt must be >= 1")
        return min(
            self.max_backoff_seconds,
            self.initial_backoff_seconds * (self.multiplier ** (attempt - 1)),
        )


class WorkflowStep(BaseModel):
    """Declarative step; side effects execute only through the activity registry."""

    model_config = ConfigDict(frozen=True)

    step_id: str = Field(min_length=1, max_length=128)
    activity: str = Field(min_length=1, max_length=128)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    timeout_seconds: float = Field(default=300.0, gt=0, le=86_400)

    @field_validator("step_id", "activity")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class WorkflowDefinition(BaseModel):
    """Immutable workflow definition pinned to a version for safe replay."""

    model_config = ConfigDict(frozen=True)

    workflow_id: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=128)
    steps: tuple[WorkflowStep, ...] = Field(min_length=1, max_length=1000)

    @field_validator("workflow_id", "version")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class WorkflowEvent(BaseModel):
    """Append-only fact used to reconstruct workflow state after a crash."""

    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=uuid4)
    workflow_run_id: UUID
    sequence: int = Field(ge=0)
    event_type: str = Field(min_length=1, max_length=128)
    step_id: str | None = Field(default=None, max_length=128)
    payload: Mapping[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkflowRun(BaseModel):
    """Durable workflow identity and current projection."""

    model_config = ConfigDict(validate_assignment=True)

    workflow_run_id: UUID = Field(default_factory=uuid4)
    workflow_instance_id: str = Field(min_length=1, max_length=128)
    request_id: str = Field(min_length=1, max_length=128)
    tenant_id: str = Field(min_length=1, max_length=128)
    environment: str = Field(min_length=1, max_length=32)
    workflow_id: str = Field(min_length=1, max_length=128)
    workflow_version: str = Field(min_length=1, max_length=128)
    status: WorkflowStatus = WorkflowStatus.CREATED
    current_step: int = Field(default=0, ge=0)
    step_attempt: int = Field(default=0, ge=0)
    input: Mapping[str, Any] = Field(default_factory=dict)
    state: Mapping[str, Any] = Field(default_factory=dict)
    result: Any = None
    error_type: str | None = None
    error_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    @property
    def terminal(self) -> bool:
        return self.status in {
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
            WorkflowStatus.TIMED_OUT,
            WorkflowStatus.DEAD_LETTERED,
        }

    def transition(self, target: WorkflowStatus) -> None:
        allowed = {
            WorkflowStatus.CREATED: {WorkflowStatus.RUNNING, WorkflowStatus.CANCELLED},
            WorkflowStatus.RUNNING: {
                WorkflowStatus.WAITING,
                WorkflowStatus.COMPLETED,
                WorkflowStatus.FAILED,
                WorkflowStatus.CANCELLED,
                WorkflowStatus.TIMED_OUT,
                WorkflowStatus.DEAD_LETTERED,
            },
            WorkflowStatus.WAITING: {
                WorkflowStatus.RUNNING,
                WorkflowStatus.CANCELLED,
                WorkflowStatus.TIMED_OUT,
            },
        }
        if target not in allowed.get(self.status, set()):
            raise ValueError(f"invalid workflow transition: {self.status.value} -> {target.value}")
        self.status = target
        self.updated_at = datetime.now(timezone.utc)
        if self.terminal:
            self.completed_at = self.updated_at
