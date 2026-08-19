import pytest

from custom_agents import CustomAgentToolGateway, ToolCatalog, ToolDefinition, ToolExecutionDenied


def test_tool_gateway_allows_declared_read_tool():
    catalog = ToolCatalog()
    catalog.register(ToolDefinition("lookup_vendor", lambda payload: {"vendor": payload["id"]}))
    gateway = CustomAgentToolGateway(catalog)

    assert gateway.execute(
        tenant_id="tenant-a",
        allowed_tools=("lookup_vendor",),
        tool_name="lookup_vendor",
        payload={"id": "V-001"},
    ) == {"vendor": "V-001"}


def test_tool_gateway_rejects_undeclared_tool():
    catalog = ToolCatalog()
    catalog.register(ToolDefinition("lookup_vendor", lambda payload: payload))
    gateway = CustomAgentToolGateway(catalog)

    with pytest.raises(ToolExecutionDenied):
        gateway.execute(
            tenant_id="tenant-a",
            allowed_tools=(),
            tool_name="lookup_vendor",
            payload={},
        )


def test_tool_gateway_requires_approval_for_mutation():
    catalog = ToolCatalog()
    catalog.register(ToolDefinition("approve_purchase", lambda payload: {"approved": True}, mutating=True))
    gateway = CustomAgentToolGateway(catalog)

    with pytest.raises(ToolExecutionDenied):
        gateway.execute(
            tenant_id="tenant-a",
            allowed_tools=("approve_purchase",),
            tool_name="approve_purchase",
            payload={"id": "PO-001"},
        )

    assert gateway.execute(
        tenant_id="tenant-a",
        allowed_tools=("approve_purchase",),
        tool_name="approve_purchase",
        payload={"id": "PO-001"},
        approved_actions=frozenset({"approve_purchase"}),
    ) == {"approved": True}
