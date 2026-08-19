"""Month 4 logistics adapter."""

from __future__ import annotations

from typing import Any, Dict

from domain_agent import DomainAgentResult
from schemas import Domain

from ._base import normalize_result, requires_review_from_steps
from ._loader import load_domain_agent


class LogisticsDomainAdapter:
    domain = Domain.LOGISTICS

    def __init__(self) -> None:
        self._agent = None

    def _get_agent(self):
        if self._agent is None:
            module = load_domain_agent("month-4-logistics")
            self._agent = module.LogisticsAgent()
        return self._agent

    def evaluate(self, payload: Dict[str, Any]) -> DomainAgentResult:
        module = load_domain_agent("month-4-logistics")
        shipment = module.ShipmentPayload.model_validate(payload)
        report = self._get_agent().evaluate(shipment)
        return normalize_result(
            self.domain,
            report,
            confidence=1.0,
            requires_human_review=requires_review_from_steps(report.mitigation_plan, "requires_human_approval"),
            audit_metadata={"engine": "LogisticsAgent", "source": "month-4-logistics", "confidence_semantics": "deterministic_rule_engine"},
        )

    def health(self) -> Dict[str, Any]:
        return {"domain": self.domain.value, "status": "ready", "engine": "LogisticsAgent"}

    def capabilities(self) -> Dict[str, Any]:
        return {
            "trade_compliance": True,
            "cold_chain_detection": True,
            "shipment_risk": True,
            "deterministic_fallback": True,
            "human_in_the_loop": True,
        }
