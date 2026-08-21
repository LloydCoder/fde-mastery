"""Security-gated Tool Gateway adapter for agent execution."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fde_platform.identity import RequestContext
from fde_platform.tools import ToolGateway
from fde_platform.tools.models import ToolCall, ToolCapability, ToolResult

from .agentic import AgentAction, AgentActionSecurityGate, AgentSecurityContext, RiskTier


class AgentSecureToolGateway(ToolGateway):
    """Wrap the existing Tool Gateway with an agentic pre-action security gate."""

    def __init__(self, delegate: ToolGateway, security_context: AgentSecurityContext,
                 gate: AgentActionSecurityGate | None = None) -> None:
        self._delegate = delegate
        self._security_context = security_context
        self._gate = gate or AgentActionSecurityGate()

    def register(self, definition, handler: Callable[[dict[str, Any]], Any]) -> None:
        self._delegate.register(definition, handler)

    def invoke(self, context: RequestContext, call: ToolCall) -> ToolResult:
        if call.request_id != self._security_context.request_id or call.tenant_id != self._security_context.tenant_id:
            return ToolResult(False, error_code="agent_security_context_mismatch")
        risk = RiskTier.LOW
        if ToolCapability.DELETE in call.capabilities:
            risk = RiskTier.CRITICAL
        elif ToolCapability.WRITE in call.capabilities:
            risk = RiskTier.HIGH
        elif ToolCapability.EXTERNAL_NETWORK in call.capabilities:
            risk = RiskTier.MEDIUM
        action = AgentAction(
            tool_name=call.tool_name,
            tenant_id=call.tenant_id,
            capabilities=frozenset(cap.value for cap in call.capabilities),
            risk=risk,
            irreversible=risk is RiskTier.CRITICAL,
            external_side_effect=ToolCapability.EXTERNAL_NETWORK in call.capabilities,
        )
        decision = self._gate.evaluate(self._security_context, action)
        if not decision.allowed:
            return ToolResult(False, error_code=decision.reason)
        return self._delegate.invoke(context, call)
