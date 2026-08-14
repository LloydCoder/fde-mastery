"""FastAPI Gateway — Unified API for all domain agents."""

import json
import sys
import time
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

_PLATFORM_ROOT = Path(__file__).resolve().parents[2]
if str(_PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLATFORM_ROOT))

from schemas import Domain, TriageResponse  # noqa: E402
from shared_orchestrator.router import AgentRouter  # noqa: E402
from deployment.api_gateway.auth import require_admin_api_key, require_api_key  # noqa: E402
from deployment.api_gateway.limiter_factory import build_rate_limiter  # noqa: E402
from persistence.factory import build_repository  # noqa: E402
from persistence.models import ClientRecord  # noqa: E402
from persistence.repository import PlatformRepository  # noqa: E402
from observability import log_request, monotonic_ms, new_request_id  # noqa: E402

app = FastAPI(title="FDE Mastery Platform API", version="0.8.0")
REPOSITORY: PlatformRepository = build_repository()
RATE_LIMITER = build_rate_limiter()
_START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    storage_backend: str
    rate_limit_backend: str


class ClientRegistration(BaseModel):
    client_id: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    client_name: str = Field(min_length=1, max_length=200)
    domains: list[Domain] = Field(min_length=1, max_length=6)


AGENT_ROUTER = AgentRouter()
AGENT_ROUTER.register_defaults()


@app.middleware("http")
async def request_observability(request: Request, call_next):
    request_id = new_request_id()
    request.state.request_id = request_id
    started = monotonic_ms()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = monotonic_ms() - started
        log_request(request_id, request.method, request.url.path, 500, duration_ms, request.path_params.get("client_id"))
        raise
    duration_ms = monotonic_ms() - started
    response.headers["X-Request-ID"] = request_id
    log_request(request_id, request.method, request.url.path, response.status_code, duration_ms, request.path_params.get("client_id"))
    return response


@app.get("/health", response_model=HealthResponse)
def health():
    backend = type(REPOSITORY).__name__.replace("PlatformRepository", "").lower()
    limiter_backend = "redis" if RATE_LIMITER.__module__.endswith("redis_rate_limit") else "memory"
    return HealthResponse(
        status="healthy",
        version="0.8.0",
        uptime_seconds=round(time.time() - _START_TIME, 2),
        storage_backend=backend,
        rate_limit_backend=limiter_backend,
    )


@app.get("/health/agents", dependencies=[Depends(require_api_key)])
def agent_health():
    return AGENT_ROUTER.health()


@app.get("/capabilities", dependencies=[Depends(require_api_key)])
def capabilities():
    return AGENT_ROUTER.capabilities()


@app.post("/api/{client_id}/{domain}/triage", dependencies=[Depends(require_api_key)])
def triage(client_id: str, domain: Domain, request: Request, payload: dict[str, Any]):
    start = time.time()
    request_id = getattr(request.state, "request_id", new_request_id())[:8]
    client = REPOSITORY.get_client(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found. Onboard first.")

    RATE_LIMITER(request, client_id)
    if domain.value not in client.domains:
        raise HTTPException(status_code=403, detail=f"Domain {domain.value} is not enabled for client {client_id}.")

    pref_path = _PLATFORM_ROOT / "preferences" / client_id / "rubric_overrides.json"
    rubric: dict[str, Any] = {}
    if pref_path.exists():
        try:
            with pref_path.open("r", encoding="utf-8") as f:
                rubric = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=500, detail="Client preference configuration is invalid.") from exc

    if rubric:
        payload = {**payload, "_platform": {"rubric_overrides": rubric}}

    try:
        agent_result = AGENT_ROUTER.route(domain, payload)
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Domain agent execution failed.") from exc

    REPOSITORY.increment_usage(client_id)
    elapsed_ms = (time.time() - start) * 1000
    return TriageResponse(
        request_id=request_id,
        client_id=client_id,
        domain=domain.value,
        result=agent_result.result,
        confidence=agent_result.confidence,
        processing_time_ms=round(elapsed_ms, 2),
        audit_log_id=f"AUDIT-{request_id}",
    )


@app.post("/admin/clients/register")
def register_client(registration: ClientRegistration, _: str = Depends(require_admin_api_key)):
    REPOSITORY.register_client(ClientRecord.create(registration.client_id, registration.client_name, [d.value for d in registration.domains]))
    return {"status": "registered", "client_id": registration.client_id}


@app.get("/admin/clients/{client_id}/usage")
def client_usage(client_id: str, _: str = Depends(require_admin_api_key)):
    return {"client_id": client_id, "total_calls": REPOSITORY.get_usage(client_id), "billing_period": "current"}
