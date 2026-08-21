"""Stable v1 API facade over the existing gateway execution boundary."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from schemas import Domain
from .oidc_auth import require_api_or_oidc

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "api_version": "v1"}


@router.get("/capabilities", dependencies=[Depends(require_api_or_oidc)])
def capabilities() -> dict[str, Any]:
    # Import lazily so the facade cannot create a module cycle with the gateway.
    from .main import AGENT_ROUTER

    return {"api_version": "v1", "capabilities": AGENT_ROUTER.capabilities()}


@router.post("/triage/{client_id}/{domain}", dependencies=[Depends(require_api_or_oidc)])
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

    return triage(client_id, domain, request, payload, identity)
