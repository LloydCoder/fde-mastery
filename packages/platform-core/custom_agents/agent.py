"""Tenant-scoped custom-agent contract."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping


@dataclass(frozen=True)
class CustomAgentSpec:
    name: str
    version: str
    tenant_id: str
    tool_allowlist: tuple[str, ...] = ()
    require_human_approval_for: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


class CustomAgent:
    """Customer extension point constrained by tenant and tool policy."""
    def __init__(self, spec: CustomAgentSpec, handler: Callable[[dict[str, Any]], Any]) -> None:
        if not spec.name or not spec.tenant_id:
            raise ValueError("custom agent name and tenant_id are required")
        self.spec = spec
        self._handler = handler

    def evaluate(self, payload: dict[str, Any]) -> Any:
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dictionary")
        return self._handler(payload)

    def capabilities(self) -> dict[str, Any]:
        return {"custom": True, "tenant_scoped": True, "tool_allowlist": list(self.spec.tool_allowlist), "human_approval_actions": list(self.spec.require_human_approval_for)}
