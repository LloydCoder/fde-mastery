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
    # Re-read environment configuration for each readiness request so tests,
    # rotations and deployment configuration changes cannot be masked by a
    # process-start snapshot.
    runtime_settings = Settings()
    assessment = assess_readiness(runtime_settings, set(router.list_domains()), set(VALID_DOMAINS))
    if not assessment.ready:
        raise HTTPException(status_code=503, detail=assessment.as_dict())
    return assessment.as_dict()


@app.post("/v1/{domain}/execute")
def execute(
    domain: str,
    request: AgentRequest,
    validated_domain: str = Depends(validate_domain),
    identity=Depends(require_bearer_from_env()),
    x_request_id: str | None = Header(default=None, alias="x-request-id"),
):
    principal = Principal.from_claims(identity.claims)
    try:
        require_access(principal, tenant_id=request.tenant_id, scope="agents:execute")
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail="Access denied") from exc

    try:
        result = router.route(validated_domain, request.payload)
    except Exception as exc:  # Keep internal agent failures out of the wire contract.
        request_id = x_request_id or getattr(request, "request_id", "")
        raise HTTPException(status_code=502, detail="Agent execution failed", headers={"x-request-id": request_id}) from exc

    return JSONResponse(content=result, headers={"x-request-id": x_request_id or request.state.request_id})
