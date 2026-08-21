from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from fde_platform.commercial import (
    Entitlement,
    EntitlementRegistry,
    Plan,
    Subscription,
    SubscriptionStatus,
    UsageEvent,
    UsageMeter,
)


NOW = datetime(2026, 8, 21, tzinfo=timezone.utc)


def plan() -> Plan:
    return Plan(
        plan_id="growth",
        version=1,
        entitlements=(
            Entitlement("agent.runs", Decimal("1000"), "runs"),
            Entitlement("reports", Decimal("20"), "reports"),
        ),
    )


def subscription(status=SubscriptionStatus.ACTIVE) -> Subscription:
    return Subscription(
        subscription_id="sub-1",
        tenant_id="tenant-a",
        plan_id="growth",
        plan_version=1,
        status=status,
        starts_at=NOW - timedelta(days=1),
    )


def test_entitlement_is_tenant_scoped_and_versioned():
    registry = EntitlementRegistry()
    registry.register_plan(plan())
    registry.attach_subscription(subscription())

    allowed = registry.decide("tenant-a", "agent.runs", now=NOW)
    denied = registry.decide("tenant-b", "agent.runs", now=NOW)

    assert allowed.allowed is True
    assert allowed.remaining == Decimal("1000")
    assert denied.allowed is False
    assert denied.reason == "subscription_inactive"


def test_entitlement_limit_is_enforced():
    registry = EntitlementRegistry()
    registry.register_plan(plan())
    registry.attach_subscription(subscription())
    decision = registry.decide("tenant-a", "agent.runs", now=NOW, current_usage=Decimal("1000"))
    assert decision.allowed is False
    assert decision.reason == "entitlement_limit_exhausted"
    assert decision.remaining == Decimal("0")


def test_unknown_plan_version_cannot_be_attached():
    registry = EntitlementRegistry()
    with pytest.raises(ValueError, match="unknown plan"):
        registry.attach_subscription(subscription())


def test_inactive_subscription_fails_closed():
    registry = EntitlementRegistry()
    registry.register_plan(plan())
    registry.attach_subscription(subscription(SubscriptionStatus.PAST_DUE))
    decision = registry.decide("tenant-a", "agent.runs", now=NOW)
    assert decision.allowed is False


def test_naive_subscription_datetime_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        Subscription(
            "sub-1", "tenant-a", "growth", 1, SubscriptionStatus.ACTIVE,
            datetime(2026, 8, 20),
        )


def test_usage_is_idempotent_per_tenant():
    meter = UsageMeter()
    event = UsageEvent(
        "evt-1", "tenant-a", "agent.runs", Decimal("3"), NOW, "request-1"
    )
    assert meter.record(event) is True
    assert meter.record(event) is False
    assert meter.total("tenant-a", "agent.runs") == Decimal("3")


def test_idempotency_key_cannot_change_meaning():
    meter = UsageMeter()
    meter.record(UsageEvent("evt-1", "tenant-a", "agent.runs", Decimal("3"), NOW, "request-1"))
    with pytest.raises(ValueError, match="idempotency"):
        meter.record(UsageEvent("evt-2", "tenant-a", "agent.runs", Decimal("4"), NOW, "request-1"))


def test_usage_isolated_between_tenants():
    meter = UsageMeter()
    meter.record(UsageEvent("evt-a", "tenant-a", "agent.runs", Decimal("3"), NOW, "same-key"))
    meter.record(UsageEvent("evt-b", "tenant-b", "agent.runs", Decimal("7"), NOW, "same-key"))
    assert meter.total("tenant-a", "agent.runs") == Decimal("3")
    assert meter.total("tenant-b", "agent.runs") == Decimal("7")


def test_non_finite_usage_is_rejected():
    with pytest.raises(ValueError):
        UsageEvent("evt", "tenant-a", "agent.runs", Decimal("NaN"), NOW, "key")


def test_duplicate_features_and_unbounded_metadata_are_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        Plan("bad", 1, (Entitlement("x"), Entitlement("x")))
    with pytest.raises(ValueError, match="cardinality"):
        UsageEvent(
            "evt", "tenant-a", "agent.runs", Decimal("1"), NOW, "key",
            {str(i): "x" for i in range(33)},
        )
