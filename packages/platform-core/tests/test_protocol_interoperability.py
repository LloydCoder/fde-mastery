"""Build 16 MCP/A2A interoperability and security contract tests."""
from __future__ import annotations

import pytest

from fde_platform.protocols import (
    A2AAgentRegistry,
    A2ARequest,
    A2ATaskBridge,
    A2ATaskState,
    AgentCard,
    AgentInterface,
    AgentSkill,
    MCPAuthorizationContext,
    MCPProtocolVersion,
    MCPRequest,
    MCPRequestValidator,
    MCPToolAnnotations,
    MCPToolCatalog,
    MCPToolCatalogEntry,
    SecurityScheme,
    authorize_a2a,
    validate_agent_card_endpoint,
)
from fde_platform.protocols.mcp import MCPToolDefinition


def auth(tenant: str = "tenant-a") -> MCPAuthorizationContext:
    return MCPAuthorizationContext(
        tenant_id=tenant,
        subject="agent-user",
        issuer="https://issuer.example.com",
        scopes=frozenset({"crm.read"}),
        authorization_reference="authz-1",
    )


def test_mcp_request_requires_matching_routable_headers() -> None:
    request = MCPRequest(
        protocol_version=MCPProtocolVersion.V2026_07_28,
        method="tools/call",
        name="search",
        request_id="req-1",
        tenant_id="tenant-a",
        authorization=auth(),
        headers={"Mcp-Method": "tools/call", "Mcp-Name": "search"},
    )
    MCPRequestValidator.validate(request)
    bad = MCPRequest(
        protocol_version=MCPProtocolVersion.V2026_07_28,
        method="tools/call",
        name="search",
        request_id="req-2",
        tenant_id="tenant-a",
        authorization=auth(),
        headers={"Mcp-Method": "tools/call", "Mcp-Name": "wrong"},
    )
    with pytest.raises(ValueError):
        MCPRequestValidator.validate(bad)


def test_mcp_authorization_is_tenant_scoped_and_scope_gated() -> None:
    catalog = MCPToolCatalog()
    tool = MCPToolDefinition(
        name="search",
        version="1",
        input_schema={"type": "object"},
        annotations=MCPToolAnnotations(read_only=True, idempotent=True),
        required_scopes=frozenset({"crm.read"}),
    )
    catalog.register(MCPToolCatalogEntry("tenant-a", tool, frozenset({"crm.read"})), tool_name="search")
    request = MCPRequest(
        MCPProtocolVersion.V2026_07_28, "tools/call", "search", "req", "tenant-a", auth(),
        headers={"Mcp-Method": "tools/call", "Mcp-Name": "search"},
    )
    assert catalog.authorize(request, tool_name="search").tenant_id == "tenant-a"
    with pytest.raises(LookupError):
        catalog.get("tenant-b", "search")
    with pytest.raises(PermissionError):
        catalog.authorize(request.__class__(
            MCPProtocolVersion.V2026_07_28, "tools/call", "search", "req2", "tenant-a",
            MCPAuthorizationContext("tenant-a", "agent-user", "https://issuer.example.com", frozenset(), "authz-2"),
            headers={"Mcp-Method": "tools/call", "Mcp-Name": "search"},
        ), tool_name="search")


def test_mcp_authorization_tenant_mismatch_fails_closed() -> None:
    with pytest.raises(PermissionError):
        MCPRequest(
            MCPProtocolVersion.V2026_07_28, "tools/call", "search", "req", "tenant-a",
            auth("tenant-b"), headers={"Mcp-Method": "tools/call", "Mcp-Name": "search"},
        )


def test_a2a_agent_card_is_discoverable_by_tenant_and_skill() -> None:
    card = AgentCard(
        name="Fraud Agent",
        description="Enterprise fraud investigation agent",
        version="1.0.0",
        supported_interfaces=(AgentInterface("https://fraud.example.com/a2a"),),
        skills=(AgentSkill("fraud.investigate", "Investigate", "Investigate fraud signals"),),
        security_schemes=(SecurityScheme("oauth", "oauth2", ("fraud.read",)),),
    )
    registry = A2AAgentRegistry()
    registry.register("tenant-a", card)
    assert registry.discover("tenant-a", "fraud.investigate") == (card,)
    assert registry.discover("tenant-b", "fraud.investigate") == ()


def test_a2a_authorization_checks_recipient_skill_and_policy() -> None:
    card = AgentCard(
        name="Fraud Agent", description="Fraud", version="1", supported_interfaces=(AgentInterface("https://fraud.example.com/a2a"),),
        skills=(AgentSkill("fraud.investigate", "Investigate", "Investigate fraud"),),
    )
    request = A2ARequest("tenant-a", "risk-agent", "Fraud Agent", "fraud.investigate", "task-1", "authz-1")
    authorize_a2a(request, card, lambda tenant, sender, skill, reference: tenant == "tenant-a" and reference == "authz-1")
    with pytest.raises(PermissionError):
        authorize_a2a(request, card, lambda *_: False)


def test_a2a_agent_card_endpoint_must_be_allowlisted() -> None:
    card = AgentCard(
        name="Agent", description="Agent", version="1", supported_interfaces=(AgentInterface("https://agent.example.com/a2a"),),
        skills=(AgentSkill("read", "Read", "Read data"),),
    )
    validate_agent_card_endpoint(card, allowed_hosts=("agent.example.com",))
    with pytest.raises(PermissionError):
        validate_agent_card_endpoint(card, allowed_hosts=("evil.example.com",))
    with pytest.raises(ValueError):
        AgentInterface("http://agent.example.com/a2a")


def test_a2a_task_bridge_reuses_workflow_identity_and_is_tenant_scoped() -> None:
    bridge = A2ATaskBridge()
    ref = bridge.create("tenant-a", "task-1", "workflow-99")
    assert ref.workflow_id == "workflow-99"
    assert bridge.update_state("tenant-a", "task-1", A2ATaskState.WORKING).state is A2ATaskState.WORKING
    with pytest.raises(LookupError):
        bridge.get("tenant-b", "task-1")
    with pytest.raises(ValueError):
        bridge.create("tenant-a", "task-1", "workflow-100")
