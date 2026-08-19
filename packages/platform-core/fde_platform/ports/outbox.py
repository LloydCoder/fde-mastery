"""Port for durable event publication intents."""

from typing import Protocol
from uuid import UUID

from fde_platform.events.models import EventEnvelope
from fde_platform.events.outbox import OutboxRecord


class OutboxPort(Protocol):
    """Application boundary for atomic event-intent persistence."""

    def append(self, event: EventEnvelope) -> OutboxRecord:
        """Persist a publication intent in the same transaction as domain state."""

    def get(self, event_id: UUID) -> OutboxRecord:
        """Return a publication intent by immutable event identifier."""
