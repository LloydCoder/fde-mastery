"""Provider-neutral contract for customer-system integrations.

Concrete connectors must implement this boundary; no provider credentials or customer data
belong in the repository. The same contract supports SIEM, ERP, EHR, TMS, DMS and CRM systems.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class IntegrationHealth:
    provider: str
    reachable: bool
    authenticated: bool
    detail: str = ""


class DomainIntegration(Protocol):
    provider: str

    def health(self) -> IntegrationHealth: ...

    def ingest(self, payload: dict[str, Any], *, tenant_id: str, request_id: str) -> dict[str, Any]: ...

    def enrich(self, indicator: str, *, tenant_id: str, request_id: str) -> dict[str, Any]: ...


class DomainIntegrationRegistry:
    """Tenant-aware registry for concrete domain connectors; unknown providers fail closed."""

    def __init__(self) -> None:
        self._providers: dict[tuple[str, str], DomainIntegration] = {}

    def register(self, tenant_id: str, provider: DomainIntegration) -> None:
        if not tenant_id or not getattr(provider, "provider", ""):
            raise ValueError("tenant_id and provider name are required")
        self._providers[(tenant_id, provider.provider)] = provider

    def get(self, tenant_id: str, provider: str) -> DomainIntegration:
        try:
            return self._providers[(tenant_id, provider)]
        except KeyError as exc:
            raise LookupError("integration is not configured for this tenant") from exc


# Backward-compatible descriptive alias for callers that imported the old name.
LegacyIntegrationRegistry = DomainIntegrationRegistry
