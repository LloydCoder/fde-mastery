import pytest

from schemas import Domain
from shared_orchestrator.domain_agent import DomainAgentResult
from shared_orchestrator.router import AgentRouter


PAYLOADS = {
    Domain.CYBERSECURITY: {
        "log_id": "LOG-E2E-001",
        "timestamp": "2026-08-14T00:00:00Z",
        "source_ip": "10.0.0.10",
        "event_type": "UNAUTHORIZED_SSH_ATTEMPT",
        "payload_summary": "Repeated failed SSH authentication attempts.",
    },
    Domain.FINANCE: {
        "transaction_id": "TXN-E2E-001",
        "account_id": "ACC-001",
        "counterparty_id": "CP-001",
        "transaction_type": "WIRE_TRANSFER",
        "amount": 1000.0,
        "source_country": "US",
        "destination_country": "GB",
    },
    Domain.HEALTHTECH: {
        "encounter_id": "ENC-E2E-001",
        "patient_id": "PATIENT-HASH-001",
        "encounter_type": "AMBULATORY",
        "primary_symptom": "routine cough",
        "raw_notes": "No acute distress reported.",
    },
    Domain.LOGISTICS: {
        "shipment_id": "SHP-E2E-001",
        "transport_mode": "OCEAN_CONTAINER",
        "carrier": "Example Carrier",
        "origin_country": "US",
        "destination_country": "GB",
        "hs_code": "100630",
        "declared_temp_range_c": [2.0, 8.0],
        "goods_value_usd": 10000.0,
        "telemetry": {
            "temperature_c": 5.0,
            "humidity_percent": 50.0,
            "shock_g_force": 0.1,
            "location_coords": "40.0,-73.0",
        },
        "carrier_status_note": "On schedule.",
    },
    Domain.LEGAL: {
        "contract_id": "CON-E2E-001",
        "title": "Master Services Agreement",
        "counterparty": "Example Corp",
        "governing_jurisdiction": "New York",
        "annual_contract_value_usd": 25000.0,
        "clauses": [
            {
                "clause_id": "C-1",
                "clause_type": "GOVERNING_LAW",
                "section_title": "Governing Law",
                "text": "This agreement is governed by the laws of New York.",
            }
        ],
    },
    Domain.REVOPS: {
        "opportunity_id": "OPP-E2E-001",
        "account_name": "Example Enterprise",
        "annual_recurring_revenue_usd": 50000.0,
        "lead_source": "INBOUND_DEMO",
        "deal_stage": "QUALIFICATION",
        "discount_requested_pct": 5.0,
        "has_exec_sponsor": True,
        "telemetry": {
            "monthly_active_users": 100,
            "weekly_usage_growth_pct": 5.0,
            "license_utilization_pct": 80.0,
        },
    },
}


@pytest.mark.parametrize("domain", list(Domain))
def test_router_executes_registered_domain_adapter(domain, monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "true")
    monkeypatch.setenv("CYBERSECURITY_LLM_PROVIDER", "openai")
    router = AgentRouter()
    try:
        router.register_defaults()
        result = router.route(domain, PAYLOADS[domain])
        assert isinstance(result, DomainAgentResult)
        assert result.domain == domain
        assert isinstance(result.result, dict)
        assert 0.0 <= result.confidence <= 1.0
        assert "engine" in result.audit_metadata
    finally:
        router.close()


def test_router_rejects_unknown_domain():
    router = AgentRouter()
    try:
        with pytest.raises(ValueError, match="No agent registered"):
            router.route(Domain.CYBERSECURITY, {})
    finally:
        router.close()
