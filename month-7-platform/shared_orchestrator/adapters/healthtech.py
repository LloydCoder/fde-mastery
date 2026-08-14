"""Month 3 HealthTech adapter."""

from __future__ import annotations

from typing import Any, Dict

from domain_agent import DomainAgentResult
from schemas import Domain

from ._base import normalize_result
from ._loader import load_domain_agent


class HealthTechDomainAdapter:
    domain = Domain.HEALTHTECH

    def __init__(self) -> None:
        self._agent = None

    def _get_agent(self):
        if self._agent is None:
            module = load_domain_agent("month-3-healthtech")
            self._agent = module.HealthTechAgent()
        return self._agent

    def evaluate(self, payload: Dict[str, Any]) -> DomainAgentResult:
        module = load_domain_agent("month-3-healthtech")
        encounter = module.HealthtechPayload.model_validate(payload)
        report = self._get_agent().evaluate_clinical_risk(encounter)
        requires_review = report.severity.value in {"HIGH", "CRITICAL"}
        return normalize_result(
            self.domain,
            report,
            confidence=1.0,
            requires_human_review=requires_review,
            audit_metadata={
                "engine": "HealthTechAgent",
                "source": "month-3-healthtech",
                "confidence_semantics": "deterministic_rule_engine",
                "clinical_decision_requires_qualified_human_review": True,
            },
        )

    def health(self) -> Dict[str, Any]:
        return {"domain": self.domain.value, "status": "ready", "engine": "HealthTechAgent"}

    def capabilities(self) -> Dict[str, Any]:
        return {
            "phi_deidentification": True,
            "clinical_triage": True,
            "deterministic_safeguards": True,
            "synthetic_data_only": True,
        }
