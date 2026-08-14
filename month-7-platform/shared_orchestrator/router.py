"""Multi-agent router — routes requests to the correct domain agent."""

from typing import Any, Dict

try:
    from ..schemas import Domain
except ImportError:
    from schemas import Domain


class AgentRouter:
    """Routes incoming triage requests to the appropriate domain agent."""

    def __init__(self):
        self._agents: Dict[Domain, Any] = {}

    def register_agent(self, domain: Domain, agent_instance: Any) -> None:
        self._agents[domain] = agent_instance

    def route(self, domain: Domain, payload: Dict[str, Any]) -> Dict[str, Any]:
        if domain not in self._agents:
            raise ValueError(f"No agent registered for domain: {domain.value}")
        agent = self._agents[domain]
        return agent.evaluate(payload)

    def list_domains(self) -> list:
        return [d.value for d in self._agents.keys()]