"""FastAPI Gateway — Unified API for all domain agents."""

import json
import sys
import time
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

_PLATFORM_ROOT = Path(__file__).resolve().parents[2]
if str(_PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLATFORM_ROOT))

from config import settings
from observability import log_request, monotonic_ms, new_request_id
from observability_metrics import metrics
from persistence.audit import AuditEvent
from persistence.factory import build_repository
from persistence.models import ClientRecord
from persistence.repository import PlatformRepository
from schemas import Domain, TriageResponse
from shared_orchestrator.resilience import AgentTimeoutError, CircuitOpenError
from shared_orchestrator.router import AgentRouter
from deployment.api_gateway.auth import require_admin_api_key
from deployment.api_gateway.oidc_auth import require_api_or_oidc, require_scope
from deployment.api_gateway.errors import api_error
from deployment.api_gateway.limiter_factory import build_rate_limiter
from security.auth import Identity

app = FastAPI(title="FDE Mastery Platform API", version=settings.version)
if settings.cors_origins:
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"])

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


def _storage_backend() -> str:
    return type(REPOSITORY).__name__.replace("PlatformRepository", "").lower()


def _limiter_backend() -> str:
    return "redis" if RATE_LIMITER.__module__.endswith("redis_rate_limit") else "memory"


def _audit_failure(request_id: str, client_id: str, domain: Domain, code: str, status_code: int, duration_ms: float) -> None:
    REPOSITORY.record_audit_event(AuditEvent.create(event_id=f"AUDIT-{request_id}", request_id=request_id, client_id=client_id, domain=domain.value, action="triage", outcome="failure", status_code=status_code, duration_ms=duration_ms, metadata={"error_code": code}))


@app.middleware("http")
async def security_and_observability(request: Request, call_next):
    request_id = new_request_id()
    request.state.request_id = request_id
    started = monotonic_ms()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = monotonic_ms() - started
        metrics.observe_request(request.method, request.url.path, 500, duration_ms)
        log_request(request_id, request.method, request.url.path, 500, duration_ms, request.path_params.get("client_id"))
        raise
    duration_ms = monotonic_ms() - started
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/admin") else "no-cache"
    metrics.observe_request(request.method, request.url.path, response.status_code, duration_ms)
    log_request(request_id, request.method, request.url.path, response.status_code, duration_ms, request.path_params.get("client_id"))
    return response


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="healthy", version=settings.version, uptime_seconds=round(time.time() - _START_TIME, 2), storage_backend=_storage_backend(), rate_limit_backend=_limiter_backend())


@app.get("/health/ready")
def readiness():
    checks: dict[str, str] = {"repository": "ok", "rate_limiter": "ok"}
    if settings.storage_backend == "postgres":
        try:
            from persistence.postgres import PostgreSQLPlatformRepository
            if not isinstance(REPOSITORY, PostgreSQLPlatformRepository):
                raise RuntimeError("configured PostgreSQL backend is not active")
            with REPOSITORY.engine.connect() as connection:
                connection.exec_driver_sql("SELECT 1")
        except Exception:
            checks["repository"] = "unavailable"
    if settings.rate_limit_backend == "redis":
        try:
            client = getattr(RATE_LIMITER, "client", None)
            if client is None:
                raise RuntimeError("Redis limiter is not initialized")
            client.ping()
        except Exception:
            checks["rate_limiter"] = "unavailable"
    ready = all(value == "ok" for value in checks.values())
    return {"status": "ready" if ready else "not_ready", "checks": checks}


@app.get("/metrics", response_class=PlainTextResponse, dependencies=[Depends(require_api_or_oidc)])
def metrics_endpoint():
    return metrics.prometheus()


@app.get("/health/agents", dependencies=[Depends(require_api_or_oidc)])
def agent_health():
    return AGENT_ROUTER.health()


@app.get("/capabilities", dependencies=[Depends(require_api_or_oidc)])
def capabilities():
    return AGENT_ROUTER.capabilities()


@app.post("/api/{client_id}/{domain}/triage", dependencies=[Depends(require_api_or_oidc)])
def triage(client_id: str, domain: Domain, request: Request, payload: dict[str, Any], identity: Identity | str = Depends(require_api_or_oidc)):
    start = time.time()
    request_id = getattr(request.state, "request_id", new_request_id())
    if isinstance(identity, Identity):
        if identity.tenant_id != client_id:
            raise HTTPException(status_code=403, detail="Token tenant does not match client.")
        require_scope(identity, "triage:execute")
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
    except AgentTimeoutError:
        elapsed_ms = (time.time() - start) * 1000
        _audit_failure(request_id, client_id, domain, "AGENT_TIMEOUT", 504, elapsed_ms)
        return api_error(status_code=504, code="AGENT_TIMEOUT", message="The domain agent exceeded the execution deadline.", request_id=request_id, retryable=True)
    except CircuitOpenError:
        elapsed_ms = (time.time() - start) * 1000
        _audit_failure(request_id, client_id, domain, "AGENT_CIRCUIT_OPEN", 503, elapsed_ms)
        return api_error(status_code=503, code="AGENT_CIRCUIT_OPEN", message="The domain agent is temporarily unavailable.", request_id=request_id, retryable=True)
    except (ValueError, TypeError, KeyError):
        elapsed_ms = (time.time() - start) * 1000
        _audit_failure(request_id, client_id, domain, "INVALID_AGENT_INPUT", 422, elapsed_ms)
        return api_error(status_code=422, code="INVALID_AGENT_INPUT", message="The request could not be processed by the domain agent.", request_id=request_id, retryable=False)
    except Exception:
        elapsed_ms = (time.time() - start) * 1000
        _audit_failure(request_id, client_id, domain, "AGENT_EXECUTION_FAILED", 500, elapsed_ms)
        return api_error(status_code=500, code="AGENT_EXECUTION_FAILED", message="The domain agent failed to process the request.", request_id=request_id, retryable=False)

    REPOSITORY.increment_usage(client_id)
    elapsed_ms = (time.time() - start) * 1000
    audit_id = f"AUDIT-{request_id}"
    REPOSITORY.record_audit_event(AuditEvent.create(event_id=audit_id, request_id=request_id, client_id=client_id, domain=domain.value, action="triage", outcome="success", status_code=200, duration_ms=elapsed_ms, metadata={"agent": domain.value}))
    return TriageResponse(request_id=request_id, client_id=client_id, domain=domain.value, result=agent_result.result, confidence=agent_result.confidence, processing_time_ms=round(elapsed_ms, 2), audit_log_id=audit_id)


@app.get("/admin/audit/{event_id}", dependencies=[Depends(require_admin_api_key)])
def audit_event(event_id: str):
    event = REPOSITORY.get_audit_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Audit event not found.")
    return event


@app.post("/admin/clients/register")
def register_client(registration: ClientRegistration, _: str = Depends(require_admin_api_key)):
    REPOSITORY.register_client(ClientRecord.create(registration.client_id, registration.client_name, [d.value for d in registration.domains]))
    return {"status": "registered", "client_id": registration.client_id}


@app.get("/admin/clients/{client_id}/usage")
def client_usage(client_id: str, _: str = Depends(require_admin_api_key)):
    return {"client_id": client_id, "total_calls": REPOSITORY.get_usage(client_id), "billing_period": "current"}
