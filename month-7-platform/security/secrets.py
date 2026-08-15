"""Secrets provider contract with explicit production backends.

The application depends on this interface rather than reading provider secrets
from arbitrary environment variables. Deployments can bind AWS Secrets Manager,
HashiCorp Vault, or another approved implementation at startup.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


class SecretsProvider(Protocol):
    def get(self, name: str) -> str: ...


@dataclass(frozen=True)
class EnvironmentSecretsProvider:
    prefix: str = "FDE_SECRET_"

    def get(self, name: str) -> str:
        value = os.getenv(f"{self.prefix}{name}")
        if not value:
            raise KeyError(f"secret {name!r} is not configured")
        return value


class FailClosedSecretsProvider:
    """Production-safe placeholder until a managed provider is injected."""

    def get(self, name: str) -> str:
        raise RuntimeError(f"No managed secrets provider configured for {name!r}")


def build_secrets_provider() -> SecretsProvider:
    backend = os.getenv("FDE_SECRETS_BACKEND", "managed").lower()
    if backend == "environment" and os.getenv("FDE_ENVIRONMENT", "development") != "production":
        return EnvironmentSecretsProvider()
    if backend != "managed":
        raise ValueError("FDE_SECRETS_BACKEND must be managed or environment")
    return FailClosedSecretsProvider()
