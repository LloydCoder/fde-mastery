"""FastAPI Gateway — Unified API for all domain agents."""

import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

_PLATFORM_ROOT = Path(__file__).resolve().parents[2]
if str(_PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLATFORM_ROOT))

from schemas import Domain, TriageResponse  # noqa: E402
from shared_orchestrator.router import AgentRouter  # noqa: E402
from deployment.api_gateway.auth import require_admin_api_key, require_api_key  # noqa: E402
from deployment.api_gateway.rate_limit import enforce_request_limits  # noqa: E402
from persistence.models import ClientRecord  # noqa: E402
from persistence.repository import InMemoryPlatformRepository, PlatformRepository  # noqa: E402

app = FastAPI(title="FDE Mastery Platform API", version="7.0.0")

# The gateway depends on an interface rather than a concrete storage format.
# Swap this for a PostgreSQL implementation without changing endpoint logic.
REPOSITORY: PlatformRepository = InMemoryPlatformRepository()
_START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float


class ClientRegistration(BaseModel):
    client_id: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    client_name: str = Field(min_length=1, max_length=200)
    domains: list[Domain] = Field(min_length=1, max_length=6)


AGENT_ROUTER = AgentRouter()
AGENT_ROUTER.register_defaults()


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="healthy",
        version="7.0.0",
        uptime_seconds=round(time.time() - _START_TIME, 2),
    )


@app.get("/health/agents", dependencies=[Depends(require_api_key)])
def agent_health():
    return AGENT_ROUTER.health()


@app.get("/capabilities", dependencies=[Depends(require_api_key)])
def capabilities():
    return AGENT_ROUTER.capabilities()


@app.post("/api/{client_id}/{domain}/triage", dependencies=[Depends(require_api_key)])
def triage(
    client_id: str,
    domain: Domain,
    request: Request,
    payload: Dict[str, Any],
):
    start = time.time()
    request_id = str(uuid.uuid4())[:8]

    client = REPOSITORY.get_client(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found. Onboard first.")

    enforce_request_limits(request, client_id)

    if domain.value not in client.domains:
        raise HTTPException(
            status_code=403,
            detail=f"Domain {domain.value} is not enabled for client {client_id}.",
        )

    pref_path = Path("preferences") / client_id / "rubric_overrides.json"
    rubric: Dict[str, Any] = {}
    if pref_path.exists():
        with pref_path.open("r", encoding="utf-8") as f:
            rubric = json.load(f)

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
    REPOSITORY.register_client(
        ClientRecord.create(
            client_id=registration.client_id,
            client_name=registration.client_name,
            domains=[domain.value for domain in registration.domains],
        )
    )
    return {"status": "registered", "client_id": registration.client_id}


@app.get("/admin/clients/{client_id}/usage")
def client_usage(client_id: str, _: str = Depends(require_admin_api_key)):
    return {
        "client_id": client_id,
        "total_calls": REPOSITORY.get_usage(client_id),
        "billing_period": "current",
    }
