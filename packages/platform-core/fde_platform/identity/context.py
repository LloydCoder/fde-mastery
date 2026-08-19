"""Immutable request security context propagated across platform boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from .principal import Principal
from .tenant import Environment, TenantRef


@dataclass(frozen=True, slots=True)
class RequestContext:
    principal: Principal
    tenant: TenantRef
    request_id: str
    environment: Environment

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id is required")
        if self.principal.tenant_id != self.tenant.tenant_id:
            raise ValueError("principal tenant does not match request tenant")
        if self.environment != self.tenant.environment:
            raise ValueError("request environment does not match tenant environment")

    @property
    def tenant_id(self):
        return self.tenant.tenant_id

    def require_same_tenant(self, tenant_id: str) -> None:
        if str(self.tenant_id) != tenant_id:
            raise PermissionError("cross-tenant access denied")
