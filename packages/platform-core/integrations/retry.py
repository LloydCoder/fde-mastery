"""Bounded retry and rate-limit primitives for outbound integrations."""
from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


@dataclass(frozen=True, slots=True)
class RetryDecision:
    retry: bool
    delay_seconds: float = 0.0
    reason: str = ""


def retry_after_seconds(value: str | None, *, now: datetime | None = None) -> float | None:
    if not value:
        return None
    try:
        seconds = float(value)
        return max(0.0, seconds)
    except ValueError:
        try:
            target = parsedate_to_datetime(value)
            if target.tzinfo is None:
                target = target.replace(tzinfo=timezone.utc)
            current = now or datetime.now(timezone.utc)
            return max(0.0, (target - current).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None


def classify_retry(status_code: int, attempt: int, *, retry_after: str | None = None, max_attempts: int = 4,
                   base_delay: float = 0.5, max_delay: float = 30.0, jitter: float = 0.2) -> RetryDecision:
    if attempt < 1 or max_attempts < 1:
        raise ValueError("attempt and max_attempts must be positive")
    if attempt >= max_attempts:
        return RetryDecision(False, reason="retry_budget_exhausted")
    if status_code == 429 or status_code in {408, 425} or 500 <= status_code <= 599:
        server_delay = retry_after_seconds(retry_after)
        exponential = min(max_delay, base_delay * (2 ** (attempt - 1)))
        delay = server_delay if server_delay is not None else exponential
        delay = min(max_delay, delay + secrets.SystemRandom().uniform(0.0, max(0.0, delay * jitter)))
        return RetryDecision(True, delay, reason="server_retryable")
    return RetryDecision(False, reason="status_not_retryable")


@dataclass(slots=True)
class TokenBucket:
    capacity: int
    refill_per_second: float
    tokens: float | None = None
    last_refill: float | None = None

    def allow(self, now: float) -> bool:
        import time
        if self.capacity < 1 or self.refill_per_second <= 0:
            raise ValueError("invalid token bucket configuration")
        current = now if now >= 0 else time.monotonic()
        if self.tokens is None:
            self.tokens = float(self.capacity)
            self.last_refill = current
        previous = self.last_refill if self.last_refill is not None else current
        elapsed = max(0.0, current - previous)
        self.tokens = min(float(self.capacity), self.tokens + elapsed * self.refill_per_second)
        self.last_refill = current
        if self.tokens < 1.0:
            return False
        self.tokens -= 1.0
        return True
