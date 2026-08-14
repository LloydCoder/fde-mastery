"""Month 5 legal adapter."""

from __future__ import annotations

from typing import Any, Dict

from domain_agent import DomainAgentResult
from schemas import Domain

from ._base import normalize_result, requires_review_from_steps
from ._loader import load_domain_agent


class LegalDomainAdapter:
    domain = Domain.LEGAL

    def __init__(self) -> None:
        self._agent = None

    def _get_agent(self):
        if self._agent is None:
            module = load_domain_agent("month-5-legal")
            self._agent = module.LegalAgent()
        return self._agent

    def evaluate(self, payload: Dict[str, Any]) -> DomainAgentResult:
        module = load_domain_agent("month-5-legal")
        contract = module.ContractPayload.model_validate(payload)
        report = self._get_agent().evaluate(contract)
        return normalize_result(
            self.domain,
            report,
            confidence=1.0,
            requires_human_review=requires_review_from_steps(
                report.mitigation_plan, "requires_counsel_approval"
            ) or report.recommended_action.value in {"ESCALATE_LEGAL_COUNSEL", "REJECT_CONTRACT"},
            audit_metadata={
                "engine": "LegalAgent",
                "source": "month-5-legal",
                "confidence_semantics": "deterministic_rule_engine",
                "legal_advice_disclaimer": True,
            },
        )

    def health(self) -> Dict[str, Any]:
        return {"domain": self.domain.value, "status": "ready", "engine": "LegalAgent"}

    def capabilities(self) -> Dict[str, Any]:
        return {
            "contract_risk": True,
            "clause_analysis": True,
            "redline_generation": True,
            "counsel_escalation": True,
        }
