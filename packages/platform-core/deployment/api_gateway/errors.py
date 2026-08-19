"""Safe, machine-readable API error responses."""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse


def api_error(
    *, status_code: int, code: str, message: str, request_id: str, retryable: bool = False, details: Any = None
) -> JSONResponse:
    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
            "retryable": retryable,
        }
    }
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)
