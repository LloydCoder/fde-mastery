"""Versioned, tenant-aware event contracts.

The platform uses CloudEvents-inspired fields while keeping the kernel
framework- and broker-neutral. Event payloads are opaque mappings so domain
packages retain ownership of their schemas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4


class EventContractError(ValueError):
    """Raised when an event violates a platform contract."""


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    """Immutable event envelope with explicit tenant and schema identity."""

    event_id: UUID
    event_type: str
    schema_version: int
    source: str
    tenant_id: str
    environment_id: str
    subject: str
    payload: Mapping[str, Any]
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: UUID | None = None
    causation_id: UUID | None = None
    trace_id: str | None = None
    partition_key: str | None = None

    def __post_init__(self) -> None:
        if not self.event_type.strip() or not self.source.strip():
            raise EventContractError("event_type and source are required")
        if self.schema_version < 1:
            raise EventContractError("schema_version must be positive")
        if not self.tenant_id.strip() or not self.environment_id.strip():
            raise EventContractError("tenant_id and environment_id are required")
        if self.occurred_at.tzinfo is None:
            raise EventContractError("occurred_at must be timezone-aware")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))

    @classmethod
    def create(
        cls,
        *,
        event_type: str,
        schema_version: int,
        source: str,
        tenant_id: str,
        environment_id: str,
        subject: str,
        payload: Mapping[str, Any],
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
        trace_id: str | None = None,
        partition_key: str | None = None,
    ) -> "EventEnvelope":
        return cls(
            event_id=uuid4(),
            event_type=event_type,
            schema_version=schema_version,
            source=source,
            tenant_id=tenant_id,
            environment_id=environment_id,
            subject=subject,
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
            trace_id=trace_id,
            partition_key=partition_key,
        )


CloudEvent = EventEnvelope
