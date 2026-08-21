"""Provider-neutral commercial access and usage contracts.

This module deliberately stops at product entitlements and metering. Payment
collection, invoices, tax and card data belong to an external billing provider.
The platform only decides whether a tenant is entitled to a capability and
whether a usage event can be accepted into a tenant-scoped meter.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Mapping


_MAX_FEATURES = 256
_MAX_METADATA = 32
_MAX_KEY_LENGTH = 64
_MAX_VALUE_LENGTH = 256
_MAX_FEATURE_LENGTH = 128


def _bounded_metadata(values: Mapping[str, str]) -> dict[str, str]:
    if len(values) > _MAX_METADATA:
        raise ValueError("metadata exceeds maximum cardinality")
    result: dict[str, str] = {}
    for key, value in values.items():
        if not isinstance(key, str) or not key or len(key) > _MAX_KEY_LENGTH:
            raise ValueError("metadata key is invalid")
        if not isinstance(value, str) or len(value) > _MAX_VALUE_LENGTH:
            raise ValueError("metadata value is invalid")
        result[key] = value
    return result


def _require_id(value: str, field_name: str, max_length: int = _MAX_VALUE_LENGTH) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > max_length:
        raise ValueError(f"{field_name} is required and must be bounded")
    return value.strip()


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


class SubscriptionStatus(str, Enum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    PAUSED = "paused"
    CANCELED = "canceled"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class Entitlement:
    feature: str
    limit: Decimal | None = None
    unit: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.feature, "feature", _MAX_FEATURE_LENGTH)
        if self.limit is not None and (self.limit < 0 or not self.limit.is_finite()):
            raise ValueError("entitlement limit must be finite and non-negative")
        if self.limit is not None and not self.unit:
            raise ValueError("bounded entitlements require a unit")
        if self.unit is not None:
            _require_id(self.unit, "unit", 32)


@dataclass(frozen=True, slots=True)
class Plan:
    plan_id: str
    version: int
    entitlements: tuple[Entitlement, ...]
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.plan_id, "plan_id")
        if self.version < 1:
            raise ValueError("plan version must be positive")
        if not self.entitlements or len(self.entitlements) > _MAX_FEATURES:
            raise ValueError("plan must contain between 1 and 256 entitlements")
        features = [item.feature for item in self.entitlements]
        if len(features) != len(set(features)):
            raise ValueError("plan contains duplicate features")
        object.__setattr__(self, "metadata", _bounded_metadata(self.metadata))

    def entitlement(self, feature: str) -> Entitlement | None:
        return next((item for item in self.entitlements if item.feature == feature), None)


@dataclass(frozen=True, slots=True)
class Subscription:
    subscription_id: str
    tenant_id: str
    plan_id: str
    plan_version: int
    status: SubscriptionStatus
    starts_at: datetime
    ends_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_id(self.subscription_id, "subscription_id")
        _require_id(self.tenant_id, "tenant_id")
        _require_id(self.plan_id, "plan_id")
        if self.plan_version < 1:
            raise ValueError("plan version must be positive")
        _require_aware(self.starts_at, "starts_at")
        if self.ends_at is not None:
            _require_aware(self.ends_at, "ends_at")
            if self.ends_at <= self.starts_at:
                raise ValueError("subscription end must be after start")

    def is_active_at(self, when: datetime) -> bool:
        _require_aware(when, "when")
        if self.status not in {SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE}:
            return False
        return self.starts_at <= when and (self.ends_at is None or when < self.ends_at)


@dataclass(frozen=True, slots=True)
class UsageEvent:
    event_id: str
    tenant_id: str
    feature: str
    quantity: Decimal
    occurred_at: datetime
    idempotency_key: str
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.event_id, "event_id")
        _require_id(self.tenant_id, "tenant_id")
        _require_id(self.feature, "feature", _MAX_FEATURE_LENGTH)
        _require_id(self.idempotency_key, "idempotency_key")
        _require_aware(self.occurred_at, "occurred_at")
        if self.quantity <= 0 or not self.quantity.is_finite():
            raise ValueError("usage quantity must be finite and positive")
        object.__setattr__(self, "metadata", _bounded_metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class AccessDecision:
    allowed: bool
    reason: str
    remaining: Decimal | None = None


class EntitlementRegistry:
    """In-memory reference registry; persistence belongs to the existing store boundary."""

    def __init__(self) -> None:
        self._plans: dict[tuple[str, int], Plan] = {}
        self._subscriptions: dict[str, Subscription] = {}

    def register_plan(self, plan: Plan) -> None:
        key = (plan.plan_id, plan.version)
        if key in self._plans:
            raise ValueError("plan version already registered")
        self._plans[key] = plan

    def attach_subscription(self, subscription: Subscription) -> None:
        if (subscription.plan_id, subscription.plan_version) not in self._plans:
            raise ValueError("subscription references an unknown plan version")
        existing = self._subscriptions.get(subscription.tenant_id)
        if existing and existing.subscription_id != subscription.subscription_id:
            raise ValueError("tenant already has a subscription")
        self._subscriptions[subscription.tenant_id] = subscription

    def decide(self, tenant_id: str, feature: str, *, now: datetime | None = None, current_usage: Decimal = Decimal("0")) -> AccessDecision:
        _require_id(tenant_id, "tenant_id")
        _require_id(feature, "feature", _MAX_FEATURE_LENGTH)
        if current_usage < 0 or not current_usage.is_finite():
            raise ValueError("current usage must be finite and non-negative")
        now = now or datetime.now(timezone.utc)
        subscription = self._subscriptions.get(tenant_id)
        if subscription is None or not subscription.is_active_at(now):
            return AccessDecision(False, "subscription_inactive")
        plan = self._plans.get((subscription.plan_id, subscription.plan_version))
        if plan is None:
            return AccessDecision(False, "plan_unavailable")
        entitlement = plan.entitlement(feature)
        if entitlement is None:
            return AccessDecision(False, "feature_not_entitled")
        if entitlement.limit is None:
            return AccessDecision(True, "feature_entitled_unbounded")
        remaining = max(Decimal("0"), entitlement.limit - current_usage)
        if remaining <= 0:
            return AccessDecision(False, "entitlement_limit_exhausted", Decimal("0"))
        return AccessDecision(True, "feature_entitled", remaining)


class UsageMeter:
    """Tenant-safe usage meter with event-level idempotency."""

    def __init__(self) -> None:
        self._events: dict[tuple[str, str], UsageEvent] = {}
        self._totals: dict[tuple[str, str], Decimal] = {}

    def record(self, event: UsageEvent) -> bool:
        key = (event.tenant_id, event.idempotency_key)
        existing = self._events.get(key)
        if existing is not None:
            if existing.event_id != event.event_id or existing.quantity != event.quantity or existing.feature != event.feature:
                raise ValueError("idempotency key reused with different usage event")
            return False
        self._events[key] = event
        total_key = (event.tenant_id, event.feature)
        self._totals[total_key] = self._totals.get(total_key, Decimal("0")) + event.quantity
        return True

    def total(self, tenant_id: str, feature: str) -> Decimal:
        return self._totals.get((tenant_id, feature), Decimal("0"))
