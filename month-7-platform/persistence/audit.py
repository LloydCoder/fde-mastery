"""Audit event model used for security and operational traceability."""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    request_id: str
    client_id: str
    domain: str
    action: str
    outcome: str
    status_code: int
    duration_ms: float
    created_at: str
    metadata: dict[str, str]

    @classmethod
    def create(
        cls,
        *,
        event_id: str,
        request_id: str,
        client_id: str,
        domain: str,
        action: str,
        outcome: str,
        status_code: int,
        duration_ms: float,
        metadata: dict[str, str] | None = None,
    ) -> "AuditEvent":
        return cls(
            event_id=event_id,
            request_id=request_id,
            client_id=client_id,
            domain=domain,
            action=action,
            outcome=outcome,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            created_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )
