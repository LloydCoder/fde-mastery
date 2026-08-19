"""Procurement domain contract and deterministic v1 workflow engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProcurementResult:
    disposition: str
    risk_level: str
    confidence: float
    reasons: list[str]
    requires_human_review: bool
    recommended_next_step: str


class ProcurementAgent:
    """Deployment-safe procurement analyst; recommendation-only in v1."""

    def evaluate(self, payload: dict[str, Any]) -> ProcurementResult:
        supplier_id = str(payload.get("supplier_id", "")).strip()
        quote_amount = float(payload.get("quote_amount_usd", 0) or 0)
        risk_score = float(payload.get("supplier_risk_score", 0) or 0)
        policy_limit = float(payload.get("approval_threshold_usd", 50000) or 50000)
        quotes = int(payload.get("quote_count", 1) or 1)
        reasons: list[str] = []
        if not supplier_id:
            raise ValueError("supplier_id is required")
        if quote_amount < 0 or not 0 <= risk_score <= 100:
            raise ValueError("quote amount/risk score is outside the supported range")
        risk_level = "high" if risk_score >= 70 else "medium" if risk_score >= 40 else "low"
        if risk_level != "low":
            reasons.append("supplier risk score requires review")
        if quotes < 2:
            reasons.append("fewer than two comparable quotes supplied")
        if quote_amount >= policy_limit:
            reasons.append("quote meets or exceeds approval threshold")
        requires_review = quote_amount >= policy_limit or risk_level != "low" or quotes < 2
        return ProcurementResult(
            disposition="REVIEW" if requires_review else "PROCEED_TO_APPROVAL",
            risk_level=risk_level,
            confidence=0.92 if reasons else 0.88,
            reasons=reasons,
            requires_human_review=requires_review,
            recommended_next_step="human_procurement_approval" if requires_review else "standard_approval_workflow",
        )

    def health(self) -> dict[str, str]:
        return {"domain": "procurement", "status": "ready", "engine": "ProcurementAgent"}

    def capabilities(self) -> dict[str, bool]:
        return {"supplier_risk": True, "quote_comparison": True, "spend_thresholds": True, "human_in_the_loop": True, "autonomous_purchase_order": False, "autonomous_supplier_award": False}
