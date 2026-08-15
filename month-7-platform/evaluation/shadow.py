"""Shadow-mode evaluation: observe recommendations without executing actions."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ShadowRecord:
    request_id: str
    tenant_id: str
    domain: str
    recommendation: dict[str, Any]
    human_disposition: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ShadowRecorder:
    """In-memory reference implementation; production deployments persist records in audit storage."""

    def __init__(self) -> None:
        self.records: list[ShadowRecord] = []

    def record(self, record: ShadowRecord) -> None:
        if not record.request_id or not record.tenant_id or not record.domain:
            raise ValueError("request_id, tenant_id and domain are required")
        self.records.append(record)

    def attach_human_disposition(self, request_id: str, disposition: str) -> None:
        for record in self.records:
            if record.request_id == request_id:
                record.human_disposition = disposition
                return
        raise KeyError(request_id)

    def agreement_rate(self) -> float:
        compared = [r for r in self.records if r.human_disposition is not None]
        if not compared:
            return 0.0
        matches = sum(r.recommendation.get("disposition") == r.human_disposition for r in compared)
        return matches / len(compared)
