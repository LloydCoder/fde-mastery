"""Procurement domain adapter using the shared deployment envelope."""

from __future__ import annotations

from typing import Any, Dict

from domain_agent import DomainAgentResult
from schemas import Domain
from domains.procurement.agent import ProcurementAgent

from ._base import normalize_result


class ProcurementDomainAdapter:
    domain = Domain.PROCUREMENT

    def __init__(self) -> None:
        self._agent = ProcurementAgent()

    def evaluate(self, payload: Dict[str, Any]) -> DomainAgentResult:
        report = self._agent.evaluate(payload)
        return normalize_result(
            self.domain,
            report,
            confidence=report.confidence,
            requires_human_review=report.requires_human_review,
            audit_metadata={"engine": "ProcurementAgent", "source": "domains/procurement", "review_boundary": "procurement_approval_policy"},
        )

    def health(self) -> Dict[str, Any]:
        return self._agent.health()

    def capabilities(self) -> Dict[str, Any]:
        return self._agent.capabilities()
