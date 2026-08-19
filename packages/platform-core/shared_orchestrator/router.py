"""Multi-agent router with per-domain resilience isolation."""

from typing import Any, Dict

try:
    from ..config import settings
    from ..schemas import Domain
except ImportError:
    from config import settings
    from schemas import Domain

from .resilience import ResilienceConfig, ResilienceExecutor


_DOMAIN_SOURCES = {
    Domain.CYBERSECURITY: "domains/cybersecurity (legacy month-1 implementation)",
    Domain.FINANCE: "domains/finance (legacy month-2 implementation)",
    Domain.HEALTHTECH: "domains/healthtech (legacy month-3 implementation)",
    Domain.LOGISTICS: "domains/logistics (legacy month-4 implementation)",
    Domain.LEGAL: "domains/legal (legacy month-5 implementation)",
    Domain.REVOPS: "domains/revops (legacy month-6 implementation)",
    Domain.PROCUREMENT: "domains/procurement",
}


class AgentRouter:
    """Routes requests while isolating failures and capacity per domain."""

    def __init__(self, resilience_config: ResilienceConfig | None = None):
        self._agents: Dict[Domain, Any] = {}
        self._resilience: Dict[Domain, ResilienceExecutor] = {}
        self._resilience_config = resilience_config or ResilienceConfig(
            timeout_seconds=settings.agent_timeout_seconds,
            max_retries=settings.agent_max_retries,
            backoff_seconds=settings.agent_backoff_seconds,
            max_backoff_seconds=settings.agent_max_backoff_seconds,
            circuit_failure_threshold=settings.agent_circuit_failure_threshold,
            circuit_recovery_seconds=settings.agent_circuit_recovery_seconds,
            max_concurrency=settings.agent_max_concurrency,
        )

    def register_agent(self, domain: Domain, agent_instance: Any) -> None:
        if not isinstance(domain, Domain):
            raise TypeError("domain must be a Domain enum value")
        if not hasattr(agent_instance, "evaluate"):
            raise TypeError(f"Agent for {domain} must expose evaluate(payload)")
        old = self._resilience.pop(domain, None)
        if old:
            old.close()
        self._agents[domain] = agent_instance
        self._resilience[domain] = ResilienceExecutor(self._resilience_config)

    def register_defaults(self) -> None:
        """Register all seven production domain adapters."""
        from .adapters import (
            CybersecurityDomainAdapter,
            FinanceDomainAdapter,
            HealthTechDomainAdapter,
            LegalDomainAdapter,
            LogisticsDomainAdapter,
            ProcurementDomainAdapter,
            RevOpsDomainAdapter,
        )
        self.register_agent(Domain.CYBERSECURITY, CybersecurityDomainAdapter())
        self.register_agent(Domain.FINANCE, FinanceDomainAdapter())
        self.register_agent(Domain.HEALTHTECH, HealthTechDomainAdapter())
        self.register_agent(Domain.LOGISTICS, LogisticsDomainAdapter())
        self.register_agent(Domain.LEGAL, LegalDomainAdapter())
        self.register_agent(Domain.REVOPS, RevOpsDomainAdapter())
        self.register_agent(Domain.PROCUREMENT, ProcurementDomainAdapter())

    @staticmethod
    def _retryable(exc: Exception) -> bool:
        return isinstance(exc, (ConnectionError, TimeoutError, OSError))

    def route(self, domain: Domain, payload: Dict[str, Any]) -> Any:
        if not isinstance(domain, Domain):
            raise TypeError("domain must be a Domain enum value")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dictionary")
        if domain not in self._agents:
            raise ValueError(f"No agent registered for domain: {domain.value}")
        return self._resilience[domain].execute(
            lambda: self._agents[domain].evaluate(payload),
            retryable=self._retryable,
        )

    def health(self) -> Dict[str, Any]:
        return {
            domain.value: {
                "agent": agent.health() if hasattr(agent, "health") else {"status": "unknown"},
                "resilience": self._resilience[domain].health(),
            }
            for domain, agent in self._agents.items()
        }

    def capabilities(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for domain, agent in self._agents.items():
            capabilities = dict(agent.capabilities()) if hasattr(agent, "capabilities") else {}
            capabilities.setdefault("domain", domain.value)
            capabilities.setdefault("source", _DOMAIN_SOURCES[domain])
            result[domain.value] = capabilities
        return result

    def list_domains(self) -> list:
        return [d.value for d in self._agents.keys()]

    def close(self) -> None:
        for executor in self._resilience.values():
            executor.close()
