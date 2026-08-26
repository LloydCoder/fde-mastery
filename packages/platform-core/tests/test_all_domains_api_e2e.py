from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from deployment.api_gateway.main import app


CASES = {
    "cybersecurity": {
        "log_id": "SOC-E2E-001",
        "timestamp": "2026-01-01T00:00:00+00:00",
        "source_ip": "10.10.10.10",
        "destination_ip": "10.10.10.20",
        "user_id": "synthetic-analyst",
        "event_type": "UNAUTHORIZED_SSH_ATTEMPT",
        "payload_summary": "Repeated failed SSH authentication attempts.",
    },
    "finance": {
        "transaction_id": "TXN-E2E-001",
        "account_id": "acct-synthetic",
        "counterparty_id": "counterparty-synthetic",
        "transaction_type": "WIRE_TRANSFER",
        "amount": 1000,
        "currency": "USD",
        "source_country": "US",
        "destination_country": "US",
        "metadata": {},
    },
    "healthtech": {
        "encounter_id": "ENC-E2E-001",
        "patient_id": "patient-synthetic",
        "encounter_type": "AMBULATORY",
        "primary_symptom": "routine follow-up",
        "vital_signs": {"heart_rate": 72, "systolic_bp": 120, "diastolic_bp": 80, "spo2": 98},
        "raw_notes": "Synthetic E2E fixture.",
        "phi_redacted": True,
    },
    "logistics": {
        "shipment_id": "SHIP-E2E-001",
        "transport_mode": "OCEAN_CONTAINER",
        "carrier": "Synthetic Carrier",
        "origin_country": "US",
        "destination_country": "DE",
        "hs_code": "8517.62",
        "declared_temp_range_c": [2, 8],
        "goods_value_usd": 10000,
        "telemetry": {"temperature_c": 5, "humidity_percent": 45, "shock_g_force": 0.2, "location_coords": "40.7128,-74.0060"},
        "carrier_status_note": "On schedule.",
    },
    "legal": {
        "contract_id": "CONTRACT-E2E-001",
        "title": "Synthetic Services Agreement",
        "counterparty": "Synthetic Counterparty",
        "governing_jurisdiction": "Delaware, USA",
        "annual_contract_value_usd": 50000,
        "clauses": [],
    },
    "revops": {
        "opportunity_id": "OPP-E2E-001",
        "account_name": "Synthetic Account",
        "annual_recurring_revenue_usd": 100000,
        "lead_source": "PRODUCT_QUALIFIED_PQL",
        "deal_stage": "TECHNICAL_EVALUATION",
        "discount_requested_pct": 5,
        "has_exec_sponsor": True,
        "telemetry": {"monthly_active_users": 100, "weekly_usage_growth_pct": 10, "license_utilization_pct": 80},
    },
    "procurement": {
        "supplier_id": "SUP-E2E-001",
        "quote_amount_usd": 75000,
        "supplier_risk_score": 25,
        "approval_threshold_usd": 50000,
        "quote_count": 3,
    },
    "custom": {
        "risk_level": "medium",
        "confidence": 0.75,
        "reasons": ["Synthetic tenant-defined E2E case."],
    },
}


def test_every_first_class_domain_executes_through_v1_api(monkeypatch):
    monkeypatch.setenv("FDE_API_KEYS", "e2e-api-key")
    monkeypatch.setenv("FDE_ADMIN_API_KEYS", "e2e-admin-key")
    monkeypatch.setenv("MOCK_LLM", "true")
    monkeypatch.setenv("FDE_MONTH1_PROVIDER", "openai")

    client = TestClient(app)
    client_id = f"e2e-{uuid4().hex[:12]}"

    registration = client.post(
        "/admin/clients/register",
        headers={"X-API-Key": "e2e-admin-key"},
        json={"client_id": client_id, "client_name": "Synthetic E2E Client", "domains": list(CASES)},
    )
    assert registration.status_code == 200, registration.text

    for domain, payload in CASES.items():
        request_id = str(uuid4())
        response = client.post(
            f"/v1/triage/{client_id}/{domain}",
            headers={
                "X-API-Key": "e2e-api-key",
                "X-Request-ID": request_id,
                "Idempotency-Key": f"{client_id}-{domain}-e2e",
            },
            json=payload,
        )
        assert response.status_code == 200, f"{domain}: {response.text}"
        body = response.json()
        assert body["client_id"] == client_id
        assert body["domain"] == domain
        assert body["request_id"] == request_id
        assert body["audit_log_id"] == f"AUDIT-{request_id}"
        assert 0.0 <= body["confidence"] <= 1.0


def test_every_first_class_domain_is_exposed_by_capabilities(monkeypatch):
    monkeypatch.setenv("FDE_API_KEYS", "e2e-api-key")
    response = TestClient(app).get("/v1/capabilities", headers={"X-API-Key": "e2e-api-key"})
    assert response.status_code == 200
    assert set(response.json()["capabilities"]) == set(CASES)
