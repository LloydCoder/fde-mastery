"""Tenant-aware AI cost accounting and budget guardrails."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from threading import Lock


@dataclass(frozen=True)
class CostRecord:
    tenant_id: str
    run_id: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if not self.tenant_id or not self.run_id or not self.model:
            raise ValueError("tenant_id, run_id and model are required")
        if self.input_tokens < 0 or self.output_tokens < 0 or self.cost_usd < 0:
            raise ValueError("cost and token counts must be non-negative")


@dataclass(frozen=True)
class CostBudget:
    tenant_id: str
    limit_usd: Decimal

    def __post_init__(self) -> None:
        if not self.tenant_id or self.limit_usd < 0:
            raise ValueError("tenant_id is required and budget must be non-negative")


class CostLedger:
    """Thread-safe reference ledger; production adapters persist records transactionally."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._spent: dict[str, Decimal] = {}

    def record(self, record: CostRecord, budget: CostBudget | None = None) -> Decimal:
        if budget is not None and budget.tenant_id != record.tenant_id:
            raise ValueError("budget tenant must match cost record tenant")
        with self._lock:
            current = self._spent.get(record.tenant_id, Decimal("0"))
            updated = current + record.cost_usd
            if budget is not None and updated > budget.limit_usd:
                raise BudgetExceeded(record.tenant_id, budget.limit_usd, updated)
            self._spent[record.tenant_id] = updated
            return updated

    def spent(self, tenant_id: str) -> Decimal:
        with self._lock:
            return self._spent.get(tenant_id, Decimal("0"))


class BudgetExceeded(RuntimeError):
    """Raised before a cost record would cross an enforced budget."""

    def __init__(self, tenant_id: str, limit: Decimal, attempted: Decimal) -> None:
        super().__init__(f"tenant {tenant_id!r} budget exceeded: {attempted} > {limit}")
        self.tenant_id = tenant_id
        self.limit = limit
        self.attempted = attempted
