"""Stable v1 API facade over the existing gateway execution boundary."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from schemas import Domain
from .oidc_auth import require_api_or_oidc

router = APIRouter(prefix="/v1", tags=["v1"])


def _problem_response(status_code: int, request: Request, *, code: str, detail: str, retryable: bool = False) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    body: dict[str, Any] = {
        "type": f"https://fde-mastery.dev/problems/{code}",
        "title": code.replace("_", " ").title(),
        "status": status_code,
        "detail": detail,
        "instance": str(request.url.path),
        "code": code,
        "request_id": request_id,
        "retryable": retryable,
    }
    return JSONResponse(status_code=status_code, content=body, media_type="application/problem+json")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "api_version": "v1"}


@router.get("/capabilities", dependencies=[Depends(require_api_or_oidc)])
def capabilities() -> dict[str, Any]:
    # Import lazily so the facade cannot create a module cycle with the gateway.
    from .main import AGENT_ROUTER

    return {"api_version": "v1", "capabilities": AGENT_ROUTER.capabilities()}


@router.post("/triage/{client_id}/{domain}")
def triage_v1(
    client_id: str,
    domain: Domain,
    request: Request,
    payload: dict[str, Any],
    identity: Any = Depends(require_api_or_oidc),
) -> Any:
    # Reuse the established triage implementation; v1 is a compatibility facade,
    # not a second execution path.
    from .main import triage

    try:
        result = triage(client_id, domain, request, payload, identity)
    except HTTPException as exc:
        return _problem_response(exc.status_code, request, code="HTTP_ERROR", detail=str(exc.detail))
    if isinstance(result, JSONResponse) and result.status_code >= 400:
        try:
            body = json.loads(result.body.decode("utf-8"))
        except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
            return _problem_response(result.status_code, request, code="API_ERROR", detail="The request failed.")
        error = body.get("error", {}) if isinstance(body, dict) else {}
        return _problem_response(
            result.status_code,
            request,
            code=str(error.get("code", "API_ERROR")),
            detail=str(error.get("message", "The request failed.")),
            retryable=bool(error.get("retryable", False)),
        )
    return result
