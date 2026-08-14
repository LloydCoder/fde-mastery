import pytest

from schemas import Domain
from shared_orchestrator.domain_agent import DomainAgentResult
from shared_orchestrator.router import AgentRouter


@pytest.mark.parametrize("domain", list(Domain))
def test_router_executes_registered_domain_adapter(domain):
    router = AgentRouter()
    try:
        router.register_defaults()
        payload = {}
        result = router.route(domain, payload)
        assert isinstance(result, DomainAgentResult)
        assert result.domain == domain
        assert isinstance(result.result, dict)
        assert 0.0 <= result.confidence <= 1.0
        assert "adapter" in result.audit_metadata
    finally:
        router.close()


def test_router_rejects_unknown_domain():
    router = AgentRouter()
    try:
        with pytest.raises(ValueError, match="No agent registered"):
            router.route(Domain.CYBERSECURITY, {})
    finally:
        router.close()
