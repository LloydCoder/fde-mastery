"""Enterprise integration control-plane contracts.

The control plane stores connector metadata and references to managed credentials; it never
stores credential material. Runtime side effects remain behind the existing Tool Gateway.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping


class AuthMethod(StrEnum):
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    HMAC = "hmac"
    MTLS = "mtls"
    NONE = "none"


class IntegrationStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DEGRADED = "degraded"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class CredentialReference:
    """Opaque reference to a managed secret; the secret value must never enter this object."""

    name: str
    version: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("credential reference name is required")
        if any(token in self.name.lower() for token in ("secret=", "token=", "password=", "api_key=")):
            raise ValueError("credential reference must not contain credential material")


@dataclass(frozen=True, slots=True)
class IntegrationDefinition:
    provider: str
    version: str
    auth_method: AuthMethod
    capabilities: frozenset[str] = field(default_factory=frozenset)
    allowed_hosts: frozenset[str] = field(default_factory=frozenset)
    webhook_events: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.provider.strip() or not self.version.strip():
            raise ValueError("provider and version are required")
        if any(not host.strip() for host in self.allowed_hosts):
            raise ValueError("allowed hosts cannot be blank")


@dataclass(frozen=True, slots=True)
class IntegrationBinding:
    tenant_id: str
    environment: str
    integration_id: str
    definition: IntegrationDefinition
    credential: CredentialReference | None = None
    config: Mapping[str, str] = field(default_factory=dict)
    status: IntegrationStatus = IntegrationStatus.ACTIVE

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.environment.strip() or not self.integration_id.strip():
            raise ValueError("tenant, environment and integration id are required")
        if self.definition.auth_method is not AuthMethod.NONE and self.credential is None:
            raise ValueError("authenticated integrations require a managed credential reference")


class IntegrationRegistry:
    """Fail-closed tenant/environment registry for integration bindings."""

    def __init__(self) -> None:
        self._bindings: dict[tuple[str, str, str], IntegrationBinding] = {}

    def register(self, binding: IntegrationBinding) -> None:
        key = (binding.tenant_id, binding.environment, binding.integration_id)
        if key in self._bindings:
            raise ValueError("integration binding already exists")
        self._bindings[key] = binding

    def get(self, tenant_id: str, environment: str, integration_id: str) -> IntegrationBinding:
        binding = self._bindings.get((tenant_id, environment, integration_id))
        if binding is None:
            raise LookupError("integration is not configured for this tenant and environment")
        if binding.status is not IntegrationStatus.ACTIVE:
            raise PermissionError("integration is not active")
        return binding

    def disable(self, tenant_id: str, environment: str, integration_id: str) -> None:
        key = (tenant_id, environment, integration_id)
        binding = self._bindings.get(key)
        if binding is None:
            raise LookupError("integration is not configured")
        self._bindings[key] = IntegrationBinding(
            tenant_id=binding.tenant_id,
            environment=binding.environment,
            integration_id=binding.integration_id,
            definition=binding.definition,
            credential=binding.credential,
            config=binding.config,
            status=IntegrationStatus.DISABLED,
        )
