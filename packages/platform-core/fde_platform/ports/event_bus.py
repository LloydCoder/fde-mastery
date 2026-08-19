"""Event publication boundary for the future event-driven platform."""

from typing import Any, Mapping, Protocol


class EventBusPort(Protocol):
    """Application boundary for publishing domain/integration events."""

    def publish(self, event_type: str, payload: Mapping[str, Any]) -> None:
        """Publish an event without coupling callers to a broker implementation."""
