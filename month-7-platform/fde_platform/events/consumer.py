"""Idempotent consumer boundary for at-least-once event delivery."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Callable
from uuid import UUID

from .models import EventEnvelope


class InboxDecision(str):
    ACCEPTED = "accepted"
    DUPLICATE = "duplicate"


@dataclass(frozen=True, slots=True)
class InboxRecord:
    event_id: UUID
    consumer: str
    tenant_id: str


class InMemoryInbox:
    """Reference inbox that atomically deduplicates event IDs per consumer."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._processed: set[tuple[str, UUID]] = set()

    def consume(self, event: EventEnvelope, *, consumer: str, handler: Callable[[EventEnvelope], None]) -> str:
        key = (consumer, event.event_id)
        with self._lock:
            if key in self._processed:
                return InboxDecision.DUPLICATE
            # Mark only after successful handler execution so failures remain retryable.
            handler(event)
            self._processed.add(key)
            return InboxDecision.ACCEPTED

    def has_processed(self, event_id: UUID, *, consumer: str) -> bool:
        with self._lock:
            return (consumer, event_id) in self._processed
