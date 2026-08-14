"""Production API entry point for the FDE platform."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from observability.fastapi import instrument_app
from observability.tracing import configure_tracing
from schemas import Domain
from security.auth import Identity, OIDCAuthenticator, bearer_authenticator, require_identity
from security.rbac import AuthorizationError, Principal, require_access
from shared_orchestrator.router import AgentRouter

configure_tracing()
app = FastAPI(title="FDE Mastery Platform", version="1.0.1")
instrument_app(app)
router = AgentRouter()
router.register_defaults()


@lru_cache(maxsize=1)
def get_authenticator() -> OIDCAuthenticator:
    return bearer_authenticator()


def authenticated_identity():
    return require_identity(get_authenticator())


class AgentRequest(BaseModel):
    tenant_id: str = Field(min_length=1, max_length=100)
    payload: dict


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "domains": router.list_domains()}


@app.post("/v1/{domain}/execute")
def execute(
    domain: Domain,
    request: AgentRequest,
    identity: Identity = Depends(authenticated_identity),
):
    principal = Principal.from_claims(identity.claims)
    try:
        require_access(principal, tenant_id=request.tenant_id, scope="agents:execute")
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail="Access denied") from exc
    return router.route(domain, request.payload)
