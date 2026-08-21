"""Authenticated, replay-resistant inbound webhook verification."""
from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass


@dataclass(slots=True)
class ReplayGuard:
    ttl_seconds: int = 900

    def __post_init__(self) -> None:
        self._seen: dict[str, float] = {}

    def accept(self, delivery_id: str, *, now: float | None = None) -> bool:
        if not delivery_id.strip():
            return False
        current = now if now is not None else time.time()
        cutoff = current - self.ttl_seconds
        self._seen = {key: value for key, value in self._seen.items() if value >= cutoff}
        if delivery_id in self._seen:
            return False
        self._seen[delivery_id] = current
        return True


def verify_hmac_sha256(payload: bytes, signature: str, secret: str) -> bool:
    """Verify `sha256=<hex>` signatures using constant-time comparison."""
    if not secret or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_timestamped_signature(payload: bytes, signature: str, secret: str, timestamp: int,
                                 *, tolerance_seconds: int = 300, now: int | None = None) -> bool:
    """Verify a provider-neutral `t=<unix>,v1=<hex>` signature and reject stale requests."""
    current = int(time.time()) if now is None else now
    if tolerance_seconds <= 0 or abs(current - timestamp) > tolerance_seconds:
        return False
    try:
        parts = dict(item.split("=", 1) for item in signature.split(","))
        supplied = parts["v1"]
    except (KeyError, ValueError):
        return False
    signed = f"{timestamp}.".encode("ascii") + payload
    expected = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, supplied)
