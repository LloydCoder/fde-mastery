"""Multi-agent router — routes requests to the correct domain agent."""

from typing import Any, Dict

try:
    from ..schemas import Domain
except ImportError:
    from schemas import Domain


class AgentRouter:
    """Routes incoming platform requests to registered domain agents.

    The router owns registration and dispatch only. Domain-specific behavior
    lives behind the shared DomainAgent adapter contract.
    """

    def __init__(self):
        self._agents: Dict[Domain, Any] = {}

    def register_agent(self, domain: Domain, agent_instance: Any) -> None:
        if not hasattr(agent_instance, "evaluate"):
            raise TypeError(f"Agent for {domain.value} must expose evaluate(payload)")
        self._agents[domain] = agent_instance

    def register_defaults(self) -> None:
        """Register all six Month 1-6 domain adapters."""
        from .adapters import (
            CybersecurityDomainAdapter,
            FinanceDomainAdapter,
            HealthTechDomainAdapter,
            LegalDomainAdapter,
            LogisticsDomainAdapter,
            RevOpsDomainAdapter,
        )

        self.register_agent(Domain.CYBERSECURITY, CybersecurityDomainAdapter())
        self.register_agent(Domain.FINANCE, FinanceDomainAdapter())
        self.register_agent(Domain.HEALTHTECH, HealthTechDomainAdapter())
        self.register_agent(Domain.LOGISTICS, LogisticsDomainAdapter())
        self.register_agent(Domain.LEGAL, LegalDomainAdapter())
        self.register_agent(Domain.REVOPS, RevOpsDomainAdapter())

    def route(self, domain: Domain, payload: Dict[str, Any]) -> Any:
        if domain not in self._agents:
            raise ValueError(f"No agent registered for domain: {domain.value}")
        return self._agents[domain].evaluate(payload)

    def health(self) -> Dict[str, Any]:
        return {
            domain.value: agent.health() if hasattr(agent, "health") else {"status": "unknown"}
            for domain, agent in self._agents.items()
        }

    def capabilities(self) -> Dict[str, Any]:
        return {
            domain.value: agent.capabilities()
            if hasattr(agent, "capabilities")
            else {}
            for domain, agent in self._agents.items()
        }

    def list_domains(self) -> list:
        return [d.value for d in self._agents.keys()]
