"""Idempotency primitives for mutation endpoints.

The in-memory implementation is deterministic for tests; production should
back this contract with PostgreSQL or Redis with a TTL and unique key.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock
from typing import Any


@dataclass(frozen=True)
class IdempotencyRecord:
    key: str
    fingerprint: str
    response: Any
    expires_at: float


class IdempotencyConflict(ValueError):
    pass


class MemoryIdempotencyStore:
    def __init__(self, ttl_seconds: int = 86_400):
        if ttl_seconds < 1:
            raise ValueError("ttl_seconds must be positive")
        self.ttl_seconds = ttl_seconds
        self._records: dict[str, IdempotencyRecord] = {}
        self._lock = Lock()

    def get(self, key: str, fingerprint: str) -> Any | None:
        with self._lock:
            record = self._records.get(key)
            if record is None:
                return None
            if record.expires_at <= time.time():
                self._records.pop(key, None)
                return None
            if record.fingerprint != fingerprint:
                raise IdempotencyConflict("idempotency key was reused with a different request")
            return record.response

    def put(self, key: str, fingerprint: str, response: Any) -> None:
        with self._lock:
            self._records[key] = IdempotencyRecord(key, fingerprint, response, time.time() + self.ttl_seconds)
