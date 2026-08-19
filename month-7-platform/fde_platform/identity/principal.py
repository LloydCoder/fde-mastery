"""Authenticated subject model independent of any identity provider."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

from .tenant import TenantId


class PrincipalType(StrEnum):
    USER = "user"
    SERVICE = "service"
    AGENT = "agent"


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    tenant_id: TenantId
    principal_type: PrincipalType
    roles: frozenset[str] = frozenset()
    scopes: frozenset[str] = frozenset()
    claims: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise ValueError("subject is required")
        if not str(self.tenant_id).strip():
            raise ValueError("tenant_id is required")
        object.__setattr__(self, "roles", frozenset(x.strip() for x in self.roles if x.strip()))
        object.__setattr__(self, "scopes", frozenset(x.strip() for x in self.scopes if x.strip()))

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes

    def can_access_tenant(self, tenant_id: TenantId) -> bool:
        return self.tenant_id == tenant_id
