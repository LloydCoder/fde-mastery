from schemas import Domain
from shared_orchestrator.router import AgentRouter


def test_all_domain_agents_register_through_platform_router(monkeypatch):
    monkeypatch.setenv("FDE_MONTH1_PROVIDER", "mock")
    router = AgentRouter()
    try:
        router.register_defaults()
        assert set(router.list_domains()) == {domain.value for domain in Domain}
        health = router.health()
        capabilities = router.capabilities()
        assert all(health[domain.value]["agent"]["status"] == "ready" for domain in Domain)
        assert all(capabilities[domain.value]["domain"] == domain.value for domain in Domain)
        assert capabilities[Domain.PROCUREMENT.value]["source"] == "domains/procurement"
        assert capabilities[Domain.CYBERSECURITY.value]["source"].startswith("domains/")
    finally:
        router.close()
