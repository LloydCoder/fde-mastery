import pytest

from shared_orchestrator.resilience import CircuitOpenError, ResilienceConfig, ResilienceExecutor


def test_timeout_and_failure_recovery_isolated_per_executor():
    executor = ResilienceExecutor(ResilienceConfig(timeout_seconds=0.05, max_retries=0, circuit_failure_threshold=1, circuit_recovery_seconds=60))
    try:
        with pytest.raises(Exception):
            executor.execute(lambda: (_ for _ in ()).throw(ConnectionError("provider down")))
        with pytest.raises(CircuitOpenError):
            executor.execute(lambda: {"ok": True})
        assert executor.health()["circuit"] == "open"
    finally:
        executor.close()
