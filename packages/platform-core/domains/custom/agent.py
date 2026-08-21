"""Safe, deterministic custom-domain adapter.

Custom domains are configuration-driven in v1. The platform can classify and
recommend a next step, but it never executes tenant-defined actions directly.
"""

from __future__ import annotations

from typing import Any

from schemas import Domain
from shared_orchestrator.domain_agent import DomainAgentResult


class CustomDomainAgent:
    """Tenant-configurable recommendation engine with no autonomous side effects."""

    def evaluate(self, payload: dict[str, Any]) -> DomainAgentResult:
        if not isinstance(payload, dict) or not payload:
            raise ValueError("custom domain payload must be a non-empty object")

        risk = str(payload.get("risk_level", "medium")).strip().lower()
        if risk not in {"low", "medium", "high"}:
            raise ValueError("risk_level must be low, medium, or high")

        confidence = float(payload.get("confidence", 0.5))
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        reasons = [str(item) for item in payload.get("reasons", []) if str(item).strip()]
        requires_review = risk != "low" or confidence < 0.8
        return DomainAgentResult(
            domain=Domain.CUSTOM,
            result={
                "disposition": "REVIEW" if requires_review else "PROCEED_TO_APPROVAL",
                "risk_level": risk,
                "reasons": reasons,
                "recommended_next_step": (
                    "human_custom_domain_approval" if requires_review else "standard_approval_workflow"
                ),
            },
            confidence=confidence,
            requires_human_review=requires_review,
            audit_metadata={
                "engine": "CustomDomainAgent",
                "deployment_mode": "human_in_the_loop",
                "autonomous_side_effects": False,
            },
        )

    def health(self) -> dict[str, str]:
        return {"domain": "custom", "status": "ready", "engine": "CustomDomainAgent"}

    def capabilities(self) -> dict[str, Any]:
        return {
            "domain": "custom",
            "classification": True,
            "recommendation": True,
            "configuration_driven": True,
            "human_in_the_loop": True,
            "autonomous_side_effects": False,
        }
