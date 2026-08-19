"""Durable audit-event repository backed by PostgreSQL."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .audit import AuditEvent


class AuditStore:
    """Append-only audit store with tenant-scoped query support."""

    def __init__(self, engine: Engine):
        self.engine = engine

    def append(self, event: AuditEvent) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    """INSERT INTO fde_audit_events
                    (event_id, request_id, client_id, domain, action, outcome,
                     status_code, duration_ms, created_at, metadata_json)
                    VALUES (:event_id, :request_id, :client_id, :domain, :action,
                            :outcome, :status_code, :duration_ms, :created_at, :metadata_json)
                    ON CONFLICT (event_id) DO NOTHING"""
                ),
                {
                    "event_id": event.event_id,
                    "request_id": event.request_id,
                    "client_id": event.client_id,
                    "domain": event.domain,
                    "action": event.action,
                    "outcome": event.outcome,
                    "status_code": event.status_code,
                    "duration_ms": event.duration_ms,
                    "created_at": event.created_at,
                    "metadata_json": json.dumps(event.metadata, separators=(",", ":"), sort_keys=True),
                },
            )

    def list_for_client(self, client_id: str, limit: int = 100) -> list[dict[str, Any]]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """SELECT event_id, request_id, client_id, domain, action, outcome,
                              status_code, duration_ms, created_at, metadata_json
                       FROM fde_audit_events
                       WHERE client_id = :client_id
                       ORDER BY created_at DESC
                       LIMIT :limit"""
                ),
                {"client_id": client_id, "limit": limit},
            ).mappings()
            return [dict(row) for row in rows]
