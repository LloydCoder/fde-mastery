"""Verify integration actions use the existing Tool Gateway trust boundary."""
from __future__ import annotations

from typing import Any

from fde_platform.identity import Environment, Principal, PrincipalType, RequestContext, TenantId, TenantRef
from fde_platform.tools import InMemoryToolGateway
from fde_platform.tools.models import ToolCall
from integrations.plane import AuthMethod, CredentialReference, IntegrationBinding, IntegrationDefinition
from integrations.tool_adapter import register_integration_action


def test_integration_action_is_registered_as_approval_gated_tool() -> None:
    gateway = InMemoryToolGateway()
    tenant_id = TenantId("tenant-a")
    tenant = TenantRef(tenant_id, Environment.PRODUCTION)
    principal = Principal("integration-test", tenant_id, PrincipalType.USER)
    binding = IntegrationBinding(
        "tenant-a",
        "production",
        "crm-1",
        IntegrationDefinition("salesforce", "1", AuthMethod.API_KEY, frozenset({"read"})),
        CredentialReference("salesforce-prod"),
    )
    called: list[dict[str, Any]] = []
    name = register_integration_action(gateway, binding=binding, action="create_case", handler=lambda args: called.append(args))
    result = gateway.invoke(
        RequestContext(principal=principal, tenant=tenant, request_id="req-1", environment=Environment.PRODUCTION),
        ToolCall(
            tool_name=name,
            arguments={"title": "test"},
            tenant_id="tenant-a",
            request_id="req-1",
            idempotency_key="idem-1",
        ),
    )
    assert result.success is False
    assert result.error_code == "approval_required"
    assert called == []
