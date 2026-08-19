from datetime import timedelta

import pytest

from fde_platform.authorization import (
    AuthorizationRequest,
    DecisionReason,
    InMemoryApprovalStore,
    PolicyDecisionPoint,
    PolicyRule,
    RiskTier,
)
from fde_platform.authorization.approvals import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    utc_now,
)
from fde_platform.authorization.audit import AuthorizationAuditEvent
from fde_platform.identity import (
    Environment,
    Principal,
    PrincipalType,
    RequestContext,
    TenantRef,
)


def context(
    *,
    tenant: str = "tenant-a",
    roles: frozenset[str] = frozenset({"operator"}),
    scopes: frozenset[str] = frozenset({"jobs:run"}),
) -> RequestContext:
    ref = TenantRef(tenant_id=tenant, environment=Environment.PRODUCTION)
    return RequestContext(
        principal=Principal(
            "user-1",
            ref.tenant_id,
            PrincipalType.USER,
            roles=roles,
            scopes=scopes,
        ),
        tenant=ref,
        request_id="req-1",
        environment=Environment.PRODUCTION,
    )


def request(ctx: RequestContext, tenant: str | None = None) -> AuthorizationRequest:
    return AuthorizationRequest(
        context=ctx,
        action="workflow.run",
        resource="workflow:payments",
        resource_tenant_id=tenant or str(ctx.tenant_id),
        required_scope="jobs:run",
        required_roles=frozenset({"operator"}),
    )


def test_pdp_denies_cross_tenant_before_policy() -> None:
    pdp = PolicyDecisionPoint(
        (
            PolicyRule(
                "run",
                "1.0.0",
                frozenset({"workflow.run"}),
                allowed_roles=frozenset({"operator"}),
            ),
        )
    )
    decision = pdp.evaluate(request(context(), tenant="tenant-b"))
    assert decision.reason is DecisionReason.DENIED_TENANT
    assert not decision.allowed


def test_pdp_fails_closed_for_unknown_action() -> None:
    pdp = PolicyDecisionPoint(())
    decision = pdp.evaluate(request(context()))
    assert decision.reason is DecisionReason.DENIED_ACTION


def test_high_risk_requires_approval() -> None:
    pdp = PolicyDecisionPoint(
        (
            PolicyRule(
                "run",
                "1.0.0",
                frozenset({"workflow.run"}),
                max_risk=RiskTier.CRITICAL,
            ),
        )
    )
    decision = pdp.evaluate(request(context()), risk=RiskTier.HIGH)
    assert decision.requires_approval
    assert decision.reason is DecisionReason.DENIED_RISK


def test_missing_scope_denies() -> None:
    pdp = PolicyDecisionPoint(
        (
            PolicyRule(
                "run",
                "1.0.0",
                frozenset({"workflow.run"}),
                required_scopes=frozenset({"jobs:run"}),
            ),
        )
    )
    decision = pdp.evaluate(request(context(scopes=frozenset())))
    assert decision.reason is DecisionReason.DENIED_SCOPE


def test_approval_is_single_use_and_expiry_bound() -> None:
    now = utc_now()
    store = InMemoryApprovalStore()
    store.put(
        ApprovalRequest(
            "ap-1",
            "tenant-a",
            "user-1",
            "workflow.run",
            "workflow:payments",
            RiskTier.HIGH,
            "1.0.0",
            now,
            now + timedelta(minutes=5),
        )
    )
    store.decide(
        ApprovalDecision(
            "ap-1",
            ApprovalStatus.APPROVED,
            "admin",
            now + timedelta(minutes=1),
        )
    )
    with pytest.raises(ValueError, match="already decided"):
        store.decide(
            ApprovalDecision(
                "ap-1",
                ApprovalStatus.REJECTED,
                "admin",
                now + timedelta(minutes=2),
            )
        )


def test_audit_digest_changes_when_chain_input_changes() -> None:
    now = utc_now()
    pdp = PolicyDecisionPoint(
        (PolicyRule("run", "1.0.0", frozenset({"workflow.run"})),)
    )
    decision = pdp.evaluate(request(context()))
    first = AuthorizationAuditEvent(
        "req-1",
        "tenant-a",
        "user-1",
        "workflow.run",
        "workflow:payments",
        decision,
        now,
    )
    second = AuthorizationAuditEvent(
        "req-2",
        "tenant-a",
        "user-1",
        "workflow.run",
        "workflow:payments",
        decision,
        now,
        first.digest,
    )
    assert first.digest != second.digest
