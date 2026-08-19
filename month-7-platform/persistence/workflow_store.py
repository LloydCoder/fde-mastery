"""PostgreSQL adapter for durable workflow runs and append-only history."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, Text, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from fde_platform.workflow.models import WorkflowEvent, WorkflowRun, WorkflowStatus
from fde_platform.workflow.store import WorkflowStore


class WorkflowBase(DeclarativeBase):
    pass


class WorkflowRunRow(WorkflowBase):
    __tablename__ = "fde_workflow_runs"

    workflow_run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_instance_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(63), nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String(32), nullable=False)
    workflow_id: Mapped[str] = mapped_column(String(128), nullable=False)
    workflow_version: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    step_attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    state_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkflowEventRow(WorkflowBase):
    __tablename__ = "fde_workflow_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_run_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    tenant_id: Mapped[str] = mapped_column(String(63), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    step_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PostgreSQLWorkflowStore(WorkflowStore):
    """Tenant-scoped PostgreSQL workflow store.

    The adapter requires a trusted tenant context at construction time and
    also relies on database RLS as a second isolation boundary.
    """

    def __init__(self, database_url: str | None = None, *, tenant_id: str) -> None:
        url = database_url or os.getenv("FDE_DATABASE_URL")
        if not url:
            raise ValueError("FDE_DATABASE_URL is required for PostgreSQL workflow storage")
        if not tenant_id.strip():
            raise ValueError("tenant_id is required")
        self.tenant_id = tenant_id
        self.engine = create_engine(url, pool_pre_ping=True)

    def _session(self) -> Session:
        session = Session(self.engine)
        session.execute(text("SET LOCAL fde.tenant_id = :tenant_id"), {"tenant_id": self.tenant_id})
        return session

    @staticmethod
    def _to_row(run: WorkflowRun) -> WorkflowRunRow:
        return WorkflowRunRow(
            workflow_run_id=str(run.workflow_run_id),
            workflow_instance_id=run.workflow_instance_id,
            request_id=run.request_id,
            tenant_id=run.tenant_id,
            environment=run.environment,
            workflow_id=run.workflow_id,
            workflow_version=run.workflow_version,
            status=run.status.value,
            current_step=run.current_step,
            step_attempt=run.step_attempt,
            input_json=json.dumps(run.input, separators=(",", ":")),
            state_json=json.dumps(run.state, separators=(",", ":")),
            result_json=json.dumps(run.result, separators=(",", ":")) if run.result is not None else None,
            error_type=run.error_type,
            error_message=run.error_message,
            created_at=run.created_at,
            updated_at=run.updated_at,
            completed_at=run.completed_at,
        )

    @staticmethod
    def _from_row(row: WorkflowRunRow) -> WorkflowRun:
        return WorkflowRun(
            workflow_run_id=UUID(row.workflow_run_id),
            workflow_instance_id=row.workflow_instance_id,
            request_id=row.request_id,
            tenant_id=row.tenant_id,
            environment=row.environment,
            workflow_id=row.workflow_id,
            workflow_version=row.workflow_version,
            status=WorkflowStatus(row.status),
            current_step=row.current_step,
            step_attempt=row.step_attempt,
            input=json.loads(row.input_json),
            state=json.loads(row.state_json),
            result=json.loads(row.result_json) if row.result_json is not None else None,
            error_type=row.error_type,
            error_message=row.error_message,
            created_at=row.created_at,
            updated_at=row.updated_at,
            completed_at=row.completed_at,
        )

    def create_run(self, run: WorkflowRun) -> WorkflowRun:
        if run.tenant_id != self.tenant_id:
            raise PermissionError("workflow tenant does not match store tenant")
        with self._session() as session:
            session.add(self._to_row(run))
            session.commit()
        return run.model_copy(deep=True)

    def get_run(self, workflow_run_id: UUID) -> WorkflowRun | None:
        with self._session() as session:
            row = session.get(WorkflowRunRow, str(workflow_run_id))
            return self._from_row(row) if row else None

    def save_run(self, run: WorkflowRun) -> WorkflowRun:
        if run.tenant_id != self.tenant_id:
            raise PermissionError("workflow tenant does not match store tenant")
        with self._session() as session:
            row = session.get(WorkflowRunRow, str(run.workflow_run_id))
            if row is None:
                raise KeyError(f"unknown workflow run: {run.workflow_run_id}")
            values = self._to_row(run)
            for column in (
                "status", "current_step", "step_attempt", "input_json", "state_json",
                "result_json", "error_type", "error_message", "updated_at", "completed_at",
            ):
                setattr(row, column, getattr(values, column))
            session.commit()
        return run.model_copy(deep=True)

    def append_event(self, event: WorkflowEvent, *, expected_sequence: int) -> WorkflowEvent:
        with self._session() as session:
            latest = session.scalar(
                select(WorkflowEventRow.sequence)
                .where(WorkflowEventRow.workflow_run_id == str(event.workflow_run_id))
                .order_by(WorkflowEventRow.sequence.desc())
                .limit(1)
            )
            actual = 0 if latest is None else int(latest) + 1
            if actual != expected_sequence or event.sequence != expected_sequence:
                raise ValueError(f"workflow history conflict: expected={expected_sequence}, actual={actual}")
            session.add(
                WorkflowEventRow(
                    event_id=str(event.event_id),
                    workflow_run_id=str(event.workflow_run_id),
                    tenant_id=self.tenant_id,
                    sequence=event.sequence,
                    event_type=event.event_type,
                    step_id=event.step_id,
                    payload_json=json.dumps(event.payload, separators=(",", ":"), default=str),
                    created_at=event.created_at,
                )
            )
            session.commit()
        return event

    def list_events(self, workflow_run_id: UUID) -> tuple[WorkflowEvent, ...]:
        with self._session() as session:
            rows = session.scalars(
                select(WorkflowEventRow)
                .where(WorkflowEventRow.workflow_run_id == str(workflow_run_id))
                .order_by(WorkflowEventRow.sequence.asc())
            ).all()
            return tuple(
                WorkflowEvent(
                    event_id=UUID(row.event_id),
                    workflow_run_id=UUID(row.workflow_run_id),
                    sequence=row.sequence,
                    event_type=row.event_type,
                    step_id=row.step_id,
                    payload=json.loads(row.payload_json),
                    created_at=row.created_at,
                )
                for row in rows
            )
