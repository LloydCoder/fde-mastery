"""Small, framework-neutral authorization layer for JWT claims."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class AuthorizationError(PermissionError):
    pass


@dataclass(frozen=True)
class Principal:
    subject: str
    tenant_id: str
    roles: frozenset[str]
    scopes: frozenset[str]

    @classmethod
    def from_claims(cls, claims: Mapping[str, Any]) -> "Principal":
        subject = str(claims.get("sub", "")).strip()
        tenant = str(claims.get("tenant_id", claims.get("org_id", ""))).strip()
        if not subject or not tenant:
            raise AuthorizationError("subject and tenant claims are required")
        roles = claims.get("roles", ())
        scopes = claims.get("scope", "")
        if isinstance(roles, str):
            roles = roles.split()
        if isinstance(scopes, str):
            scopes = scopes.split()
        return cls(subject, tenant, frozenset(str(x) for x in roles), frozenset(str(x) for x in scopes))


def require_access(principal: Principal, *, tenant_id: str, scope: str, roles: set[str] | None = None) -> None:
    if principal.tenant_id != tenant_id:
        raise AuthorizationError("cross-tenant access denied")
    if scope not in principal.scopes:
        raise AuthorizationError("required scope missing")
    if roles and not (principal.roles & roles):
        raise AuthorizationError("required role missing")
