"""Policy-as-code gate for high-impact domain actions."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    requires_human_approval: bool = False


def evaluate_action(*, action: str, confidence: float, severity: str = "low", amount: float | None = None, client_tier: str = "standard") -> PolicyDecision:
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0 and 1")
    normalized = severity.lower()
    high_impact = normalized in {"critical", "high"} or action in {"account_freeze", "auto_contain", "payment_reversal"}
    approval_threshold = 0.90 if client_tier == "enterprise" else 0.95
    if high_impact and (confidence < approval_threshold or (amount is not None and amount >= 10_000)):
        return PolicyDecision(False, "high-impact action requires human approval", True)
    return PolicyDecision(True, "policy allows action")
