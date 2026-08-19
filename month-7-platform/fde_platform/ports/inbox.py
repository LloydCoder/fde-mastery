"""Port for idempotent event consumption."""

from typing import Protocol

from fde_platform.events.consumer import InboxDecision
from fde_platform.events.models import EventEnvelope


class InboxPort(Protocol):
    """Application boundary for durable consumer deduplication."""

    def consume(self, event: EventEnvelope, *, consumer: str) -> InboxDecision:
        """Accept an event once per consumer identity."""
