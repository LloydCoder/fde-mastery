"""Integration tests for the Month 7 API -> router -> adapter path."""

import importlib.util
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("FDE_API_KEYS", "test-api-key")
os.environ.setdefault("FDE_ADMIN_API_KEYS", "test-admin-key")
os.environ.setdefault("FDE_STORAGE_BACKEND", "memory")
os.environ.setdefault("FDE_RATE_LIMIT_BACKEND", "memory")
os.environ.setdefault("MOCK_LLM", "true")

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
    from deployment.api_gateway.rate_limit import reset_rate_limits
    from persistence.models import ClientRecord

    reset_rate_limits()
    module.REPOSITORY.register_client(
        ClientRecord.create(
            "test-client",
            "Integration Test Client",
            ["cybersecurity", "finance", "healthtech", "logistics", "legal", "revops"],
        )
    )
    yield
    reset_rate_limits()


DOMAIN_CASES = [
    (
        "cybersecurity",
        {
            "log_id": "LOG-TEST-001",
            "timestamp": "2026-08-14T12:00:00Z",
            "source_ip": "10.0.0.8",
            "destination_ip": "192.168.1.10",
            "user_id": "synthetic-user",
            "event_type": "UNAUTHORIZED_SSH_ATTEMPT",
            "payload_summary": "Repeated failed SSH login attempts from a synthetic test source.",
        },
    ),
    (
        "finance",
        {
            "transaction_id": "TXN-TEST-001",
            "account_id": "ACC-TEST-001",
            "counterparty_id": "CP-TEST-001",
            "transaction_type": "CARD_PURCHASE",
            "amount": 1250,
            "currency": "USD",
            "source_country": "US",
            "destination_country": "US",
            "metadata": {},
        },
    ),
    (
        "healthtech",
        {
            "encounter_id": "ENC-TEST-001",
            "encounter_type": "OUTPATIENT",
            "primary_symptom": "cough",
            "raw_notes": "Synthetic patient reports mild cough.",
            "patient_id": "synthetic-001",
        },
    ),
    (
        "logistics",
        {
            "shipment_id": "SYN-001",
            "transport_mode": "AIR_FREIGHT",
            "carrier": "Synthetic Carrier",
            "origin_country": "NG",
            "destination_country": "DE",
            "hs_code": "300490",
            "declared_temp_range_c": [2, 8],
            "goods_value_usd": 25000,
            "telemetry": {
                "temperature_c": 5.0,
                "humidity_percent": 45.0,
                "shock_g_force": 0.2,
                "location_coords": "6.5244,3.3792",
            },
            "carrier_status_note": "Synthetic shipment operating normally.",
        },
    ),
    (
        "legal",
        {
            "contract_id": "SYN-CONTRACT-001",
            "title": "Synthetic Master Services Agreement",
            "counterparty": "Synthetic Corp",
            "governing_jurisdiction": "Delaware",
            "annual_contract_value_usd": 50000,
            "clauses": [
                {
                    "clause_id": "CLAUSE-001",
                    "clause_type": "LIABILITY_CAP",
                    "section_title": "Limitation of Liability",
                    "text": "Each party's aggregate liability shall be limited to fees paid under this agreement.",
                }
            ],
        },
    ),
    (
        "revops",
        {
            "opportunity_id": "SYN-OPP-001",
            "account_name": "Synthetic Enterprise",
            "annual_recurring_revenue_usd": 50000,
            "lead_source": "INBOUND_DEMO",
            "deal_stage": "PROPOSAL_NEGOTIATION",
            "discount_requested_pct": 5,
            "has_exec_sponsor": True,
            "telemetry": {
                "monthly_active_users": 100,
                "weekly_usage_growth_pct": 8.0,
                "license_utilization_pct": 75.0,
            },
        },
    ),
]


@pytest.mark.parametrize("domain,payload", DOMAIN_CASES)
def test_triage_reaches_real_domain_adapter(client, domain, payload):
    response = client.post(
        f"/api/test-client/{domain}/triage",
        json=payload,
        headers={"X-API-Key": "test-api-key"},
    )
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
    assert client.post(
        "/admin/clients/register", json=payload, headers={"X-API-Key": "test-api-key"}
    ).status_code == 403
    assert client.post(
        "/admin/clients/register", json=payload, headers={"X-API-Key": "test-admin-key"}
    ).status_code == 200


def test_domain_isolation(client):
    from persistence.models import ClientRecord

    module.REPOSITORY.register_client(ClientRecord.create("restricted", "Restricted", ["finance"]))
    response = client.post(
        "/api/restricted/healthtech/triage",
        json=DOMAIN_CASES[2][1],
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 403


def test_unknown_client_is_rejected(client):
    response = client.post(
        "/api/missing/finance/triage",
        json=DOMAIN_CASES[1][1],
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 404


def test_usage_is_persisted_through_repository(client):
    response = client.post(
        "/api/test-client/finance/triage",
        json=DOMAIN_CASES[1][1],
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 200, response.text
    assert module.REPOSITORY.get_usage("test-client") == 1


def test_agent_health_exposes_all_domains(client):
    response = client.get("/health/agents", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    assert set(response.json()) == {"cybersecurity", "finance", "healthtech", "logistics", "legal", "revops"}
