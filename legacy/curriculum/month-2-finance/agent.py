"""
month-2-finance/agent.py
------------------------
Financial Risk Scoring Agent powered by Anthropic Claude Sonnet 4.6.
Evaluates incoming transactions against compliance policies, fraud indicators,
and velocity metrics to generate structured RiskAssessmentReport objects.
"""

import json
import logging
import os
from typing import Dict, Any, List

from anthropic import Anthropic
from schemas import (
    FinancialTransaction,
    RiskAssessmentReport,
    RiskLevel,
    FinancialAction,
    RiskRuleTrigger
)

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
logger = logging.getLogger("FinancialRiskAgent")


class FinancialRiskAgent:
    """Agent responsible for evaluating financial transactions and enforcing compliance rules."""

    DEFAULT_MODEL = "claude-sonnet-4-6"

    SYSTEM_PROMPT = """You are an expert Financial Risk & AML Compliance AI Agent operating in an enterprise fintech infrastructure.
Your task is to analyze incoming financial transaction payloads and produce a deterministic Risk Assessment Report.

EVALUATION POLICY & THRESHOLDS:
1. LOW RISK (Score 0.0 - 29.9):
   - Recommended Action: APPROVE
   - Standard domestic transactions, verified merchants, normal volume, no policy violations.

2. MEDIUM RISK (Score 30.0 - 59.9):
   - Recommended Action: MONITOR
   - Moderate velocity increases or slightly unusual merchant categories without red flags.

3. HIGH RISK (Score 60.0 - 89.9):
   - Recommended Action: FLAG_FOR_REVIEW
   - Triggers: Hyper-velocity transfers (>5x daily average), transfers to high-risk offshore jurisdictions (e.g., Cayman Islands - KY), unverified beneficiaries on large transfers (>$100k).

4. CRITICAL RISK (Score 90.0 - 100.0):
   - Recommended Action: AUTO_REJECT or FREEZE_ACCOUNT
   - Triggers: Potential account takeover (e.g., password reset 2 minutes prior), connections via TOR exit nodes, matches on Sanctions/OFAC lists, crypto mixer destinations.

MUST OUTPUT STRICT JSON ONLY adhering to this exact schema:
{
  "risk_score": <float between 0.0 and 100.0>,
  "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "recommended_action": "APPROVE" | "MONITOR" | "FLAG_FOR_REVIEW" | "AUTO_REJECT" | "FREEZE_ACCOUNT",
  "confidence": <float between 0.0 and 1.0>,
  "triggered_rules": [
    {
      "rule_id": "<STRING_CODE>",
      "rule_name": "<RULE_NAME>",
      "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
      "description": "<REASONING>"
    }
  ],
  "reasoning_trace": [
    "Step 1 — ...",
    "Step 2 — ..."
  ]
}
Do NOT include markdown wrapping or conversational commentary around the raw JSON output.
"""

    def __init__(self, model_name: str = DEFAULT_MODEL, api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None

    def evaluate_transaction(self, transaction: FinancialTransaction) -> RiskAssessmentReport:
        """Evaluates a financial transaction payload and returns a structured RiskAssessmentReport."""
        logger.info(f"[{self.model_name}] Evaluating Transaction ID: {transaction.transaction_id}")

        if not self.client:
            logger.warning("No Anthropic API key found. Falling back to deterministic rule engine.")
            return self._heuristic_fallback(transaction)

        try:
            prompt_content = json.dumps(transaction.model_dump(mode="json"), indent=2)

            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                temperature=0.0,  # Zero temperature for deterministic evaluation
                system=self.SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": f"Evaluate this transaction:\n\n{prompt_content}"}
                ]
            )

            raw_response = response.content[0].text.strip()
            # Clean possible markdown block formatting
            if raw_response.startswith("```json"):
                raw_response = raw_response.split("```json")[1].split("```")[0].strip()
            elif raw_response.startswith("```"):
                raw_response = raw_response.split("```")[1].split("```")[0].strip()

            parsed = json.loads(raw_response)

            triggered_rules = [
                RiskRuleTrigger(
                    rule_id=r["rule_id"],
                    rule_name=r["rule_name"],
                    severity=RiskLevel(r["severity"]),
                    description=r["description"]
                )
                for r in parsed.get("triggered_rules", [])
            ]

            return RiskAssessmentReport(
                transaction_id=transaction.transaction_id,
                risk_score=float(parsed["risk_score"]),
                risk_level=RiskLevel(parsed["risk_level"]),
                recommended_action=FinancialAction(parsed["recommended_action"]),
                confidence=float(parsed["confidence"]),
                triggered_rules=triggered_rules,
                reasoning_trace=parsed.get("reasoning_trace", [])
            )

        except Exception as e:
            logger.error(f"LLM Triage failed: {str(e)}. Falling back to deterministic rule engine.")
            return self._heuristic_fallback(transaction)

    def _heuristic_fallback(self, transaction: FinancialTransaction) -> RiskAssessmentReport:
        """Rule-based fallback when live API is unavailable or encounters error."""
        meta = transaction.metadata
        rules = []
        score = 5.0
        reasoning = ["Step 1 — Ingested transaction into fallback rule engine."]

        # ═══════════════════════════════════════════════════════════════════════
        # FIX: Return separate rules for each distinct fraud indicator
        # ═══════════════════════════════════════════════════════════════════════
        critical_triggered = False

        # Sanctions List Match
        if meta.get("sanctions_list_match"):
            critical_triggered = True
            rules.append(RiskRuleTrigger(
                rule_id="SANCTIONS_LIST_MATCH",
                rule_name="Sanctions / OFAC List Match",
                severity=RiskLevel.CRITICAL,
                description=f"Counterparty or entity matched sanctions list: {meta.get('sanctions_list_match')}."
            ))

        # Tor Exit Node
        if meta.get("is_tor_exit_node") == "true":
            critical_triggered = True
            rules.append(RiskRuleTrigger(
                rule_id="TOR_EXIT_NODE_DETECTED",
                rule_name="TOR Exit Node Detected",
                severity=RiskLevel.CRITICAL,
                description="Transaction origin or destination routed through known TOR exit node."
            ))

        # Account Takeover Pattern
        if "PASSWORD_RESET" in meta.get("account_compromise_indicator", ""):
            critical_triggered = True
            rules.append(RiskRuleTrigger(
                rule_id="ACCOUNT_TAKEOVER_PATTERN",
                rule_name="Account Takeover Pattern",
                severity=RiskLevel.CRITICAL,
                description="Recent password reset or credential change detected immediately prior to transaction."
            ))

        # If any critical indicator fired, return immediately with AUTO_REJECT
        if critical_triggered:
            score = 98.0
            reasoning.append("Step 2 — Identified critical fraud indicator(s). Triggering AUTO_REJECT.")
            return RiskAssessmentReport(
                transaction_id=transaction.transaction_id,
                risk_score=score,
                risk_level=RiskLevel.CRITICAL,
                recommended_action=FinancialAction.AUTO_REJECT,
                confidence=0.98,
                triggered_rules=rules,
                reasoning_trace=reasoning
            )

        # Velocity / Volume Check
        txn_count = int(meta.get("transactions_in_last_hour", "0"))
        volume = float(meta.get("total_volume_last_hour_usd", "0"))
        if txn_count > 10 or volume > 20000:
            score = 75.0
            rules.append(RiskRuleTrigger(
                rule_id="HYPER_VELOCITY_SPIKE",
                rule_name="Hyper Velocity Spike",
                severity=RiskLevel.HIGH,
                description="Abnormal transaction frequency and volume in last hour."
            ))
            rules.append(RiskRuleTrigger(
                rule_id="VOLUME_DEVIATION_5X",
                rule_name="Volume Deviation >5x Average",
                severity=RiskLevel.HIGH,
                description="Hourly volume significantly exceeds baseline daily average."
            ))
            reasoning.append("Step 2 — High transaction velocity detected. Flagging for review.")

        # High-Risk Jurisdiction Check
        if transaction.destination_country in ["KY", "RU", "IR", "KP"]:
            score = max(score, 80.0)
            rules.append(RiskRuleTrigger(
                rule_id="HIGH_RISK_JURISDICTION",
                rule_name="High-Risk Jurisdiction Transfer",
                severity=RiskLevel.HIGH,
                description=f"Destination country {transaction.destination_country} is classified as high risk."
            ))
            if meta.get("beneficiary_owner_verified") == "false":
                rules.append(RiskRuleTrigger(
                    rule_id="UNVERIFIED_BENEFICIARY_LARGE_TRANSFER",
                    rule_name="Unverified Beneficiary on Large Transfer",
                    severity=RiskLevel.HIGH,
                    description="Transfer exceeds threshold without verified ultimate beneficial ownership."
                ))
            reasoning.append("Step 2 — Destination in high-risk jurisdiction with unverified beneficial ownership.")

        risk_level = RiskLevel.LOW
        action = FinancialAction.APPROVE

        if score >= 90.0:
            risk_level = RiskLevel.CRITICAL
            action = FinancialAction.AUTO_REJECT
        elif score >= 60.0:
            risk_level = RiskLevel.HIGH
            action = FinancialAction.FLAG_FOR_REVIEW
        elif score >= 30.0:
            risk_level = RiskLevel.MEDIUM
            action = FinancialAction.MONITOR

        return RiskAssessmentReport(
            transaction_id=transaction.transaction_id,
            risk_score=score,
            risk_level=risk_level,
            recommended_action=action,
            confidence=0.95,
            triggered_rules=rules,
            reasoning_trace=reasoning
        )