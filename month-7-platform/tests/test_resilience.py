import time

import pytest

from shared_orchestrator.resilience import (
    AgentTimeoutError,
    CircuitOpenError,
    ResilienceConfig,
    ResilienceExecutor,
)


def test_retries_transient_failure_then_succeeds():
    attempts = 0

    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("temporary")
        return "ok"

    executor = ResilienceExecutor(ResilienceConfig(max_retries=2, backoff_seconds=0))
    try:
        assert executor.execute(operation, retryable=lambda exc: isinstance(exc, ConnectionError)) == "ok"
        assert attempts == 3
    finally:
        executor.close()


def test_does_not_retry_non_retryable_failure():
    attempts = 0

    def operation():
        nonlocal attempts
        attempts += 1
        raise ValueError("invalid request")

    executor = ResilienceExecutor(ResilienceConfig(max_retries=3, backoff_seconds=0))
    try:
        with pytest.raises(ValueError):
            executor.execute(operation, retryable=lambda exc: isinstance(exc, ConnectionError))
        assert attempts == 1
    finally:
        executor.close()


def test_timeout_is_bounded():
    executor = ResilienceExecutor(ResilienceConfig(timeout_seconds=0.02, max_retries=0))
    try:
        started = time.monotonic()
        with pytest.raises(AgentTimeoutError):
            executor.execute(lambda: time.sleep(1), retryable=lambda exc: False)
        assert time.monotonic() - started < 0.2
    finally:
        executor.close()


def test_circuit_opens_after_threshold():
    executor = ResilienceExecutor(
        ResilienceConfig(circuit_failure_threshold=2, max_retries=0, backoff_seconds=0)
    )
    try:
        for _ in range(2):
            with pytest.raises(ValueError):
                executor.execute(lambda: (_ for _ in ()).throw(ValueError("boom")), retryable=lambda exc: False)
        with pytest.raises(CircuitOpenError):
            executor.execute(lambda: "blocked", retryable=lambda exc: False)
        assert executor.health()["circuit"] == "open"
    finally:
        executor.close()
