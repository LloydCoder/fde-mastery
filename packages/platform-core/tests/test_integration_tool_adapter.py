"""Verify integration actions use the existing Tool Gateway trust boundary."""
from __future__ import annotations

from fde_platform.identity import RequestContext, TenantId
from fde_platform.tools import InMemoryToolGateway
from integrations.plane import AuthMethod, CredentialReference, IntegrationBinding, IntegrationDefinition
from integrations.tool_adapter import register_integration_action


def test_integration_action_is_registered_as_approval_gated_tool() -> None:
    gateway = InMemoryToolGateway()
    binding = IntegrationBinding(
        "tenant-a",
        "production",
        "crm-1",
        IntegrationDefinition("salesforce", "1", AuthMethod.API_KEY, frozenset({"read"})),
        CredentialReference("salesforce-prod"),
    )
    called = []
    name = register_integration_action(gateway, binding=binding, action="create_case", handler=lambda args: called.append(args))
    result = gateway.invoke(
        RequestContext(tenant_id=TenantId("tenant-a"), request_id="req-1"),
        __import__("fde_platform.tools.models", fromlist=["ToolCall"]).ToolCall(
            tool_name=name,
            arguments={"title": "test"},
            tenant_id="tenant-a",
            request_id="req-1",
            idempotency_key="idem-1",
            capabilities=frozenset(),
        ),
    )
    assert result.success is False
    assert result.error_code == "approval_required"
    assert called == []
