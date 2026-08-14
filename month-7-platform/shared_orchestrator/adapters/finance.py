"""Month 2 finance adapter."""

from __future__ import annotations

from typing import Any, Dict

from domain_agent import DomainAgentResult
from schemas import Domain

from ._base import normalize_result, requires_review_from_steps
from ._loader import load_domain_agent


class FinanceDomainAdapter:
    domain = Domain.FINANCE

    def __init__(self) -> None:
        self._agent = None

    def _get_agent(self):
        if self._agent is None:
            module = load_domain_agent("month-2-finance")
            self._agent = module.FinancialRiskAgent()
        return self._agent

    def evaluate(self, payload: Dict[str, Any]) -> DomainAgentResult:
        module = load_domain_agent("month-2-finance")
        transaction = module.FinancialTransaction.model_validate(payload)
        report = self._get_agent().evaluate_transaction(transaction)
        return normalize_result(
            self.domain,
            report,
            confidence=report.confidence,
            requires_human_review=requires_review_from_steps(
                getattr(self._get_agent(), "build_mitigation_plan", lambda _: [])(report)
                if hasattr(self._get_agent(), "build_mitigation_plan") else [],
                "requires_human_approval",
            ) or report.recommended_action.value in {"FLAG_FOR_REVIEW", "FREEZE_ACCOUNT"},
            audit_metadata={"engine": "FinancialRiskAgent", "source": "month-2-finance"},
        )

    def health(self) -> Dict[str, Any]:
        return {"domain": self.domain.value, "status": "ready", "engine": "FinancialRiskAgent"}

    def capabilities(self) -> Dict[str, Any]:
        return {"transaction_risk": True, "aml_policy": True, "deterministic_fallback": True}
