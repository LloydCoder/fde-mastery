"""Request deadline primitives shared by the platform execution path."""

from __future__ import annotations

import contextvars
import time
from dataclasses import dataclass
from typing import Optional


_deadline: contextvars.ContextVar[Optional[float]] = contextvars.ContextVar("request_deadline", default=None)


@dataclass(frozen=True)
class Deadline:
    """Absolute monotonic deadline for a request."""

    expires_at: float

    @classmethod
    def from_timeout(cls, seconds: float) -> "Deadline":
        if seconds <= 0:
            raise ValueError("deadline timeout must be positive")
        return cls(time.monotonic() + seconds)

    @property
    def remaining(self) -> float:
        return max(0.0, self.expires_at - time.monotonic())

    @property
    def expired(self) -> bool:
        return self.remaining <= 0


def set_deadline(deadline: Deadline):
    return _deadline.set(deadline.expires_at)


def reset_deadline(token) -> None:
    _deadline.reset(token)


def current_deadline() -> Optional[Deadline]:
    value = _deadline.get()
    return Deadline(value) if value is not None else None
