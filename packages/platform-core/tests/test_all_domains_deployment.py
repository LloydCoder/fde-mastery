from datetime import datetime, timezone

from schemas import Domain
from shared_orchestrator.adapters import (
    CybersecurityDomainAdapter,
    FinanceDomainAdapter,
    HealthTechDomainAdapter,
    LegalDomainAdapter,
    LogisticsDomainAdapter,
    ProcurementDomainAdapter,
    RevOpsDomainAdapter,
)
from domains.custom.agent import CustomDomainAgent


def test_all_first_class_domains_have_deployment_safe_smoke_paths(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "true")
    monkeypatch.setenv("FDE_MONTH1_PROVIDER", "openai")

    cases = [
        (CybersecurityDomainAdapter(), Domain.CYBERSECURITY, {"log_id": "SOC-DEPLOY-001", "timestamp": datetime.now(timezone.utc).isoformat(), "source_ip": "10.10.10.10", "destination_ip": "10.10.10.20", "user_id": "analyst-test", "event_type": "UNAUTHORIZED_SSH_ATTEMPT", "payload_summary": "Repeated failed SSH authentication attempts."}),
        (FinanceDomainAdapter(), Domain.FINANCE, {"transaction_id": "TXN-DEPLOY-001", "account_id": "acct-test", "counterparty_id": "counterparty-test", "transaction_type": "WIRE_TRANSFER", "amount": 1000, "currency": "USD", "source_country": "US", "destination_country": "US", "metadata": {}}),
        (HealthTechDomainAdapter(), Domain.HEALTHTECH, {"encounter_id": "ENC-DEPLOY-001", "patient_id": "patient-test", "encounter_type": "AMBULATORY", "primary_symptom": "routine follow-up", "vital_signs": {"heart_rate": 72, "systolic_bp": 120, "diastolic_bp": 80, "spo2": 98}, "raw_notes": "Synthetic deployment smoke test.", "phi_redacted": True}),
        (LogisticsDomainAdapter(), Domain.LOGISTICS, {"shipment_id": "SHIP-DEPLOY-001", "transport_mode": "OCEAN_CONTAINER", "carrier": "Synthetic Carrier", "origin_country": "US", "destination_country": "DE", "hs_code": "8517.62", "declared_temp_range_c": [2, 8], "goods_value_usd": 10000, "telemetry": {"temperature_c": 5, "humidity_percent": 45, "shock_g_force": 0.2, "location_coords": "40.7128,-74.0060"}, "carrier_status_note": "On schedule."}),
        (LegalDomainAdapter(), Domain.LEGAL, {"contract_id": "CONTRACT-DEPLOY-001", "title": "Synthetic Services Agreement", "counterparty": "Synthetic Counterparty", "governing_jurisdiction": "Delaware, USA", "annual_contract_value_usd": 50000, "clauses": []}),
        (RevOpsDomainAdapter(), Domain.REVOPS, {"opportunity_id": "OPP-DEPLOY-001", "account_name": "Synthetic Account", "annual_recurring_revenue_usd": 100000, "lead_source": "PRODUCT_QUALIFIED_PQL", "deal_stage": "TECHNICAL_EVALUATION", "discount_requested_pct": 5, "has_exec_sponsor": True, "telemetry": {"monthly_active_users": 100, "weekly_usage_growth_pct": 10, "license_utilization_pct": 80}}),
        (ProcurementDomainAdapter(), Domain.PROCUREMENT, {"supplier_id": "SUP-DEPLOY-001", "quote_amount_usd": 75000, "supplier_risk_score": 25, "approval_threshold_usd": 50000, "quote_count": 3}),
        (CustomDomainAgent(), Domain.CUSTOM, {"risk_level": "medium", "confidence": 0.75, "reasons": ["Synthetic deployment smoke test."]}),
    ]

    assert {domain for _, domain, _ in cases} == set(Domain)

    for adapter, expected_domain, payload in cases:
        result = adapter.evaluate(payload)
        assert result.domain is expected_domain
        assert 0.0 <= result.confidence <= 1.0
        assert result.audit_metadata["deployment_mode"] == "human_in_the_loop"
        assert adapter.health()["status"] == "ready"
        assert adapter.capabilities()["human_in_the_loop"] is True


def test_high_impact_actions_are_always_human_review():
    from shared_orchestrator.adapters import BaseLegacyAdapter
    assert BaseLegacyAdapter._requires_review({"recommended_action": "AUTO_CONTAIN"})
    assert BaseLegacyAdapter._requires_review({"recommended_action": "FREEZE_ACCOUNT"})
    assert BaseLegacyAdapter._requires_review({"recommended_action": "HOLD_AND_QUARANTINE"})
    assert BaseLegacyAdapter._requires_review({"recommended_action": "REJECT_CONTRACT"})
    assert BaseLegacyAdapter._requires_review({"action": "IMMEDIATE_INTERVENTION"})
