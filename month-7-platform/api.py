"""Production API entry point for the FDE platform."""

from __future__ import annotations

import os
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from integrations.tinlance_contract import TinlanceAgentRequest, VALID_DOMAINS
from observability.fastapi import instrument_app
from observability.tracing import configure_tracing
from schemas import Domain
from security.dependencies import require_bearer_from_env
from security.rbac import AuthorizationError, Principal, require_access
from shared_orchestrator.router import AgentRouter

configure_tracing()
app = FastAPI(title="FDE Mastery Platform", version="1.1.0")
instrument_app(app)
router = AgentRouter()
router.register_defaults()


class AgentRequest(TinlanceAgentRequest):
    """Stable Tinlance-to-Mastery execution envelope."""


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    response.headers["cache-control"] = "no-store" if request.url.path.startswith("/v1/") else "no-cache"
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "domains": router.list_domains()}


@app.get("/ready")
def ready() -> dict:
    """Report whether the production security boundary is configured."""
    issuer = os.getenv("FDE_OIDC_ISSUER", "").strip()
    audience = os.getenv("FDE_OIDC_AUDIENCE", "").strip()
    if not issuer or not audience:
        raise HTTPException(status_code=503, detail="OIDC issuer/audience are not configured")
    configured = set(router.list_domains())
    expected = set(VALID_DOMAINS)
    if configured != expected:
        raise HTTPException(status_code=503, detail="Domain router is not fully configured")
    return {"status": "ready", "domains": sorted(configured)}


@app.post("/v1/{domain}/execute")
def execute(
    domain: Domain,
    request: AgentRequest,
    identity=Depends(require_bearer_from_env()),
    x_request_id: str | None = Header(default=None, alias="x-request-id"),
):
    principal = Principal.from_claims(identity.claims)
    try:
        require_access(principal, tenant_id=request.tenant_id, scope="agents:execute")
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail="Access denied") from exc

    # Domain is an enum at the HTTP boundary; the explicit allowlist protects
    # the Tinlance integration contract if domains are expanded elsewhere.
    if domain.value not in VALID_DOMAINS:
        raise HTTPException(status_code=422, detail="Unknown domain")

    try:
        result = router.route(domain, request.payload)
    except Exception as exc:  # Keep internal agent failures out of the wire contract.
        request_id = x_request_id or getattr(request, "request_id", "")
        raise HTTPException(status_code=502, detail="Agent execution failed", headers={"x-request-id": request_id}) from exc

    return JSONResponse(content=result, headers={"x-request-id": x_request_id or request.state.request_id})
