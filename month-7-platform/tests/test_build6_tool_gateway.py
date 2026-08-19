from __future__ import annotations

from fde_platform.identity import Environment, Principal, PrincipalType, RequestContext, TenantRef
from fde_platform.tools import (
    InMemoryToolGateway,
    ToolCall,
    ToolCapability,
    ToolDefinition,
    ToolResult,
)


def context() -> RequestContext:
    tenant = TenantRef("tenant-a", Environment.TEST)
    principal = Principal("user-a", PrincipalType.USER, tenant.tenant_id)
    return RequestContext(principal, tenant, "req-1", Environment.TEST)


def test_gateway_executes_registered_tool_with_explicit_capability() -> None:
    gateway = InMemoryToolGateway()
    gateway.register(
        ToolDefinition("lookup", "1.0.0", "read a record", frozenset({ToolCapability.READ})),
        lambda args: {"id": args["id"]},
    )

    result = gateway.invoke(
        context(), ToolCall("lookup", {"id": "V-1"}, "req-1", "call-1", frozenset({ToolCapability.READ}))
    )
    assert result == ToolResult(True, {"id": "V-1"})


def test_gateway_fails_closed_for_unknown_or_excessive_capability() -> None:
    gateway = InMemoryToolGateway()
    gateway.register(
        ToolDefinition("lookup", "1.0.0", "read a record", frozenset({ToolCapability.READ})),
        lambda args: args,
    )
    unknown = gateway.invoke(context(), ToolCall("missing", {}, "req-1", "call-1"))
    excessive = gateway.invoke(
        context(), ToolCall("lookup", {}, "req-1", "call-2", frozenset({ToolCapability.WRITE}))
    )
    assert unknown.error_code == "tool_not_found"
    assert excessive.error_code == "capability_denied"


def test_gateway_binds_call_to_request_context() -> None:
    gateway = InMemoryToolGateway()
    gateway.register(ToolDefinition("lookup", "1.0.0", "read", frozenset()), lambda args: args)
    result = gateway.invoke(context(), ToolCall("lookup", {}, "other-request", "call-1"))
    assert result.error_code == "request_context_mismatch"


def test_gateway_requires_approval_and_preserves_idempotent_result() -> None:
    gateway = InMemoryToolGateway()
    calls = 0

    def handler(_: dict[str, object]) -> ToolResult:
        nonlocal calls
        calls += 1
        return ToolResult(True, {"ok": True})

    gateway.register(ToolDefinition("delete", "1.0.0", "delete", frozenset({ToolCapability.DELETE}), True), handler)
    denied = gateway.invoke(context(), ToolCall("delete", {}, "req-1", "call-1", frozenset({ToolCapability.DELETE})))
    assert denied.error_code == "approval_required"
    assert calls == 0
