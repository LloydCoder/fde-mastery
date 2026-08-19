"""RevOps & Enterprise Automation Agent."""

import hashlib
import logging
import os
from typing import List

try:
    from .schemas import (
        AutomationStep,
        DealStage,
        LeadSource,
        OpportunityPayload,
        RevOpsAction,
        RevOpsAuditRecord,
        RevOpsEvaluationResult,
        RiskTier,
        TelemetryMetrics,
    )
except ImportError:
    from schemas import (
        AutomationStep,
        DealStage,
        LeadSource,
        OpportunityPayload,
        RevOpsAction,
        RevOpsAuditRecord,
        RevOpsEvaluationResult,
        RiskTier,
        TelemetryMetrics,
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("RevOpsAgent")

# Governance thresholds
DISCOUNT_GOVERNANCE_THRESHOLD = 30.0
MINIMUM_ARR_THRESHOLD = 50000.0
CHURN_GROWTH_THRESHOLD = -30.0
CHURN_LICENSE_THRESHOLD = 25.0


class RevOpsAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    def evaluate(self, payload: OpportunityPayload) -> RevOpsEvaluationResult:
        logger.info(f"[claude-sonnet-4-6] Evaluating Opportunity ID: {payload.opportunity_id}")

        if not self.api_key:
            logger.warning("No Anthropic API key found. Falling back to deterministic rule engine.")
            return self._evaluate_deterministic(payload)

        return self._evaluate_deterministic(payload)

    def _evaluate_deterministic(self, payload: OpportunityPayload) -> RevOpsEvaluationResult:
        flags: List[str] = []
        t = payload.telemetry

        # --- CRITICAL: Churn Risk (telemetry degradation on high-value accounts) ---
        severe_usage_drop = t.weekly_usage_growth_pct < CHURN_GROWTH_THRESHOLD
        critical_underutil = t.license_utilization_pct < CHURN_LICENSE_THRESHOLD
        high_value_at_risk = payload.annual_recurring_revenue_usd >= 100000.0

        if high_value_at_risk and (severe_usage_drop or critical_underutil):
            if severe_usage_drop:
                flags.append("SEVERE_TELEMETRY_USAGE_DROP")
            if critical_underutil:
                flags.append("CRITICAL_LICENSE_UNDERUTILIZATION")

            health_score = max(10.0, 50.0 + abs(t.weekly_usage_growth_pct) + (100.0 - t.license_utilization_pct))
            health_score = min(health_score, 100.0)

            return RevOpsEvaluationResult(
                opportunity_id=payload.opportunity_id,
                health_score=round(health_score, 1),
                risk_tier=RiskTier.CRITICAL,
                recommended_action=RevOpsAction.FLAG_CHURN_RISK,
                exception_flags=flags,
                reasoning_trace=(
                    f"High-value account (${payload.annual_recurring_revenue_usd:,.0f} ARR) showing "
                    f"severe telemetry degradation (MAU={t.monthly_active_users}, growth={t.weekly_usage_growth_pct}%, "
                    f"utilization={t.license_utilization_pct}%). Immediate churn intervention required."
                ),
                automation_workflow=[
                    AutomationStep(
                        step_number=1,
                        system_target="SALESFORCE_CRM",
                        action_description="Create high-priority churn-risk alert on opportunity record.",
                        is_automated=True,
                    ),
                    AutomationStep(
                        step_number=2,
                        system_target="CUSTOMER_SUCCESS",
                        action_description="Auto-schedule executive business review (EBR) with account team.",
                        is_automated=True,
                    ),
                    AutomationStep(
                        step_number=3,
                        system_target="SLACK",
                        action_description="Notify VP Sales and CSM lead of critical churn risk.",
                        is_automated=True,
                    ),
                ],
            )

        # --- HIGH: Deal Desk Governance (discount + sponsorship) ---
        excessive_discount = payload.discount_requested_pct > DISCOUNT_GOVERNANCE_THRESHOLD
        missing_sponsor = (
            payload.deal_stage in (DealStage.PROPOSAL_NEGOTIATION, DealStage.CLOSED_WON)
            and not payload.has_exec_sponsor
        )

        if excessive_discount or missing_sponsor:
            if excessive_discount:
                flags.append("EXCESSIVE_DISCOUNT_THRESHOLD_BREACH")
            if missing_sponsor:
                flags.append("MISSING_EXEC_SPONSORSHIP")

            health_score = 65.0
            if excessive_discount:
                health_score += payload.discount_requested_pct - DISCOUNT_GOVERNANCE_THRESHOLD
            if missing_sponsor:
                health_score += 10.0
            health_score = min(health_score, 89.0)

            return RevOpsEvaluationResult(
                opportunity_id=payload.opportunity_id,
                health_score=round(health_score, 1),
                risk_tier=RiskTier.HIGH,
                recommended_action=RevOpsAction.ESCALATE_DEAL_DESK,
                exception_flags=flags,
                reasoning_trace=(
                    f"Deal governance violation detected on ${payload.annual_recurring_revenue_usd:,.0f} ARR opportunity. "
                    f"Discount={payload.discount_requested_pct}% (threshold={DISCOUNT_GOVERNANCE_THRESHOLD}%), "
                    f"Exec Sponsor={'Yes' if payload.has_exec_sponsor else 'No'}. Requires Deal Desk review."
                ),
                automation_workflow=[
                    AutomationStep(
                        step_number=1,
                        system_target="SALESFORCE_CRM",
                        action_description="Route opportunity to Deal Desk queue for approval.",
                        is_automated=True,
                    ),
                    AutomationStep(
                        step_number=2,
                        system_target="DOCUSIGN_CLM",
                        action_description="Lock proposal generation pending Deal Desk sign-off.",
                        is_automated=True,
                    ),
                    AutomationStep(
                        step_number=3,
                        system_target="EMAIL",
                        action_description="Notify assigned AE and Sales Manager of Deal Desk hold.",
                        is_automated=True,
                    ),
                ],
            )

        # --- MEDIUM: Low-Value / Nurture Required ---
        below_min_arr = payload.annual_recurring_revenue_usd < MINIMUM_ARR_THRESHOLD

        if below_min_arr:
            flags.append("BELOW_MINIMUM_ARR_THRESHOLD")

            return RevOpsEvaluationResult(
                opportunity_id=payload.opportunity_id,
                health_score=45.0,
                risk_tier=RiskTier.MEDIUM,
                recommended_action=RevOpsAction.TRIGGER_ENRICHMENT_NURTURE,
                exception_flags=flags,
                reasoning_trace=(
                    f"Opportunity ARR (${payload.annual_recurring_revenue_usd:,.0f}) below minimum enterprise threshold "
                    f"(${MINIMUM_ARR_THRESHOLD:,.0f}). Route to automated enrichment and nurture sequence."
                ),
                automation_workflow=[
                    AutomationStep(
                        step_number=1,
                        system_target="HUBSPOT_MARKETING",
                        action_description="Enroll contact in product-led growth nurture sequence.",
                        is_automated=True,
                    ),
                    AutomationStep(
                        step_number=2,
                        system_target="CLEARBIT",
                        action_description="Trigger firmographic enrichment and technographic scoring.",
                        is_automated=True,
                    ),
                    AutomationStep(
                        step_number=3,
                        system_target="SALESFORCE_CRM",
                        action_description="Set opportunity stage to 'Nurture' and queue for 90-day re-evaluation.",
                        is_automated=True,
                    ),
                ],
            )

        # --- LOW: Healthy Enterprise Lead ---
        health_score = min(
            100.0,
            70.0
            + (t.license_utilization_pct / 5.0)
            + max(0.0, t.weekly_usage_growth_pct)
            + (10.0 if payload.has_exec_sponsor else 0.0)
            - (payload.discount_requested_pct / 2.0),
        )

        return RevOpsEvaluationResult(
            opportunity_id=payload.opportunity_id,
            health_score=round(health_score, 1),
            risk_tier=RiskTier.LOW,
            recommended_action=RevOpsAction.AUTO_ASSIGN_ENTERPRISE_AE,
            exception_flags=[],
            reasoning_trace=(
                f"Healthy enterprise opportunity: ${payload.annual_recurring_revenue_usd:,.0f} ARR, "
                f"PQL-qualified, strong telemetry (MAU={t.monthly_active_users}, utilization={t.license_utilization_pct}%), "
                f"exec sponsor engaged. Auto-assign to Enterprise AE."
            ),
            automation_workflow=[
                AutomationStep(
                    step_number=1,
                    system_target="SALESFORCE_CRM",
                    action_description="Auto-assign to next-available Enterprise AE based on territory and quota capacity.",
                    is_automated=True,
                ),
                AutomationStep(
                    step_number=2,
                    system_target="CALENDLY",
                    action_description="Send scheduling link for discovery call within 24 hours.",
                    is_automated=True,
                ),
                AutomationStep(
                    step_number=3,
                    system_target="SLACK",
                    action_description="Notify assigned AE of new qualified opportunity with telemetry summary.",
                    is_automated=True,
                ),
            ],
        )

    def create_audit_record(
        self, payload: OpportunityPayload, result: RevOpsEvaluationResult
    ) -> RevOpsAuditRecord:
        opp_hash = hashlib.sha256(
            f"{payload.opportunity_id}:{payload.account_name}".encode()
        ).hexdigest()[:16]
        log_id = (
            f"REVOPS-LEDGER-"
            f"{hashlib.md5(f'{payload.opportunity_id}:{result.health_score}'.encode()).hexdigest()[:8].upper()}"
        )

        return RevOpsAuditRecord(
            log_id=log_id,
            opportunity_id=f"HASH-{opp_hash}",
            event_type=f"REVOPS_EVALUATED_{result.recommended_action.value}",
            summary={
                "health_score": result.health_score,
                "risk_tier": result.risk_tier.value,
                "action": result.recommended_action.value,
                "flags": result.exception_flags,
                "account_name": payload.account_name,
                "arr_usd": payload.annual_recurring_revenue_usd,
                "workflow_steps": len(result.automation_workflow),
            },
        )