from domains.procurement import ProcurementAgent
from custom_agents import CustomAgent, CustomAgentRegistry, CustomAgentSpec, requires_human_approval
from shared_orchestrator.adapters import ProcurementDomainAdapter
from schemas import Domain


def test_procurement_deployment_contract():
    adapter = ProcurementDomainAdapter()
    result = adapter.evaluate({
        "supplier_id": "SUP-001",
        "quote_amount_usd": 75000,
        "supplier_risk_score": 25,
        "approval_threshold_usd": 50000,
        "quote_count": 3,
    })
    assert result.domain is Domain.PROCUREMENT
    assert result.requires_human_review is True
    assert result.audit_metadata["deployment_mode"] == "human_in_the_loop"
    assert adapter.health()["status"] == "ready"


def test_custom_agent_is_tenant_scoped_and_policy_is_fail_closed():
    spec = CustomAgentSpec(name="invoice-review", version="1.0.0", tenant_id="tenant-a")
    agent = CustomAgent(spec, lambda payload: {"ok": True, "id": payload["id"]})
    registry = CustomAgentRegistry()
    registry.register(agent)
    assert registry.get("tenant-a", "invoice-review") is agent
    assert registry.list("tenant-b") == []
    assert requires_human_approval("approve_purchase") is True
    assert requires_human_approval("classify_invoice") is False
