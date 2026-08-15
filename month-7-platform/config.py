"""Validated runtime configuration for the Month 7 platform."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


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


def _csv(name: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in os.getenv(name, "").split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    version: str = field(default_factory=lambda: os.getenv("FDE_PLATFORM_VERSION", "1.1.0"))
    storage_backend: str = field(default_factory=lambda: os.getenv("FDE_STORAGE_BACKEND", "memory").lower())
    rate_limit_backend: str = field(default_factory=lambda: os.getenv("FDE_RATE_LIMIT_BACKEND", "memory").lower())
    database_url: str | None = field(default_factory=lambda: os.getenv("FDE_DATABASE_URL"))
    redis_url: str | None = field(default_factory=lambda: os.getenv("FDE_REDIS_URL"))
    environment: str = field(default_factory=lambda: os.getenv("FDE_ENVIRONMENT", "development").lower())
    mock_llm: bool = field(default_factory=lambda: os.getenv("MOCK_LLM", "false").lower() in {"1", "true", "yes"})
    secrets_backend: str = field(default_factory=lambda: os.getenv("FDE_SECRETS_BACKEND", "managed").lower())
    oidc_issuer: str | None = field(default_factory=lambda: os.getenv("FDE_OIDC_ISSUER"))
    oidc_audience: str | None = field(default_factory=lambda: os.getenv("FDE_OIDC_AUDIENCE"))
    cors_origins: tuple[str, ...] = field(default_factory=lambda: _csv("FDE_CORS_ORIGINS"))
    agent_timeout_seconds: float = field(default_factory=lambda: _positive_float("FDE_AGENT_TIMEOUT_SECONDS", 30.0))
    agent_max_retries: int = field(default_factory=lambda: _non_negative_int("FDE_AGENT_MAX_RETRIES", 2))
    agent_backoff_seconds: float = field(default_factory=lambda: _positive_float("FDE_AGENT_BACKOFF_SECONDS", 0.25))
    agent_max_backoff_seconds: float = field(default_factory=lambda: _positive_float("FDE_AGENT_MAX_BACKOFF_SECONDS", 2.0))
    agent_circuit_failure_threshold: int = field(default_factory=lambda: max(1, _non_negative_int("FDE_AGENT_CIRCUIT_FAILURE_THRESHOLD", 5)))
    agent_circuit_recovery_seconds: float = field(default_factory=lambda: _positive_float("FDE_AGENT_CIRCUIT_RECOVERY_SECONDS", 30.0))
    agent_max_concurrency: int = field(default_factory=lambda: max(1, _non_negative_int("FDE_AGENT_MAX_CONCURRENCY", 32)))

    def validate(self) -> None:
        if self.storage_backend not in {"memory", "postgres"}:
            raise ValueError("FDE_STORAGE_BACKEND must be memory or postgres")
        if self.rate_limit_backend not in {"memory", "redis"}:
            raise ValueError("FDE_RATE_LIMIT_BACKEND must be memory or redis")
        if self.secrets_backend not in {"managed", "environment"}:
            raise ValueError("FDE_SECRETS_BACKEND must be managed or environment")
        if self.environment == "production" and self.storage_backend != "postgres":
            raise ValueError("Production deployments must use persistent PostgreSQL storage")
        if self.environment == "production" and self.rate_limit_backend != "redis":
            raise ValueError("Production deployments must use distributed Redis rate limiting")
        if self.environment == "production" and self.secrets_backend != "managed":
            raise ValueError("Production deployments must use a managed secrets provider")
        if self.environment == "production" and (not self.oidc_issuer or not self.oidc_audience):
            raise ValueError("Production deployments require FDE_OIDC_ISSUER and FDE_OIDC_AUDIENCE")
        if self.storage_backend == "postgres" and not self.database_url:
            raise ValueError("FDE_DATABASE_URL is required when PostgreSQL storage is enabled")
        if self.rate_limit_backend == "redis" and not self.redis_url:
            raise ValueError("FDE_REDIS_URL is required when Redis rate limiting is enabled")
        if self.environment == "production" and self.mock_llm:
            raise ValueError("MOCK_LLM must be disabled in production")


settings = Settings()
settings.validate()
