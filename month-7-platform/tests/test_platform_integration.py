"""Integration tests for the Month 7 API -> router -> adapter path."""

import importlib.util
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("FDE_API_KEYS", "test-api-key")
os.environ.setdefault("FDE_ADMIN_API_KEYS", "test-admin-key")
os.environ.setdefault("FDE_STORAGE_BACKEND", "memory")

PLATFORM_ROOT = Path(__file__).resolve().parents[1]
API_MAIN = PLATFORM_ROOT / "deployment" / "api_gateway" / "main.py"


def _load_api_module():
    root = str(PLATFORM_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    spec = importlib.util.spec_from_file_location("fde_platform_api", API_MAIN)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load platform API module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


pytest.importorskip("fastapi")
pytest.importorskip("httpx")
module = _load_api_module()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    return TestClient(module.app)


@pytest.fixture(autouse=True)
def registered_client():
    from persistence.models import ClientRecord
    from deployment.api_gateway.rate_limit import reset_rate_limits
    reset_rate_limits()
    module.REPOSITORY.register_client(ClientRecord.create(
        "test-client", "Integration Test Client",
        ["cybersecurity", "finance", "healthtech", "logistics", "legal", "revops"],
    ))
    yield
    reset_rate_limits()


DOMAIN_CASES = [
    ("cybersecurity", {"log": "Failed login from 10.0.0.8"}),
    ("finance", {"amount": 1250, "currency": "USD", "country": "US"}),
    ("healthtech", {"patient_id": "synthetic-001", "symptoms": ["cough"], "vitals": {"spo2": 98}}),
    ("logistics", {"shipment_id": "SYN-001", "origin": "NG", "destination": "DE"}),
    ("legal", {"contract_id": "SYN-CONTRACT-001", "contract_type": "MSA", "text": "Confidentiality clause."}),
    ("revops", {"account_id": "SYN-ACCOUNT-001", "stage": "proposal", "arr": 50000}),
]


@pytest.mark.parametrize("domain,payload", DOMAIN_CASES)
def test_triage_reaches_real_domain_adapter(client, domain, payload):
    response = client.post(f"/api/test-client/{domain}/triage", json=payload, headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["client_id"] == "test-client"
    assert body["domain"] == domain
    assert body["request_id"]
    assert body["audit_log_id"].startswith("AUDIT-")
    assert isinstance(body["result"], dict)
    assert 0.0 <= body["confidence"] <= 1.0
    assert response.headers["X-Request-ID"]


def test_authentication_is_required(client):
    assert client.get("/health/agents").status_code == 401


def test_admin_authentication_is_separate(client):
    payload = {"client_id": "admin-test", "client_name": "Admin Test", "domains": ["finance"]}
    assert client.post("/admin/clients/register", json=payload, headers={"X-API-Key": "test-api-key"}).status_code == 403
    assert client.post("/admin/clients/register", json=payload, headers={"X-API-Key": "test-admin-key"}).status_code == 200


def test_domain_isolation(client):
    from persistence.models import ClientRecord
    module.REPOSITORY.register_client(ClientRecord.create("restricted", "Restricted", ["finance"]))
    response = client.post("/api/restricted/healthtech/triage", json={"patient_id": "synthetic"}, headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 403


def test_unknown_client_is_rejected(client):
    response = client.post("/api/missing/finance/triage", json={"amount": 100}, headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 404


def test_usage_is_persisted_through_repository(client):
    response = client.post("/api/test-client/finance/triage", json={"amount": 100}, headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    assert module.REPOSITORY.get_usage("test-client") == 1


def test_agent_health_exposes_all_domains(client):
    response = client.get("/health/agents", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    assert set(response.json()) == {"cybersecurity", "finance", "healthtech", "logistics", "legal", "revops"}
