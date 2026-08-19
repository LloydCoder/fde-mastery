"""Deterministic policy decision point (PDP) and decision model."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from ..identity import RequestContext
from .policy import AuthorizationDecision, AuthorizationRequest
from .risk import RiskTier


class DecisionReason(str, Enum):
    ALLOWED = "allowed"
    DENIED_TENANT = "tenant_mismatch"
    DENIED_SCOPE = "missing_scope"
    DENIED_ROLE = "missing_role"
    DENIED_ACTION = "action_not_allowed"
    DENIED_RISK = "risk_requires_approval"
    DENIED_POLICY = "policy_denied"


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    decision: AuthorizationDecision
    reason: DecisionReason
    risk: RiskTier
    policy_version: str
    requires_approval: bool = False

    @property
    def allowed(self) -> bool:
        return self.decision is AuthorizationDecision.ALLOW


@dataclass(frozen=True, slots=True)
class PolicyRule:
    policy_id: str
    version: str
    actions: frozenset[str]
    resource_prefixes: tuple[str, ...] = ()
    allowed_roles: frozenset[str] = frozenset()
    required_scopes: frozenset[str] = frozenset()
    max_risk: RiskTier = RiskTier.MEDIUM
    approval_required: bool = False


class PolicyDecisionPoint:
    """Fail-closed, deterministic PDP.

    Rules are immutable and selected by exact action/resource matching. Tenant
    isolation is checked before rule evaluation so a matching policy can never
    grant cross-tenant access.
    """

    def __init__(self, rules: tuple[PolicyRule, ...], *, default_version: str = "deny-1") -> None:
        self._rules = rules
        self._default_version = default_version

    def evaluate(
        self,
        request: AuthorizationRequest,
        *,
        risk: RiskTier = RiskTier.LOW,
    ) -> PolicyDecision:
        if str(request.context.tenant_id) != str(request.resource_tenant_id):
            return PolicyDecision(AuthorizationDecision.DENY, DecisionReason.DENIED_TENANT, risk, self._default_version)

        candidates = [
            rule for rule in self._rules
            if request.action in rule.actions
            and (not rule.resource_prefixes or any(request.resource.startswith(p) for p in rule.resource_prefixes))
        ]
        if not candidates:
            return PolicyDecision(AuthorizationDecision.DENY, DecisionReason.DENIED_ACTION, risk, self._default_version)

        for rule in candidates:
            if rule.allowed_roles and not (rule.allowed_roles & request.context.principal.roles):
                continue
            if rule.required_scopes and not rule.required_scopes.issubset(request.context.principal.scopes):
                continue
            if risk > rule.max_risk:
                return PolicyDecision(AuthorizationDecision.DENY, DecisionReason.DENIED_RISK, risk, rule.version, True)
            needs_approval = rule.approval_required or risk.requires_human_approval
            if needs_approval:
                return PolicyDecision(AuthorizationDecision.DENY, DecisionReason.DENIED_RISK, risk, rule.version, True)
            return PolicyDecision(AuthorizationDecision.ALLOW, DecisionReason.ALLOWED, risk, rule.version)

        return PolicyDecision(AuthorizationDecision.DENY, DecisionReason.DENIED_POLICY, risk, candidates[0].version)
