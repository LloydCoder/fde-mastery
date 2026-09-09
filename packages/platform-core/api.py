"""Production API entry point for the FDE platform."""

from __future__ import annotations

from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from config import Settings
from integrations.tinlance_contract import TinlanceAgentRequest, VALID_DOMAINS
from observability.fastapi import instrument_app
from observability.tracing import configure_tracing
from operational_readiness import assess_readiness
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


def validate_domain(domain: str) -> str:
    """Validate the integration route before performing authentication work."""
    normalized = domain.strip().lower()
    if normalized not in VALID_DOMAINS:
        raise HTTPException(status_code=422, detail="Unknown domain")
    return normalized


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
    """Return a machine-readable configuration readiness result."""
    runtime_settings = Settings()
    assessment = assess_readiness(runtime_settings, set(router.list_domains()), set(VALID_DOMAINS))
    if not assessment.ready:
        raise HTTPException(status_code=503, detail=assessment.as_dict())
    return assessment.as_dict()


def _execute_domain(domain: str, request: AgentRequest, identity, x_request_id: str | None, request_id: str):
    principal = Principal.from_claims(identity.claims)
    try:
        require_access(principal, tenant_id=request.tenant_id, scope="agents:execute")
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail="Access denied") from exc
    try:
        result = router.route(domain, request.payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Agent execution failed", headers={"x-request-id": request_id}) from exc
    return JSONResponse(content=result, headers={"x-request-id": x_request_id or request_id})


@app.post("/v1/triage/{client_id}/{domain}")
def triage(
    client_id: str,
    domain: str,
    request: AgentRequest,
    validated_domain: str = Depends(validate_domain),
    identity=Depends(require_bearer_from_env()),
    x_request_id: str | None = Header(default=None, alias="x-request-id"),
):
    """Canonical Tinlance FDE contract: client-scoped triage by domain."""
    if client_id != request.tenant_id:
        raise HTTPException(status_code=403, detail="Client and tenant do not match")
    return _execute_domain(validated_domain, request, identity, x_request_id, x_request_id or "")


@app.post("/v1/{domain}/execute")
def execute(
    domain: str,
    request: AgentRequest,
    validated_domain: str = Depends(validate_domain),
    identity=Depends(require_bearer_from_env()),
    x_request_id: str | None = Header(default=None, alias="x-request-id"),
):
    """Legacy internal route retained for compatibility; new callers must use /v1/triage/{client_id}/{domain}."""
    return _execute_domain(validated_domain, request, identity, x_request_id, x_request_id or "")
