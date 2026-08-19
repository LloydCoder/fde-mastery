from __future__ import annotations

from fde_platform.identity import Environment, Principal, PrincipalType, RequestContext, TenantRef
from fde_platform.tools import InMemoryToolGateway, ToolCall, ToolCapability, ToolDefinition, ToolResult


def context() -> RequestContext:
    tenant = TenantRef("tenant-a", Environment.STAGING)
    principal = Principal("user-a", tenant.tenant_id, PrincipalType.USER)
    return RequestContext(principal, tenant, "req-1", Environment.STAGING)


def test_gateway_executes_registered_tool_with_explicit_capability() -> None:
    gateway = InMemoryToolGateway()
    gateway.register(
        ToolDefinition("lookup", "1.0.0", "read a record", frozenset({ToolCapability.READ})),
        lambda args: {"id": args["id"]},
    )
    result = gateway.invoke(
        context(), ToolCall("lookup", {"id": "V-1"}, "tenant-a", "req-1", "call-1", frozenset({ToolCapability.READ}))
    )
    assert result == ToolResult(True, {"id": "V-1"})


def test_gateway_fails_closed_for_unknown_or_excessive_capability() -> None:
    gateway = InMemoryToolGateway()
    gateway.register(
        ToolDefinition("lookup", "1.0.0", "read a record", frozenset({ToolCapability.READ})),
        lambda args: args,
    )
    unknown = gateway.invoke(context(), ToolCall("missing", {}, "tenant-a", "req-1", "call-1"))
    excessive = gateway.invoke(
        context(), ToolCall("lookup", {}, "tenant-a", "req-1", "call-2", frozenset({ToolCapability.WRITE}))
    )
    assert unknown.error_code == "tool_not_found"
    assert excessive.error_code == "capability_denied"


def test_gateway_rejects_cross_tenant_and_request_context_mismatch() -> None:
    gateway = InMemoryToolGateway()
    gateway.register(ToolDefinition("lookup", "1.0.0", "read", frozenset()), lambda args: args)
    wrong_tenant = gateway.invoke(context(), ToolCall("lookup", {}, "tenant-b", "req-1", "call-1"))
    wrong_request = gateway.invoke(context(), ToolCall("lookup", {}, "tenant-a", "other-request", "call-2"))
    assert wrong_tenant.error_code == "tenant_context_mismatch"
    assert wrong_request.error_code == "request_context_mismatch"


def test_gateway_requires_approval_before_high_impact_tool() -> None:
    gateway = InMemoryToolGateway()
    calls = 0

    def handler(_: dict[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        return ToolResult(True, {"ok": True})

    gateway.register(
        ToolDefinition("delete", "1.0.0", "delete", frozenset({ToolCapability.DELETE}), True),
        handler,
    )
    denied = gateway.invoke(
        context(), ToolCall("delete", {}, "tenant-a", "req-1", "call-1", frozenset({ToolCapability.DELETE}))
    )
    assert denied.error_code == "approval_required"
    assert calls == 0


def test_gateway_is_idempotent_per_tenant_tool_and_key() -> None:
    gateway = InMemoryToolGateway()
    calls = 0

    def handler(_: dict[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        return ToolResult(True, {"count": calls})

    gateway.register(ToolDefinition("lookup", "1.0.0", "read", frozenset()), handler)
    first = gateway.invoke(context(), ToolCall("lookup", {}, "tenant-a", "req-1", "same-key"))
    second = gateway.invoke(context(), ToolCall("lookup", {}, "tenant-a", "req-1", "same-key"))
    assert first == second
    assert calls == 1
