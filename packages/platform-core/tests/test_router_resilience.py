import time

import pytest

from schemas import Domain
from shared_orchestrator.resilience import CircuitOpenError, ResilienceConfig
from shared_orchestrator.router import AgentRouter


class FakeAgent:
    def __init__(self, fail=False):
        self.fail = fail

    def evaluate(self, payload):
        if self.fail:
            raise ConnectionError("temporary provider failure")
        return {"result": payload, "confidence": 1.0}

    def health(self):
        return {"status": "healthy"}

    def capabilities(self):
        return {"test": True}


def test_domain_circuit_isolation():
    router = AgentRouter(ResilienceConfig(circuit_failure_threshold=1, max_retries=0, backoff_seconds=0))
    failing = FakeAgent(fail=True)
    healthy = FakeAgent()
    router.register_agent(Domain.CYBERSECURITY, failing)
    router.register_agent(Domain.FINANCE, healthy)
    try:
        with pytest.raises(ConnectionError):
            router.route(Domain.CYBERSECURITY, {})
        with pytest.raises(CircuitOpenError):
            router.route(Domain.CYBERSECURITY, {})
        assert router.route(Domain.FINANCE, {"ok": True})["result"]["ok"] is True
        assert router.health()["cybersecurity"]["resilience"]["circuit"] == "open"
        assert router.health()["finance"]["resilience"]["circuit"] == "closed"
    finally:
        router.close()


def test_circuit_recovers_after_cooldown():
    router = AgentRouter(ResilienceConfig(circuit_failure_threshold=1, circuit_recovery_seconds=0.01, max_retries=0, backoff_seconds=0))
    agent = FakeAgent(fail=True)
    router.register_agent(Domain.CYBERSECURITY, agent)
    try:
        with pytest.raises(ConnectionError):
            router.route(Domain.CYBERSECURITY, {})
        time.sleep(0.02)
        agent.fail = False
        assert router.route(Domain.CYBERSECURITY, {})["confidence"] == 1.0
    finally:
        router.close()
