"""Compatibility and safety base for Month 1-6 adapters."""
from __future__ import annotations

from typing import Any


class BaseLegacyAdapter:
    """Shared safety contract retained for all legacy domain adapters."""

    @staticmethod
    def _requires_review(payload: dict[str, Any]) -> bool:
        action = str(payload.get("recommended_action", payload.get("action", ""))).upper()
        high_impact = {
            "AUTO_CONTAIN",
            "FREEZE_ACCOUNT",
            "HOLD_AND_QUARANTINE",
            "REJECT_CONTRACT",
            "IMMEDIATE_INTERVENTION",
            "DISABLE_ACCOUNT",
            "ISOLATE_ENDPOINT",
            "CANCEL_SHIPMENT",
            "EXECUTE_PAYMENT",
            "SEND_PATIENT_ACTION",
        }
        return action in high_impact
