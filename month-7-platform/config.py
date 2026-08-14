"""Validated runtime configuration for the Month 7 platform."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _positive_float(name: str, default: float) -> float:
    value = float(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _non_negative_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


@dataclass(frozen=True)
class Settings:
    version: str = os.getenv("FDE_PLATFORM_VERSION", "0.9.0")
    storage_backend: str = os.getenv("FDE_STORAGE_BACKEND", "memory").lower()
    rate_limit_backend: str = os.getenv("FDE_RATE_LIMIT_BACKEND", "memory").lower()
    database_url: str | None = os.getenv("FDE_DATABASE_URL")
    redis_url: str | None = os.getenv("FDE_REDIS_URL")
    environment: str = os.getenv("FDE_ENVIRONMENT", "development").lower()
    mock_llm: bool = os.getenv("MOCK_LLM", "false").lower() in {"1", "true", "yes"}
    cors_origins: tuple[str, ...] = tuple(item.strip() for item in os.getenv("FDE_CORS_ORIGINS", "").split(",") if item.strip())
    agent_timeout_seconds: float = _positive_float("FDE_AGENT_TIMEOUT_SECONDS", 30.0)
    agent_max_retries: int = _non_negative_int("FDE_AGENT_MAX_RETRIES", 2)
    agent_backoff_seconds: float = _positive_float("FDE_AGENT_BACKOFF_SECONDS", 0.25)
    agent_max_backoff_seconds: float = _positive_float("FDE_AGENT_MAX_BACKOFF_SECONDS", 2.0)
    agent_circuit_failure_threshold: int = max(1, _non_negative_int("FDE_AGENT_CIRCUIT_FAILURE_THRESHOLD", 5))
    agent_circuit_recovery_seconds: float = _positive_float("FDE_AGENT_CIRCUIT_RECOVERY_SECONDS", 30.0)
    agent_max_concurrency: int = max(1, _non_negative_int("FDE_AGENT_MAX_CONCURRENCY", 32))

    def validate(self) -> None:
        if self.storage_backend not in {"memory", "postgres"}:
            raise ValueError("FDE_STORAGE_BACKEND must be memory or postgres")
        if self.rate_limit_backend not in {"memory", "redis"}:
            raise ValueError("FDE_RATE_LIMIT_BACKEND must be memory or redis")
        if self.environment == "production" and self.storage_backend == "memory":
            raise ValueError("Production deployments must use persistent storage")
        if self.environment == "production" and self.rate_limit_backend == "memory":
            raise ValueError("Production deployments must use distributed rate limiting")


settings = Settings()
settings.validate()
