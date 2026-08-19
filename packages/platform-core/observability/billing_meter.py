"""Per-API-call invoicing and billing meter."""

from datetime import datetime, timedelta
from typing import Any, Dict, List

try:
    from ..schemas import BillingRecord
except ImportError:
    from schemas import BillingRecord


# Tier pricing (USD per API call)
TIER_PRICING = {
    "starter": 0.05,
    "growth": 0.03,
    "enterprise": 0.015,
}


class BillingMeter:
    """Tracks API usage per client and generates billing records."""

    def __init__(self):
        self._usage: Dict[str, Dict[str, Any]] = {}

    def record_call(self, client_id: str, domain: str, tier: str = "growth") -> None:
        if client_id not in self._usage:
            self._usage[client_id] = {
                "tier": tier,
                "calls_by_domain": {},
                "total_calls": 0,
                "period_start": datetime.now().isoformat(),
            }

        self._usage[client_id]["calls_by_domain"][domain] = (
            self._usage[client_id]["calls_by_domain"].get(domain, 0) + 1
        )
        self._usage[client_id]["total_calls"] += 1

    def generate_invoice(self, client_id: str) -> BillingRecord:
        data = self._usage.get(client_id)
        if not data:
            raise ValueError(f"No usage data for client: {client_id}")

        tier = data["tier"]
        rate = TIER_PRICING.get(tier, 0.03)
        total = data["total_calls"]

        return BillingRecord(
            client_id=client_id,
            period_start=data["period_start"],
            period_end=datetime.now().isoformat(),
            total_calls=total,
            cost_per_call_usd=rate,
            total_billed_usd=round(total * rate, 2),
            breakdown_by_domain=data["calls_by_domain"].copy(),
        )

    def list_clients(self) -> List[str]:
        return list(self._usage.keys())