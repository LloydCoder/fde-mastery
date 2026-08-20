"""Tenant-aware AI execution cost accounting."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CostRecord:
    tenant_id: str
    agent_id: str
    workflow_id: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    tool_cost: Decimal = Decimal("0")
    compute_cost: Decimal = Decimal("0")

    @property
    def total(self) -> Decimal:
        return self.tool_cost + self.compute_cost

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.tenant_id, self.agent_id, self.workflow_id, self.model)):
            raise ValueError("cost dimensions are required")
        if min(self.input_tokens, self.output_tokens) < 0:
            raise ValueError("token counts cannot be negative")


class CostTracker:
    def __init__(self, tenant_budgets: dict[str, Decimal] | None = None) -> None:
        self._records: list[CostRecord] = []
        self._budgets = tenant_budgets or {}

    def record(self, item: CostRecord) -> None:
        projected = self.total_for_tenant(item.tenant_id) + item.total
        budget = self._budgets.get(item.tenant_id)
        if budget is not None and projected > budget:
            raise PermissionError("tenant AI cost budget exceeded")
        self._records.append(item)

    def total_for_tenant(self, tenant_id: str) -> Decimal:
        return sum((item.total for item in self._records if item.tenant_id == tenant_id), Decimal("0"))

    def records(self) -> tuple[CostRecord, ...]:
        return tuple(self._records)
