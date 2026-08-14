"""Lightweight in-memory rate limiting for the platform demo.

This protects the demo gateway without pretending to be a distributed
production rate limiter. Production deployments should move counters to
Redis or an API gateway with shared state.
"""

import os
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque

from fastapi import HTTPException, Request

_WINDOW_SECONDS = int(os.getenv("FDE_RATE_LIMIT_WINDOW_SECONDS", "60"))
_MAX_REQUESTS = int(os.getenv("FDE_RATE_LIMIT_REQUESTS", "60"))
_MAX_BODY_BYTES = int(os.getenv("FDE_MAX_BODY_BYTES", str(256 * 1024)))

_hits: dict[str, Deque[float]] = defaultdict(deque)
_lock = Lock()


def enforce_request_limits(request: Request, client_id: str) -> None:
    """Apply body-size and per-client sliding-window limits."""
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > _MAX_BODY_BYTES:
                raise HTTPException(status_code=413, detail="Request body too large.")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid Content-Length header.")

    now = time.monotonic()
    cutoff = now - _WINDOW_SECONDS
    key = client_id

    with _lock:
        bucket = _hits[key]
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= _MAX_REQUESTS:
            retry_after = max(1, int(bucket[0] + _WINDOW_SECONDS - now))
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded.",
                headers={"Retry-After": str(retry_after)},
            )
        bucket.append(now)


def reset_rate_limits() -> None:
    """Clear state for deterministic tests."""
    with _lock:
        _hits.clear()
