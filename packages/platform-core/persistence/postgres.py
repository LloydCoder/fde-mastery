"""PostgreSQL repository for durable platform state."""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from .audit import AuditEvent
from .models import ClientRecord
from .repository import PlatformRepository


class Base(DeclarativeBase):
    pass


class ClientRow(Base):
    __tablename__ = "fde_clients"
    client_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    client_name: Mapped[str] = mapped_column(String(200), nullable=False)
    domains: Mapped[str] = mapped_column(String(1000), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class UsageRow(Base):
    __tablename__ = "fde_client_usage"
    client_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    total_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditEventRow(Base):
    __tablename__ = "fde_audit_events"
    event_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    client_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")


class PostgreSQLPlatformRepository(PlatformRepository):
    """Durable repository backed by PostgreSQL."""

    def __init__(self, database_url: Optional[str] = None, *, create_tables: bool = False):
        url = database_url or os.getenv("FDE_DATABASE_URL")
        if not url:
            raise ValueError("FDE_DATABASE_URL is required for PostgreSQL storage")
        self.engine = create_engine(url, pool_pre_ping=True)
        if create_tables:
            Base.metadata.create_all(self.engine)

    def register_client(self, record: ClientRecord) -> None:
        registered_at = datetime.fromisoformat(record.registered_at)
        with Session(self.engine) as session:
            row = session.get(ClientRow, record.client_id)
            if row is None:
                session.add(ClientRow(client_id=record.client_id, client_name=record.client_name, domains=",".join(record.domains), registered_at=registered_at))
                session.add(UsageRow(client_id=record.client_id, total_calls=0, updated_at=datetime.now(timezone.utc)))
            else:
                row.client_name = record.client_name
                row.domains = ",".join(record.domains)
            session.commit()

    def get_client(self, client_id: str) -> Optional[ClientRecord]:
        with Session(self.engine) as session:
            row = session.get(ClientRow, client_id)
            if row is None:
                return None
            return ClientRecord(client_id=row.client_id, client_name=row.client_name, domains=tuple(filter(None, row.domains.split(","))), registered_at=row.registered_at.isoformat())

    def increment_usage(self, client_id: str) -> int:
        with Session(self.engine) as session:
            row = session.get(UsageRow, client_id)
            now = datetime.now(timezone.utc)
            if row is None:
                row = UsageRow(client_id=client_id, total_calls=1, updated_at=now)
                session.add(row)
            else:
                row.total_calls += 1
                row.updated_at = now
            session.commit()
            return row.total_calls

    def get_usage(self, client_id: str) -> int:
        with Session(self.engine) as session:
            row = session.get(UsageRow, client_id)
            return row.total_calls if row else 0

    def record_audit_event(self, event: AuditEvent) -> None:
        with Session(self.engine) as session:
            session.add(AuditEventRow(
                event_id=event.event_id,
                request_id=event.request_id,
                client_id=event.client_id,
                domain=event.domain,
                action=event.action,
                outcome=event.outcome,
                status_code=event.status_code,
                duration_ms=event.duration_ms,
                created_at=datetime.fromisoformat(event.created_at),
                metadata_json=json.dumps(event.metadata, separators=(",", ":")),
            ))
            session.commit()

    def get_audit_event(self, event_id: str) -> Optional[AuditEvent]:
        with Session(self.engine) as session:
            row = session.get(AuditEventRow, event_id)
            if row is None:
                return None
            return AuditEvent(
                event_id=row.event_id,
                request_id=row.request_id,
                client_id=row.client_id,
                domain=row.domain,
                action=row.action,
                outcome=row.outcome,
                status_code=row.status_code,
                duration_ms=row.duration_ms,
                created_at=row.created_at.isoformat(),
                metadata=json.loads(row.metadata_json),
            )
