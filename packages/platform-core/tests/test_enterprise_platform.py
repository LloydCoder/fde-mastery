from decimal import Decimal

import pytest

from fde_platform.approvals import ApprovalService
from fde_platform.control_plane import AgentRegistry
from fde_platform.deployment import DeploymentMode, DeploymentProfile
from fde_platform.identity import Environment, Principal, PrincipalType, RequestContext, TenantId, TenantRef
from fde_platform.operations import CostRecord, CostTracker, DecisionEvidence, DecisionLineage, Incident, IncidentService
from fde_platform.protocols import A2AEnvelope, AgentMessage, MCPToolCall, MCPToolDefinition
from fde_platform.runtime.sandbox import SandboxPolicy, SandboxViolation, validate_sandbox
from fde_platform.trust import ActionRequest, SecurityGateway


def context() -> RequestContext:
    tenant = TenantRef(TenantId("acme"), Environment.PRODUCTION)
    principal = Principal("user-1", TenantId("acme"), PrincipalType.USER, frozenset({"operator"}))
    return RequestContext(principal, tenant, "req-1", Environment.PRODUCTION)


def test_registry_promotes_one_immutable_version() -> None:
    registry = AgentRegistry()
    registry.register(__import__("fde_platform.control_plane.registry", fromlist=["RegistryEntry"]).RegistryEntry("soc", 1, "acme", "staged", object()))
    registry.register(__import__("fde_platform.control_plane.registry", fromlist=["RegistryEntry"]).RegistryEntry("soc", 2, "acme", "staged", object()))
    registry.promote("soc", 2, "acme")
    assert registry.active("soc", "acme").version == 2
    with pytest.raises(ValueError):
        registry.register(__import__("fde_platform.control_plane.registry", fromlist=["RegistryEntry"]).RegistryEntry("soc", 2, "acme", "staged", object()))


def test_security_gateway_blocks_high_impact_actions() -> None:
    decision = SecurityGateway().authorize(ActionRequest(context(), "soc", "disable_endpoint", risk_level=5))
    assert decision.allowed is False
    assert decision.requires_approval is True


def test_approval_quorum() -> None:
    service = ApprovalService()
    service.create("apr-1", "acme", "award_supplier", {"a", "b"}, quorum=2)
    assert service.approve("apr-1", "a").status == "pending"
    assert service.approve("apr-1", "b").status == "approved"


def test_protocols_require_authorization_references() -> None:
    tool = MCPToolDefinition("lookup", "1", {"type": "object"})
    call = MCPToolCall(tool, {}, "call-1", "auth-1")
    message = AgentMessage("msg-1", "agent-a", "agent-b", "lookup", {"id": "1"})
    envelope = A2AEnvelope(message, "acme", "auth-2")
    assert call.authorization_reference == "auth-1"
    assert envelope.tenant_id == "acme"


def test_sandbox_rejects_implicit_network_access() -> None:
    with pytest.raises(SandboxViolation):
        validate_sandbox(SandboxPolicy(), network_access=True, credential_scope="task-scoped")


def test_lineage_is_append_only() -> None:
    lineage = DecisionLineage()
    lineage.record("run-1", DecisionEvidence(input_refs=("input-1",), policy_decisions=("allow-1",), model="enterprise", model_version="1"))
    with pytest.raises(ValueError):
        lineage.record("run-1", DecisionEvidence())


def test_finops_enforces_tenant_budget() -> None:
    tracker = CostTracker({"acme": Decimal("1.00")})
    tracker.record(CostRecord("acme", "soc", "run-1", "model", tool_cost=Decimal("0.60")))
    with pytest.raises(PermissionError):
        tracker.record(CostRecord("acme", "soc", "run-2", "model", tool_cost=Decimal("0.50")))


def test_incident_lifecycle() -> None:
    service = IncidentService()
    service.create(Incident("inc-1", "acme", "SEV-1", "agent misuse"))
    service.transition("inc-1", "contained")
    service.transition("inc-1", "investigating")
    service.transition("inc-1", "remediated")
    assert service.transition("inc-1", "closed").status == "closed"


def test_deployment_profiles() -> None:
    assert DeploymentProfile.for_mode(DeploymentMode.SHARED, "eu-west").dedicated_database is False
    assert DeploymentProfile.for_mode(DeploymentMode.DEDICATED, "eu-west").dedicated_keys is True
