"""FastAPI Gateway — Unified API for all domain agents."""

import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Make the Month 7 platform modules importable when running this file directly.
_PLATFORM_ROOT = Path(__file__).resolve().parents[2]
if str(_PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLATFORM_ROOT))

from schemas import Domain, TriageResponse  # noqa: E402
from shared_orchestrator.router import AgentRouter  # noqa: E402

app = FastAPI(title="FDE Mastery Platform API", version="7.0.0")

# In-memory store for demo (replace with Redis/DB in production).
CLIENT_REGISTRY: Dict[str, Dict[str, Any]] = {}
BILLING_COUNTER: Dict[str, int] = {}

_START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float


# One router owns all six domain adapters. Domain adapters lazy-load the
# existing Month 1-6 engines only when a request reaches that domain.
AGENT_ROUTER = AgentRouter()
AGENT_ROUTER.register_defaults()


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="healthy",
        version="7.0.0",
        uptime_seconds=round(time.time() - _START_TIME, 2),
    )


@app.get("/health/agents")
def agent_health():
    """Return readiness information for all registered domain adapters."""
    return AGENT_ROUTER.health()


@app.get("/capabilities")
def capabilities():
    """Return the capabilities exposed by the six domain adapters."""
    return AGENT_ROUTER.capabilities()


@app.post("/api/{client_id}/{domain}/triage")
def triage(client_id: str, domain: Domain, payload: Dict[str, Any]):
    """Route a real request through the selected Month 1-6 domain agent."""
    start = time.time()
    request_id = str(uuid.uuid4())[:8]

    if client_id not in CLIENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found. Onboard first.")

    if domain.value not in {str(value) for value in CLIENT_REGISTRY[client_id].get("domains", [])}:
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
        # Do not leak provider/domain implementation details through the API.
        raise HTTPException(status_code=500, detail="Domain agent execution failed.") from exc

    BILLING_COUNTER[client_id] = BILLING_COUNTER.get(client_id, 0) + 1
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
def register_client(client_id: str, client_name: str, domains: list):
    """Register a new client in the platform demo registry."""
    CLIENT_REGISTRY[client_id] = {
        "client_name": client_name,
        "domains": domains,
        "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return {"status": "registered", "client_id": client_id}


@app.get("/admin/clients/{client_id}/usage")
def client_usage(client_id: str):
    """Return API call usage for billing."""
    return {
        "client_id": client_id,
        "total_calls": BILLING_COUNTER.get(client_id, 0),
        "billing_period": "current",
    }
