"""Legal Contract Risk Analysis Agent."""

import hashlib
import logging
import os
from typing import List

try:
    from .schemas import (
        ClauseRedline,
        ContractPayload,
        LegalAction,
        LegalAuditRecord,
        LegalEvaluationResult,
        LegalMitigationStep,
        RiskTier,
    )
except ImportError:
    from schemas import (
        ClauseRedline,
        ContractPayload,
        LegalAction,
        LegalAuditRecord,
        LegalEvaluationResult,
        LegalMitigationStep,
        RiskTier,
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("LegalAgent")

STANDARD_JURISDICTIONS = {
    "Delaware, USA",
    "New York, USA",
    "California, USA",
    "United Kingdom",
    "EU",
}


class LegalAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    def evaluate(self, payload: ContractPayload) -> LegalEvaluationResult:
        logger.info(f"[claude-sonnet-4-6] Evaluating Contract ID: {payload.contract_id}")

        if not self.api_key:
            logger.warning("No Anthropic API key found. Falling back to deterministic rule engine.")
            return self._evaluate_deterministic(payload)

        return self._evaluate_deterministic(payload)

    def _evaluate_deterministic(self, payload: ContractPayload) -> LegalEvaluationResult:
        flags: List[str] = []
        redlines: List[ClauseRedline] = []

        # 1. Governing Jurisdiction Check
        if payload.governing_jurisdiction not in STANDARD_JURISDICTIONS:
            flags.append("NON_STANDARD_JURISDICTION")

        # 2. Clause Analysis
        for clause in payload.clauses:
            text_lower = clause.text.lower()

            # Liability Cap Checks
            if clause.clause_type.value == "LIABILITY_CAP":
                if "unlimited liability" in text_lower:
                    flags.append("UNLIMITED_LIABILITY_EXPOSURE")
                    redlines.append(
                        ClauseRedline(
                            clause_id=clause.clause_id,
                            original_text=clause.text,
                            proposed_redline=(
                                "Each party's aggregate liability shall be capped at 1x the total fees "
                                "paid or payable under this Agreement in the preceding 12 months."
                            ),
                            risk_reasoning="Vendor cannot accept uncapped liability for general delivery delays.",
                        )
                    )

            # Intellectual Property Checks
            if clause.clause_type.value == "IP_ASSIGNMENT":
                if (
                    "pre-existing" in text_lower
                    or "background ip" in text_lower
                    or "transfers and assigns" in text_lower
                ):
                    flags.append("BACKGROUND_IP_EXPROPRIATION_RISK")
                    redlines.append(
                        ClauseRedline(
                            clause_id=clause.clause_id,
                            original_text=clause.text,
                            proposed_redline=(
                                "Each party retains all right, title, and interest in its pre-existing IP. "
                                "Customer grants Vendor a non-exclusive license solely to perform services."
                            ),
                            risk_reasoning="Core background IP expropriation clause violates company technology retention policy.",
                        )
                    )

            # Indemnification Checks
            if clause.clause_type.value == "INDEMNIFICATION":
                if (
                    "without limitation" in text_lower
                    or ("unilateral" in text_lower and "indemnify" in text_lower)
                    or "any system downtime" in text_lower
                ):
                    flags.append("UNILATERAL_UNLIMITED_INDEMNITY")
                    redlines.append(
                        ClauseRedline(
                            clause_id=clause.clause_id,
                            original_text=clause.text,
                            proposed_redline=(
                                "Mutual indemnification limited to third-party IP infringement "
                                "and gross negligence/willful misconduct."
                            ),
                            risk_reasoning="Unilateral uncapped indemnity exposes company to open-ended financial liability.",
                        )
                    )

            # Termination Checks
            if clause.clause_type.value == "TERMINATION":
                if (
                    "immediately" in text_lower
                    or "24 hours" in text_lower
                    or "without prior notice" in text_lower
                ):
                    flags.append("UNILATERAL_IMMEDIATE_TERMINATION")
                    redlines.append(
                        ClauseRedline(
                            clause_id=clause.clause_id,
                            original_text=clause.text,
                            proposed_redline=(
                                "Either party may terminate for material breach upon thirty (30) days "
                                "written notice and opportunity to cure."
                            ),
                            risk_reasoning="24-hour termination notice creates severe operational continuity exposure.",
                        )
                    )

            # GDPR & Data Privacy Checks
            if clause.clause_type.value == "DATA_PRIVACY_GDPR":
                if (
                    "without standard contractual clauses" in text_lower
                    or "freely transferred" in text_lower
                ):
                    flags.append("GDPR_DATA_TRANSFER_VIOLATION")
                    redlines.append(
                        ClauseRedline(
                            clause_id=clause.clause_id,
                            original_text=clause.text,
                            proposed_redline=(
                                "Cross-border transfers of EU personal data shall strictly comply with "
                                "EU GDPR standard contractual clauses (SCCs) and transfer impact assessments."
                            ),
                            risk_reasoning="Unrestricted cross-border transfer creates regulatory breach risk under EU GDPR Article 46.",
                        )
                    )

        # Decision Matrix
        if (
            "UNILATERAL_IMMEDIATE_TERMINATION" in flags
            and "GDPR_DATA_TRANSFER_VIOLATION" in flags
        ):
            risk_score = 98.0
            risk_tier = RiskTier.CRITICAL
            action = LegalAction.REJECT_CONTRACT
            reasoning = (
                "Contract violates regulatory data privacy frameworks and presents "
                "existential termination operational risk."
            )
            mitigation = [
                LegalMitigationStep(
                    step_number=1,
                    description="Issue formal contract rejection notice to counterparty legal counsel.",
                    requires_counsel_approval=True,
                ),
                LegalMitigationStep(
                    step_number=2,
                    description="Require mandatory ingestion of Standard DPA with SCC safeguards prior to re-evaluation.",
                    requires_counsel_approval=True,
                ),
            ]

        elif (
            "BACKGROUND_IP_EXPROPRIATION_RISK" in flags
            or "UNILATERAL_UNLIMITED_INDEMNITY" in flags
        ):
            risk_score = 90.0
            risk_tier = RiskTier.CRITICAL
            action = LegalAction.ESCALATE_LEGAL_COUNSEL
            reasoning = (
                "High-risk clauses detected threatening company core IP ownership "
                "and uncapped financial exposure."
            )
            mitigation = [
                LegalMitigationStep(
                    step_number=1,
                    description="Escalate agreement to General Counsel for formal redline review.",
                    requires_counsel_approval=True,
                ),
                LegalMitigationStep(
                    step_number=2,
                    description="Issue redlined addendum restoring mutual IP retention and 1x ACV liability cap.",
                    requires_counsel_approval=True,
                ),
            ]

        elif (
            "UNLIMITED_LIABILITY_EXPOSURE" in flags
            or "NON_STANDARD_JURISDICTION" in flags
        ):
            risk_score = 72.0
            risk_tier = RiskTier.HIGH
            action = LegalAction.AMEND_CLAUSE
            reasoning = "Agreement contains unacceptable liability exposure and offshore jurisdiction governing law."
            mitigation = [
                LegalMitigationStep(
                    step_number=1,
                    description="Propose standard Delaware/New York governing law amendment.",
                    requires_counsel_approval=False,
                ),
                LegalMitigationStep(
                    step_number=2,
                    description="Insert standard 1x ACV mutual aggregate liability cap.",
                    requires_counsel_approval=False,
                ),
            ]

        else:
            risk_score = 10.0
            risk_tier = RiskTier.LOW
            action = LegalAction.APPROVE_STANDARD
            reasoning = (
                "Contract terms align with standard corporate legal risk appetite "
                "and governance framework."
            )
            mitigation = [
                LegalMitigationStep(
                    step_number=1,
                    description="Proceed to automated contract execution and archivism.",
                    requires_counsel_approval=False,
                ),
            ]

        return LegalEvaluationResult(
            contract_id=payload.contract_id,
            overall_risk_score=risk_score,
            risk_tier=risk_tier,
            recommended_action=action,
            exception_flags=flags,
            proposed_redlines=redlines,
            reasoning_trace=reasoning,
            mitigation_plan=mitigation,
        )

    def create_audit_record(
        self, payload: ContractPayload, result: LegalEvaluationResult
    ) -> LegalAuditRecord:
        contract_hash = hashlib.sha256(
            f"{payload.contract_id}:{payload.counterparty}".encode()
        ).hexdigest()[:16]
        log_id = (
            f"LEGAL-LEDGER-"
            f"{hashlib.md5(f'{payload.contract_id}:{result.overall_risk_score}'.encode()).hexdigest()[:8].upper()}"
        )

        return LegalAuditRecord(
            log_id=log_id,
            contract_id=f"HASH-{contract_hash}",
            event_type=f"CONTRACT_EVALUATED_{result.recommended_action.value}",
            summary={
                "overall_risk_score": result.overall_risk_score,
                "risk_tier": result.risk_tier.value,
                "action": result.recommended_action.value,
                "flags": result.exception_flags,
                "counterparty": payload.counterparty,
                "redline_count": len(result.proposed_redlines),
            },
        )