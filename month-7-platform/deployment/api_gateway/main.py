"""FastAPI Gateway — Unified API for all domain agents."""

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from schemas import Domain, TriageRequest, TriageResponse
except ImportError:
    # Fallback for standalone execution
    from enum import Enum
    class Domain(str, Enum):
        CYBERSECURITY = "cybersecurity"
        FINANCE = "finance"
        HEALTHTECH = "healthtech"
        LOGISTICS = "logistics"
        LEGAL = "legal"
        REVOPS = "revops"

app = FastAPI(title="FDE Mastery Platform API", version="7.0.0")

# In-memory store for demo (replace with Redis/DB in production)
CLIENT_REGISTRY: Dict[str, Dict[str, Any]] = {}
BILLING_COUNTER: Dict[str, int] = {}


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float


_START_TIME = time.time()


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="healthy",
        version="7.0.0",
        uptime_seconds=round(time.time() - _START_TIME, 2),
    )


@app.post("/api/{client_id}/{domain}/triage")
def triage(client_id: str, domain: Domain, payload: Dict[str, Any]):
    """Main triage endpoint — routes to the correct domain agent."""
    start = time.time()
    request_id = str(uuid.uuid4())[:8]

    if client_id not in CLIENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found. Onboard first.")

    # Load client preferences
    pref_path = Path("preferences") / client_id / "rubric_overrides.json"
    rubric = {}
    if pref_path.exists():
        with open(pref_path, "r") as f:
            rubric = json.load(f)

    # Route to domain agent (mock for platform demo)
    result = _mock_domain_agent(domain, payload, rubric)

    # Billing
    BILLING_COUNTER[client_id] = BILLING_COUNTER.get(client_id, 0) + 1

    elapsed_ms = (time.time() - start) * 1000

    return TriageResponse(
        request_id=request_id,
        client_id=client_id,
        domain=domain.value,
        result=result,
        confidence=0.95,
        processing_time_ms=round(elapsed_ms, 2),
        audit_log_id=f"AUDIT-{request_id}",
    )


def _mock_domain_agent(domain: Domain, payload: Dict[str, Any], rubric: Dict[str, Any]) -> Dict[str, Any]:
    """Mock agent router — in production, this imports the real domain agent."""
    return {
        "domain": domain.value,
        "status": "processed",
        "payload_summary": {k: str(v)[:50] for k, v in payload.items()},
        "rubric_applied": bool(rubric),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@app.post("/admin/clients/register")
def register_client(client_id: str, client_name: str, domains: list):
    """Register a new client in the platform."""
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