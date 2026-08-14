"""Multi-agent router with per-domain resilience isolation."""

from typing import Any, Dict

try:
    from ..schemas import Domain
except ImportError:
    from schemas import Domain

from .resilience import ResilienceConfig, ResilienceExecutor


class AgentRouter:
    """Routes requests while isolating failures and capacity per domain."""

    def __init__(self, resilience_config: ResilienceConfig | None = None):
        self._agents: Dict[Domain, Any] = {}
        self._resilience: Dict[Domain, ResilienceExecutor] = {}
        self._resilience_config = resilience_config or ResilienceConfig()

    def register_agent(self, domain: Domain, agent_instance: Any) -> None:
        if not hasattr(agent_instance, "evaluate"):
            raise TypeError(f"Agent for {domain.value} must expose evaluate(payload)")
        old = self._resilience.pop(domain, None)
        if old:
            old.close()
        self._agents[domain] = agent_instance
        self._resilience[domain] = ResilienceExecutor(self._resilience_config)

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

    @staticmethod
    def _retryable(exc: Exception) -> bool:
        return isinstance(exc, (ConnectionError, TimeoutError, OSError))

    def route(self, domain: Domain, payload: Dict[str, Any]) -> Any:
        if domain not in self._agents:
            raise ValueError(f"No agent registered for domain: {domain.value}")
        executor = self._resilience[domain]
        return executor.execute(
            lambda: self._agents[domain].evaluate(payload),
            retryable=self._retryable,
        )

    def health(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for domain, agent in self._agents.items():
            result[domain.value] = {
                "agent": agent.health() if hasattr(agent, "health") else {"status": "unknown"},
                "resilience": self._resilience[domain].health(),
            }
        return result

    def capabilities(self) -> Dict[str, Any]:
        return {
            domain.value: agent.capabilities() if hasattr(agent, "capabilities") else {}
            for domain, agent in self._agents.items()
        }

    def list_domains(self) -> list:
        return [d.value for d in self._agents.keys()]

    def close(self) -> None:
        for executor in self._resilience.values():
            executor.close()
