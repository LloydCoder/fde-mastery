"""Tenant-isolated custom agent registry."""
from __future__ import annotations

from .agent import CustomAgent


class CustomAgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[tuple[str, str], CustomAgent] = {}

    def register(self, agent: CustomAgent) -> None:
        self._agents[(agent.spec.tenant_id, agent.spec.name)] = agent

    def get(self, tenant_id: str, name: str) -> CustomAgent:
        try:
            return self._agents[(tenant_id, name)]
        except KeyError as exc:
            raise KeyError(f"custom agent not registered for tenant: {name}") from exc

    def list(self, tenant_id: str) -> list[str]:
        return sorted(name for owner, name in self._agents if owner == tenant_id)
