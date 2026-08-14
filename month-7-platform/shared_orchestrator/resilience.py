"""Bounded resilience primitives for domain-agent execution."""

from __future__ import annotations

import random
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, TypeVar

T = TypeVar("T")

@dataclass(frozen=True)
class ResilienceConfig:
    timeout_seconds: float = 30.0
    max_retries: int = 2
    backoff_seconds: float = 0.25
    max_backoff_seconds: float = 2.0
    circuit_failure_threshold: int = 5
    circuit_recovery_seconds: float = 30.0
    max_concurrency: int = 32

class AgentTimeoutError(TimeoutError):
    """Raised when an agent exceeds the platform execution deadline."""

class CircuitOpenError(RuntimeError):
    """Raised when execution is blocked by an open circuit."""

class ResilienceExecutor:
    """Execute an agent call with bounded timeout, retries and circuit control."""

    def __init__(self, config: Optional[ResilienceConfig] = None) -> None:
        self.config = config or ResilienceConfig()
        if self.config.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.config.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if self.config.circuit_failure_threshold < 1:
            raise ValueError("circuit_failure_threshold must be positive")
        if self.config.max_concurrency < 1:
            raise ValueError("max_concurrency must be positive")
        self._semaphore = threading.BoundedSemaphore(self.config.max_concurrency)
        self._lock = threading.Lock()
        self._failures = 0
        self._opened_at: Optional[float] = None
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_concurrency)

    def _circuit_allows(self) -> bool:
        with self._lock:
            if self._opened_at is None:
                return True
            if time.monotonic() - self._opened_at >= self.config.circuit_recovery_seconds:
                self._opened_at = None
                self._failures = 0
                return True
            return False

    def _record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None

    def _record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.config.circuit_failure_threshold:
                self._opened_at = time.monotonic()

    def _release_when_done(self, future: Future[Any]) -> None:
        try:
            future.result()
        except Exception:
            pass
        finally:
            self._semaphore.release()

    def execute(self, operation: Callable[[], T], *, retryable: Callable[[Exception], bool]) -> T:
        if not self._circuit_allows():
            raise CircuitOpenError("Agent circuit is open; execution temporarily blocked")
        if not self._semaphore.acquire(timeout=self.config.timeout_seconds):
            raise AgentTimeoutError("Agent concurrency capacity is exhausted")

        released = False
        try:
            attempts = self.config.max_retries + 1
            for attempt in range(attempts):
                future = self._executor.submit(operation)
                try:
                    result = future.result(timeout=self.config.timeout_seconds)
                    self._record_success()
                    self._semaphore.release()
                    released = True
                    return result
                except FutureTimeoutError as exc:
                    future.add_done_callback(self._release_when_done)
                    released = True
                    self._record_failure()
                    raise AgentTimeoutError("Agent execution exceeded the configured timeout") from exc
                except Exception as exc:
                    self._record_failure()
                    if attempt >= attempts - 1 or not retryable(exc):
                        self._semaphore.release()
                        released = True
                        raise
                    delay = min(self.config.backoff_seconds * (2**attempt), self.config.max_backoff_seconds)
                    time.sleep(delay * random.uniform(0.5, 1.5))
            raise RuntimeError("Unreachable resilience state")
        finally:
            if not released:
                self._semaphore.release()

    def health(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "circuit": "open" if self._opened_at is not None else "closed",
                "failures": self._failures,
                "max_concurrency": self.config.max_concurrency,
            }

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
