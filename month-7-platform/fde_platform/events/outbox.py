"""Transactional-outbox domain boundary and deterministic reference adapter."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum
from threading import RLock
from typing import Callable, Iterable
from uuid import UUID

from .models import EventEnvelope


class OutboxStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"


@dataclass(frozen=True, slots=True)
class OutboxRecord:
    """Durable publication intent; status transitions are optimistic."""

    event: EventEnvelope
    sequence: int
    status: OutboxStatus = OutboxStatus.PENDING
    attempts: int = 0
    available_at: datetime = datetime.min.replace(tzinfo=timezone.utc)
    last_error: str | None = None
    locked_by: str | None = None
    locked_at: datetime | None = None


class OutboxConflict(RuntimeError):
    """Raised when a stale outbox version attempts a state transition."""


class InMemoryOutbox:
    """Reference outbox implementing lease, retry and publish transitions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: dict[UUID, OutboxRecord] = {}
        self._sequence = 0

    def append(self, event: EventEnvelope) -> OutboxRecord:
        with self._lock:
            if event.event_id in self._records:
                raise OutboxConflict("event_id already exists")
            self._sequence += 1
            record = OutboxRecord(event=event, sequence=self._sequence)
            self._records[event.event_id] = record
            return record

    def claim(
        self,
        *,
        worker_id: str,
        now: datetime,
        limit: int = 100,
        lease_seconds: int = 60,
    ) -> list[OutboxRecord]:
        if limit < 1 or lease_seconds < 1:
            raise ValueError("limit and lease_seconds must be positive")
        with self._lock:
            candidates = sorted(self._records.values(), key=lambda r: r.sequence)
            claimed: list[OutboxRecord] = []
            for record in candidates:
                expired = record.locked_at is not None and (now - record.locked_at).total_seconds() >= lease_seconds
                eligible = record.status in {OutboxStatus.PENDING, OutboxStatus.FAILED} and record.available_at <= now
                reclaimable = record.status == OutboxStatus.PROCESSING and expired
                if not (eligible or reclaimable) or len(claimed) >= limit:
                    continue
                updated = replace(record, status=OutboxStatus.PROCESSING, attempts=record.attempts + 1, locked_by=worker_id, locked_at=now)
                self._records[record.event.event_id] = updated
                claimed.append(updated)
            return claimed

    def mark_published(self, event_id: UUID, *, worker_id: str) -> OutboxRecord:
        with self._lock:
            current = self._records[event_id]
            self._assert_owner(current, worker_id)
            updated = replace(current, status=OutboxStatus.PUBLISHED, locked_by=None, locked_at=None, last_error=None)
            self._records[event_id] = updated
            return updated

    def mark_failed(
        self,
        event_id: UUID,
        *,
        worker_id: str,
        error: str,
        retry_at: datetime,
        max_attempts: int,
    ) -> OutboxRecord:
        with self._lock:
            current = self._records[event_id]
            self._assert_owner(current, worker_id)
            status = OutboxStatus.DEAD_LETTERED if current.attempts >= max_attempts else OutboxStatus.FAILED
            updated = replace(current, status=status, available_at=retry_at, last_error=error[:2000], locked_by=None, locked_at=None)
            self._records[event_id] = updated
            return updated

    def get(self, event_id: UUID) -> OutboxRecord:
        with self._lock:
            return self._records[event_id]

    def _assert_owner(self, record: OutboxRecord, worker_id: str) -> None:
        if record.status != OutboxStatus.PROCESSING or record.locked_by != worker_id:
            raise OutboxConflict("worker does not own the outbox lease")


class OutboxPublisher:
    """Publishes claimed records with explicit at-least-once semantics."""

    def __init__(self, outbox: InMemoryOutbox, publish: Callable[[EventEnvelope], None]) -> None:
        self._outbox = outbox
        self._publish = publish

    def drain(self, *, worker_id: str, now: datetime, limit: int = 100, max_attempts: int = 5) -> int:
        claimed = self._outbox.claim(worker_id=worker_id, now=now, limit=limit)
        completed = 0
        for record in claimed:
            try:
                self._publish(record.event)
            except Exception as exc:  # boundary: provider failure becomes durable state
                delay = min(3600, 2 ** max(0, record.attempts - 1))
                self._outbox.mark_failed(
                    record.event.event_id,
                    worker_id=worker_id,
                    error=str(exc),
                    retry_at=now.replace(microsecond=0) + __import__("datetime").timedelta(seconds=delay),
                    max_attempts=max_attempts,
                )
            else:
                self._outbox.mark_published(record.event.event_id, worker_id=worker_id)
                completed += 1
        return completed
