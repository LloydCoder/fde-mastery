"""PostgreSQL leased queue adapter for durable workflow workers."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, create_engine, select, text, update
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from fde_platform.workflow.queue import WorkflowQueue, WorkflowTask


class WorkflowQueueBase(DeclarativeBase):
    pass


class WorkflowTaskRow(WorkflowQueueBase):
    __tablename__ = "fde_workflow_tasks"

    task_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(63), nullable=False, index=True)
    step_id: Mapped[str] = mapped_column(String(128), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PostgreSQLWorkflowQueue(WorkflowQueue):
    """Tenant-scoped PostgreSQL queue using transactional row leases."""

    def __init__(self, database_url: str, *, tenant_id: str) -> None:
        if not tenant_id.strip():
            raise ValueError("tenant_id is required")
        self.tenant_id = tenant_id
        self.engine = create_engine(database_url, pool_pre_ping=True)

    def _session(self) -> Session:
        session = Session(self.engine)
        session.execute(text("SET LOCAL fde.tenant_id = :tenant_id"), {"tenant_id": self.tenant_id})
        return session

    def enqueue(self, task: WorkflowTask) -> None:
        now = datetime.now(timezone.utc)
        with self._session() as session:
            session.add(
                WorkflowTaskRow(
                    task_id=str(task.task_id),
                    workflow_run_id=str(task.workflow_run_id),
                    tenant_id=self.tenant_id,
                    step_id=task.step_id,
                    attempt=task.attempt,
                    idempotency_key=task.idempotency_key,
                    available_at=task.available_at,
                    lease_until=task.lease_until,
                    created_at=now,
                )
            )
            try:
                session.commit()
            except Exception as exc:
                session.rollback()
                # Duplicate idempotency is an intentional no-op.
                if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
                    return
                raise

    def claim(self, *, now: datetime | None = None, lease_seconds: float = 60.0) -> WorkflowTask | None:
        current = now or datetime.now(timezone.utc)
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        with self._session() as session:
            row = session.scalars(
                select(WorkflowTaskRow)
                .where(WorkflowTaskRow.available_at <= current)
                .where((WorkflowTaskRow.lease_until.is_(None)) | (WorkflowTaskRow.lease_until <= current))
                .order_by(WorkflowTaskRow.available_at.asc(), WorkflowTaskRow.created_at.asc())
                .with_for_update(skip_locked=True)
                .limit(1)
            ).first()
            if row is None:
                return None
            lease_until = current.replace(microsecond=current.microsecond) + __import__("datetime").timedelta(seconds=lease_seconds)
            row.lease_until = lease_until
            session.commit()
            return WorkflowTask(
                workflow_run_id=UUID(row.workflow_run_id),
                step_id=row.step_id,
                available_at=row.available_at,
                attempt=row.attempt,
                idempotency_key=row.idempotency_key,
                task_id=UUID(row.task_id),
                lease_until=lease_until,
            )

    def ack(self, task_id: UUID) -> None:
        with self._session() as session:
            session.query(WorkflowTaskRow).filter(WorkflowTaskRow.task_id == str(task_id)).delete(synchronize_session=False)
            session.commit()

    def release(self, task_id: UUID, *, available_at: datetime) -> None:
        with self._session() as session:
            session.execute(
                update(WorkflowTaskRow)
                .where(WorkflowTaskRow.task_id == str(task_id))
                .values(available_at=available_at, lease_until=None)
            )
            session.commit()
