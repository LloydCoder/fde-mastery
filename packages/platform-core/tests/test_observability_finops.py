from decimal import Decimal

import pytest

from fde_platform.observability import CostBudget, CostLedger, CostRecord, MetricPoint, Observation
from fde_platform.observability.budget import BudgetExceeded


def test_observation_requires_timezone_aware_timestamp() -> None:
    from datetime import datetime

    with pytest.raises(ValueError):
        Observation("agent.run", timestamp=datetime(2026, 1, 1))


def test_metric_points_bound_dimensions() -> None:
    with pytest.raises(ValueError):
        MetricPoint("gen_ai.client.token.usage", 1, {str(i): "x" for i in range(21)})


def test_cost_ledger_is_tenant_scoped_and_budgeted() -> None:
    ledger = CostLedger()
    budget = CostBudget("tenant-a", Decimal("1.00"))
    ledger.record(CostRecord("tenant-a", "run-1", "model-a", cost_usd=Decimal("0.60")), budget)
    assert ledger.spent("tenant-a") == Decimal("0.60")
    assert ledger.spent("tenant-b") == Decimal("0")

    with pytest.raises(BudgetExceeded):
        ledger.record(CostRecord("tenant-a", "run-2", "model-a", cost_usd=Decimal("0.41")), budget)


def test_budget_cannot_be_used_across_tenants() -> None:
    ledger = CostLedger()
    with pytest.raises(ValueError):
        ledger.record(
            CostRecord("tenant-a", "run-1", "model-a", cost_usd=Decimal("0.10")),
            CostBudget("tenant-b", Decimal("1.00")),
        )
