from __future__ import annotations

import pytest

from fde_platform.authorization import (
    AuthorizationDecision,
    AuthorizationRequest,
    DefaultAuthorizationService,
)
from fde_platform.identity import Environment, Principal, PrincipalType, RequestContext, TenantId, TenantRef


def context(tenant: str = "acme", *, roles: frozenset[str] = frozenset({"operator"})) -> RequestContext:
    tenant_ref = TenantRef(TenantId(tenant), Environment.PRODUCTION)
    principal = Principal(
        subject="user-1",
        tenant_id=TenantId(tenant),
        principal_type=PrincipalType.USER,
        roles=roles,
        scopes=frozenset({"agent:read"}),
        claims={"iss": "https://issuer.example"},
    )
    return RequestContext(principal, tenant_ref, "req-123", Environment.PRODUCTION)


def test_context_requires_matching_principal_tenant() -> None:
    tenant = TenantRef(TenantId("acme"), Environment.PRODUCTION)
    principal = Principal("u1", TenantId("other"), PrincipalType.USER)
    with pytest.raises(ValueError, match="does not match"):
        RequestContext(principal, tenant, "req-1", Environment.PRODUCTION)


def test_cross_tenant_authorization_is_denied() -> None:
    request = AuthorizationRequest(
        context=context("acme"),
        action="read",
        resource="agent:run:1",
        resource_tenant_id="other",
        required_scope="agent:read",
    )
    assert DefaultAuthorizationService().authorize(request) is AuthorizationDecision.DENY


def test_missing_scope_is_denied() -> None:
    request = AuthorizationRequest(
        context=context(),
        action="read",
        resource="agent:run:1",
        resource_tenant_id="acme",
        required_scope="agent:write",
    )
    assert DefaultAuthorizationService().authorize(request) is AuthorizationDecision.DENY


def test_matching_tenant_and_scope_are_allowed() -> None:
    request = AuthorizationRequest(
        context=context(),
        action="read",
        resource="agent:run:1",
        resource_tenant_id="acme",
        required_scope="agent:read",
    )
    assert DefaultAuthorizationService().authorize(request) is AuthorizationDecision.ALLOW


def test_missing_policy_does_not_disable_explicit_baseline_controls() -> None:
    request = AuthorizationRequest(
        context=context(),
        action="read",
        resource="agent:run:1",
        resource_tenant_id="acme",
    )
    assert DefaultAuthorizationService().authorize(request) is AuthorizationDecision.ALLOW


def test_invalid_tenant_identifier_is_rejected() -> None:
    with pytest.raises(ValueError):
        TenantRef(TenantId("Bad Tenant"), Environment.PRODUCTION)
