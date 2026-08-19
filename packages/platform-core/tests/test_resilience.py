import threading
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


def test_timeout_is_bounded_and_slot_remains_reserved_until_worker_finishes():
    release = threading.Event()
    executor = ResilienceExecutor(ResilienceConfig(timeout_seconds=0.02, max_retries=0, max_concurrency=1))
    try:
        with pytest.raises(AgentTimeoutError):
            executor.execute(lambda: release.wait(1), retryable=lambda exc: False)
        with pytest.raises(AgentTimeoutError):
            executor.execute(lambda: "must-not-start", retryable=lambda exc: False)
        release.set()
    finally:
        release.set()
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


def test_circuit_allows_only_one_half_open_probe_and_recovers():
    executor = ResilienceExecutor(
        ResilienceConfig(
            circuit_failure_threshold=1,
            circuit_recovery_seconds=0.02,
            max_retries=0,
            backoff_seconds=0,
        )
    )
    try:
        with pytest.raises(ValueError):
            executor.execute(lambda: (_ for _ in ()).throw(ValueError("boom")), retryable=lambda exc: False)
        time.sleep(0.03)
        assert executor.execute(lambda: "recovered", retryable=lambda exc: False) == "recovered"
        assert executor.health()["circuit"] == "closed"
    finally:
        executor.close()
