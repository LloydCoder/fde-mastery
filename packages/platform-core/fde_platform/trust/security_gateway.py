"""Policy-first enforcement boundary for agent and tool actions.

The LLM proposes actions; this gateway is authoritative for execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping

from ..identity import RequestContext


@dataclass(frozen=True, slots=True)
class ActionRequest:
    context: RequestContext
    agent_id: str
    action: str
    resource: str | None = None
    risk_level: int = 0
    data_classification: str = "internal"
    attributes: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.agent_id.strip() or not self.action.strip():
            raise ValueError("agent_id and action are required")
        if not 0 <= self.risk_level <= 5:
            raise ValueError("risk_level must be between 0 and 5")


@dataclass(frozen=True, slots=True)
class SecurityDecision:
    allowed: bool
    reason: str
    requires_approval: bool = False
    policy_id: str | None = None


class SecurityGateway:
    """Independent policy enforcement point for proposed agent actions."""

    def __init__(self, policy: Callable[[ActionRequest], SecurityDecision] | None = None) -> None:
        self._policy = policy or self._default_policy

    @staticmethod
    def _default_policy(request: ActionRequest) -> SecurityDecision:
        if request.risk_level >= 4:
            return SecurityDecision(False, "high-impact action requires explicit approval", True, "risk-tier-v1")
        if request.data_classification == "restricted" and request.risk_level >= 3:
            return SecurityDecision(False, "restricted data action requires approval", True, "data-policy-v1")
        return SecurityDecision(True, "allowed by baseline policy", False, "baseline-v1")

    def authorize(self, request: ActionRequest) -> SecurityDecision:
        decision = self._policy(request)
        if not decision.allowed and not decision.requires_approval:
            return decision
        if decision.requires_approval:
            return decision
        return SecurityDecision(True, decision.reason, False, decision.policy_id)
