"""Managed secrets provider contract and adapters."""
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


class AWSSecretsManagerProvider:
    def __init__(self, region: str | None = None):
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("Install the secrets extra to use AWS Secrets Manager") from exc
        self._client = boto3.client("secretsmanager", region_name=region or os.getenv("AWS_REGION"))

    def get(self, name: str) -> str:
        response = self._client.get_secret_value(SecretId=name)
        value = response.get("SecretString")
        if not value:
            raise KeyError(f"secret {name!r} has no SecretString")
        return value


class VaultProvider:
    def __init__(self, url: str | None = None, token: str | None = None):
        try:
            import hvac
        except ImportError as exc:
            raise RuntimeError("Install the secrets extra to use HashiCorp Vault") from exc
        self._client = hvac.Client(url=url or os.getenv("VAULT_ADDR"), token=token or os.getenv("VAULT_TOKEN"))
        if not self._client.is_authenticated():
            raise RuntimeError("Vault authentication failed")

    def get(self, name: str) -> str:
        mount, _, path = name.partition(":")
        if not path:
            mount, path = "secret", mount
        response = self._client.secrets.kv.v2.read_secret_version(mount_point=mount, path=path)
        data = response.get("data", {}).get("data", {})
        value = data.get("value")
        if not value:
            raise KeyError(f"secret {name!r} is missing value")
        return str(value)


class FailClosedSecretsProvider:
    def get(self, name: str) -> str:
        raise RuntimeError(f"No managed secrets provider configured for {name!r}")


def build_secrets_provider() -> SecretsProvider:
    backend = os.getenv("FDE_SECRETS_BACKEND", "managed").lower()
    if backend == "environment" and os.getenv("FDE_ENVIRONMENT", "development") != "production":
        return EnvironmentSecretsProvider()
    if backend == "aws":
        return AWSSecretsManagerProvider()
    if backend == "vault":
        return VaultProvider()
    if backend == "managed":
        return FailClosedSecretsProvider()
    raise ValueError("FDE_SECRETS_BACKEND must be managed, aws, vault, or environment")
