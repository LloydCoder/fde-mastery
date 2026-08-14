"""Month 1 cybersecurity adapter."""

from __future__ import annotations

import os
from typing import Any, Dict

from domain_agent import DomainAgentResult
from schemas import Domain

from ._base import normalize_result, requires_review_from_steps
from ._loader import load_domain_agent


class CybersecurityDomainAdapter:
    domain = Domain.CYBERSECURITY

    def __init__(self) -> None:
        self._agent = None

    def _get_agent(self):
        if self._agent is None:
            module = load_domain_agent("month-1-cybersecurity")
            self._agent = module.SOCTriageAgent(
                provider=os.getenv("CYBERSECURITY_LLM_PROVIDER", "openai")
            )
        return self._agent

    def evaluate(self, payload: Dict[str, Any]) -> DomainAgentResult:
        module = load_domain_agent("month-1-cybersecurity")
        model = module.RawSecurityLog.model_validate(payload)
        report = self._get_agent().triage_log(model)
        return normalize_result(
            self.domain,
            report,
            confidence=report.confidence_score,
            requires_human_review=requires_review_from_steps(
                report.mitigation_plan, "requires_human_approval"
            ),
            audit_metadata={"engine": "SOCTriageAgent", "source": "month-1-cybersecurity"},
        )

    def health(self) -> Dict[str, Any]:
        return {"domain": self.domain.value, "status": "ready", "engine": "SOCTriageAgent"}

    def capabilities(self) -> Dict[str, Any]:
        return {"triage": True, "providers": ["openai", "anthropic"], "mock_mode": True}
