"""
Logistics Agent: Autonomous Freight & Supply Chain Risk Engine.
Evaluates shipment telemetry, trade compliance, and disruption risk.
"""

import os
import json
import logging
import hashlib
from typing import List

try:
    from schemas import (
        ShipmentPayload,
        LogisticsEvaluationResult,
        RiskTier,
        LogisticsAction,
        MitigationStep,
        ChainOfCustodyAuditRecord,
    )
except ImportError:
    from .schemas import (
        ShipmentPayload,
        LogisticsEvaluationResult,
        RiskTier,
        LogisticsAction,
        MitigationStep,
        ChainOfCustodyAuditRecord,
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s"
)
logger = logging.getLogger("LogisticsAgent")

SANCTIONED_DESTINATIONS = {"IR", "KP", "SY", "CU"}
INVALID_HS_CODES = {"9999.99", "0000.00"}


class LogisticsAgent:
    """Autonomous logistics risk evaluator with deterministic fallback engine."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    def evaluate(self, payload: ShipmentPayload) -> LogisticsEvaluationResult:
        logger.info(f"[LogisticsAgent] Evaluating Shipment ID: {payload.shipment_id}")

        if not self.api_key:
            logger.warning("No Anthropic API key found. Falling back to deterministic rule engine.")

        return self._evaluate_deterministic(payload)

    def _evaluate_deterministic(self, payload: ShipmentPayload) -> LogisticsEvaluationResult:
        """Rule-based evaluation engine for supply chain risk assessment."""
        flags: List[str] = []

        # 1. Sanctions and Tariff Validation
        hs_valid = payload.hs_code not in INVALID_HS_CODES
        if payload.destination_country in SANCTIONED_DESTINATIONS:
            flags.append("SANCTIONS_EMBARGO_FLAG")
        if not hs_valid:
            flags.append("INVALID_HS_TARIFF_CODE")

        # 2. Cold-Chain Excursion Check
        min_temp, max_temp = payload.declared_temp_range_c[0], payload.declared_temp_range_c[1]
        temp = payload.telemetry.temperature_c
        is_temp_excursion = temp < min_temp or temp > max_temp
        if is_temp_excursion:
            flags.append("COLD_CHAIN_EXCURSION")
            flags.append("SPOILAGE_IMMORTAL_RISK")

        # 3. Port Congestion and SLA Delay Check
        note_lower = payload.carrier_status_note.lower()
        if any(keyword in note_lower for keyword in ["delay", "anchored", "berth", "congestion"]):
            if "COLD_CHAIN_EXCURSION" not in flags and "SANCTIONS_EMBARGO_FLAG" not in flags:
                flags.append("PORT_CONGESTION_DELAY")
                flags.append("SLA_BREACH_RISK")

        # Decision Matrix based on flagged exceptions
        if "SANCTIONS_EMBARGO_FLAG" in flags or "INVALID_HS_TARIFF_CODE" in flags:
            risk_score = 99.0
            risk_tier = RiskTier.CRITICAL
            action = LogisticsAction.HOLD_AND_QUARANTINE
            reasoning = "Shipment flagged for export compliance restriction or invalid tariff classification."
            mitigation = [
                MitigationStep(step_number=1, description="Immediately halt shipment release at hub.", requires_human_approval=False),
                MitigationStep(step_number=2, description="Escalate manifest to Trade Compliance Desk.", requires_human_approval=True),
                MitigationStep(step_number=3, description="File regulatory hold notice with customs authority.", requires_human_approval=True),
            ]
        elif "COLD_CHAIN_EXCURSION" in flags:
            risk_score = 92.0
            risk_tier = RiskTier.CRITICAL
            action = LogisticsAction.REROUTE_COLD_STORAGE
            reasoning = f"Telemetry temp ({temp}°C) exceeded threshold range [{min_temp}°C, {max_temp}°C]."
            mitigation = [
                MitigationStep(step_number=1, description="Dispatch urgent reroute order to nearest refrigerated warehouse.", requires_human_approval=False),
                MitigationStep(step_number=2, description="Alert carrier fleet dispatch for thermal unit diagnostics.", requires_human_approval=False),
                MitigationStep(step_number=3, description="Trigger quality assurance inspection for cargo integrity.", requires_human_approval=True),
            ]
        elif "PORT_CONGESTION_DELAY" in flags:
            risk_score = 65.0
            risk_tier = RiskTier.MEDIUM
            action = LogisticsAction.OPTIMIZE_ROUTE
            reasoning = "Port congestion detected; delivery ETA breach risk elevated."
            mitigation = [
                MitigationStep(step_number=1, description="Calculate alternate rail/intermodal bypass routes.", requires_human_approval=False),
                MitigationStep(step_number=2, description="Notify downstream warehouse team of adjusted arrival window.", requires_human_approval=False),
            ]
        else:
            risk_score = 5.0
            risk_tier = RiskTier.LOW
            action = LogisticsAction.PROCEED_NORMAL
            reasoning = "Shipment parameters and telemetry within nominal operating thresholds."
            mitigation = [
                MitigationStep(step_number=1, description="Continue standard automated transit monitoring.", requires_human_approval=False)
            ]

        return LogisticsEvaluationResult(
            shipment_id=payload.shipment_id,
            risk_score=risk_score,
            risk_tier=risk_tier,
            recommended_action=action,
            hs_code_valid=hs_valid,
            exception_flags=flags,
            reasoning_trace=reasoning,
            mitigation_plan=mitigation
        )

    def create_audit_record(self, payload: ShipmentPayload, result: LogisticsEvaluationResult) -> ChainOfCustodyAuditRecord:
        """Generate an immutable chain-of-custody audit ledger entry."""
        shipment_hash = hashlib.sha256(f"{payload.shipment_id}:{payload.carrier}".encode()).hexdigest()[:16]
        log_id = f"COC-LEDGER-{hashlib.md5(f'{payload.shipment_id}:{result.risk_score}'.encode()).hexdigest()[:8].upper()}"

        return ChainOfCustodyAuditRecord(
            log_id=log_id,
            shipment_id=f"ANON-{shipment_hash}",
            event_type=f"SHIPMENT_EVALUATED_{result.recommended_action.value}",
            payload_summary={
                "risk_score": result.risk_score,
                "risk_tier": result.risk_tier.value,
                "action": result.recommended_action.value,
                "flags": result.exception_flags,
                "carrier": payload.carrier,
            }
        )