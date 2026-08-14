"""Integration tests for the Month 7 API -> router -> adapter path."""

import importlib.util
import sys
from pathlib import Path

import pytest

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


api = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

module = _load_api_module()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    return TestClient(module.app)


@pytest.fixture(autouse=True)
def registered_client():
    module.CLIENT_REGISTRY.clear()
    module.BILLING_COUNTER.clear()
    module.CLIENT_REGISTRY["test-client"] = {
        "client_name": "Integration Test Client",
        "domains": [
            "cybersecurity",
            "finance",
            "healthtech",
            "logistics",
            "legal",
            "revops",
        ],
    }
    yield
    module.CLIENT_REGISTRY.clear()
    module.BILLING_COUNTER.clear()


DOMAIN_CASES = [
    ("cybersecurity", {"log": "Failed login from 10.0.0.8"}),
    ("finance", {"amount": 1250, "currency": "USD", "country": "US"}),
    (
        "healthtech",
        {
            "patient_id": "synthetic-001",
            "symptoms": ["cough"],
            "vitals": {"spo2": 98},
        },
    ),
    (
        "logistics",
        {
            "shipment_id": "SYN-001",
            "origin": "NG",
            "destination": "DE",
        },
    ),
    (
        "legal",
        {
            "contract_id": "SYN-CONTRACT-001",
            "contract_type": "MSA",
            "text": "Confidentiality and limitation of liability clause.",
        },
    ),
    (
        "revops",
        {
            "account_id": "SYN-ACCOUNT-001",
            "stage": "proposal",
            "arr": 50000,
        },
    ),
]


@pytest.mark.parametrize("domain,payload", DOMAIN_CASES)
def test_triage_reaches_real_domain_adapter(client, domain, payload):
    response = client.post(f"/api/test-client/{domain}/triage", json=payload)

    assert response.status_code != 404
    assert response.status_code != 405
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["client_id"] == "test-client"
    assert body["domain"] == domain
    assert body["request_id"]
    assert body["audit_log_id"].startswith("AUDIT-")
    assert isinstance(body["result"], dict)
    assert 0.0 <= body["confidence"] <= 1.0


def test_router_registers_all_six_domains():
    expected = {
        "cybersecurity",
        "finance",
        "healthtech",
        "logistics",
        "legal",
        "revops",
    }
    assert set(module.AGENT_ROUTER.list_domains()) == expected


def test_agent_health_exposes_all_domains(client):
    response = client.get("/health/agents")

    assert response.status_code == 200
    assert set(response.json()) == {
        "cybersecurity",
        "finance",
        "healthtech",
        "logistics",
        "legal",
        "revops",
    }


def test_disabled_domain_is_rejected(client):
    module.CLIENT_REGISTRY["restricted-client"] = {
        "client_name": "Restricted",
        "domains": ["finance"],
    }

    response = client.post(
        "/api/restricted-client/healthtech/triage",
        json={"patient_id": "synthetic-001"},
    )

    assert response.status_code == 403


def test_unknown_client_is_rejected(client):
    response = client.post(
        "/api/missing-client/finance/triage",
        json={"amount": 100},
    )

    assert response.status_code == 404
