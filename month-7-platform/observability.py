"""Small, dependency-light observability helpers for the platform API."""

import json
import logging
import time
import uuid

logger = logging.getLogger("fde.platform")


def new_request_id() -> str:
    return str(uuid.uuid4())


def log_request(request_id: str, method: str, path: str, status_code: int, duration_ms: float, client_id: str | None = None) -> None:
    logger.info(json.dumps({
        "event": "http_request",
        "request_id": request_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "client_id": client_id,
    }, separators=(",", ":")))


def monotonic_ms() -> float:
    return time.monotonic() * 1000
