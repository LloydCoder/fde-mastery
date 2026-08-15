"""Month 6 RevOps adapter."""

from __future__ import annotations

from typing import Any, Dict

from domain_agent import DomainAgentResult
from schemas import Domain

from ._base import has_manual_steps, normalize_result
from ._loader import load_domain_agent


class RevOpsDomainAdapter:
    domain = Domain.REVOPS

    def __init__(self) -> None:
        self._agent = None

    def _get_agent(self):
        if self._agent is None:
            module = load_domain_agent("month-6-revops")
            self._agent = module.RevOpsAgent()
        return self._agent

    def evaluate(self, payload: Dict[str, Any]) -> DomainAgentResult:
        module = load_domain_agent("month-6-revops")
        opportunity = module.OpportunityPayload.model_validate(payload)
        report = self._get_agent().evaluate(opportunity)
        requires_review = has_manual_steps(report.automation_workflow) or report.risk_tier.value in {"HIGH", "CRITICAL"}
        return normalize_result(
            self.domain,
            report,
            confidence=1.0,
            requires_human_review=requires_review,
            audit_metadata={"engine": "RevOpsAgent", "source": "month-6-revops", "confidence_semantics": "deterministic_rule_engine"},
        )

    def health(self) -> Dict[str, Any]:
        return {"domain": self.domain.value, "status": "ready", "engine": "RevOpsAgent"}

    def capabilities(self) -> Dict[str, Any]:
        return {
            "opportunity_health": True,
            "deal_governance": True,
            "churn_risk": True,
            "workflow_routing": True,
            "human_in_the_loop": True,
        }
