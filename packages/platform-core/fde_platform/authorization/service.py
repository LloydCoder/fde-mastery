"""Fail-closed authorization service for the platform boundary."""

from __future__ import annotations

from typing import Protocol

from .policy import AuthorizationDecision, AuthorizationRequest, Policy


class AuthorizationService(Protocol):
    def authorize(self, request: AuthorizationRequest) -> AuthorizationDecision: ...
    def require(self, request: AuthorizationRequest) -> None: ...


class DefaultAuthorizationService:
    def __init__(self, policy: Policy | None = None) -> None:
        self._policy = policy

    def authorize(self, request: AuthorizationRequest) -> AuthorizationDecision:
        if request.context.tenant_id != request.resource_tenant_id:
            return AuthorizationDecision.DENY
        if not request.action.strip() or not request.resource.strip():
            return AuthorizationDecision.DENY
        if request.required_scope and not request.context.principal.has_scope(request.required_scope):
            return AuthorizationDecision.DENY
        if request.required_roles and not (request.context.principal.roles & request.required_roles):
            return AuthorizationDecision.DENY
        if self._policy is None:
            return AuthorizationDecision.ALLOW
        return self._policy.evaluate(request)

    def require(self, request: AuthorizationRequest) -> None:
        if self.authorize(request) is not AuthorizationDecision.ALLOW:
            raise PermissionError("authorization denied")
