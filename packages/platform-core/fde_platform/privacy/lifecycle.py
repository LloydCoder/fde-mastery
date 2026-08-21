"""Provider-neutral privacy, retention and erasure boundary.

The lifecycle layer records policy and deletion eligibility. It deliberately
contains no PII values and does not replace a production persistence adapter.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Mapping


_MAX_METADATA = 32
_MAX_KEY = 64
_MAX_VALUE = 256


class DataClass(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    PII = "pii"
    SENSITIVE_PII = "sensitive_pii"


class ProcessingPurpose(str, Enum):
    SERVICE_DELIVERY = "service_delivery"
    SECURITY = "security"
    SUPPORT = "support"
    ANALYTICS = "analytics"
    LEGAL = "legal"


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    policy_id: str
    purpose: ProcessingPurpose
    retention_days: int
    review_required: bool = True

    def __post_init__(self) -> None:
        if not self.policy_id.strip():
            raise ValueError("policy_id is required")
        if self.retention_days < 1 or self.retention_days > 3650:
            raise ValueError("retention_days must be between 1 and 3650")


@dataclass(frozen=True, slots=True)
class DataAsset:
    asset_id: str
    tenant_id: str
    data_class: DataClass
    purpose: ProcessingPurpose
    policy_id: str
    created_at: datetime
    legal_hold: bool = False
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for value, name in (
            (self.asset_id, "asset_id"),
            (self.tenant_id, "tenant_id"),
            (self.policy_id, "policy_id"),
        ):
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > _MAX_VALUE:
                raise ValueError(f"{name} is required and bounded")
        if self.data_class is DataClass.SENSITIVE_PII and self.purpose is ProcessingPurpose.ANALYTICS:
            raise ValueError("sensitive PII cannot use analytics as an unqualified purpose")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        if len(self.metadata) > _MAX_METADATA:
            raise ValueError("metadata exceeds maximum cardinality")
        normalized: dict[str, str] = {}
        for key, value in self.metadata.items():
            if not isinstance(key, str) or not key or len(key) > _MAX_KEY:
                raise ValueError("metadata key is invalid")
            if not isinstance(value, str) or len(value) > _MAX_VALUE:
                raise ValueError("metadata value is invalid")
            normalized[key] = value
        object.__setattr__(self, "metadata", normalized)


@dataclass(frozen=True, slots=True)
class ErasureRequest:
    request_id: str
    tenant_id: str
    requested_at: datetime
    reason: str = "data_subject_request"

    def __post_init__(self) -> None:
        for value, name in ((self.request_id, "request_id"), (self.tenant_id, "tenant_id")):
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > _MAX_VALUE:
                raise ValueError(f"{name} is required and bounded")
        if self.requested_at.tzinfo is None or self.requested_at.utcoffset() is None:
            raise ValueError("requested_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class LifecycleDecision:
    eligible: bool
    reason: str
    due_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class DeletionReceipt:
    request_id: str
    tenant_id: str
    asset_id: str
    deleted_at: datetime
    receipt_digest: str


class PrivacyRegistry:
    """Reference lifecycle registry; real storage and erasure adapters remain external ports."""

    def __init__(self) -> None:
        self._policies: dict[str, RetentionPolicy] = {}
        self._assets: dict[tuple[str, str], DataAsset] = {}
        self._receipts: dict[tuple[str, str], DeletionReceipt] = {}

    def register_policy(self, policy: RetentionPolicy) -> None:
        if policy.policy_id in self._policies:
            raise ValueError("policy_id already registered")
        self._policies[policy.policy_id] = policy

    def register_asset(self, asset: DataAsset) -> None:
        policy = self._policies.get(asset.policy_id)
        if policy is None:
            raise ValueError("asset references unknown retention policy")
        if policy.purpose is not asset.purpose:
            raise ValueError("asset purpose does not match retention policy")
        key = (asset.tenant_id, asset.asset_id)
        if key in self._assets:
            raise ValueError("asset already registered")
        self._assets[key] = asset

    def deletion_decision(self, tenant_id: str, asset_id: str, *, now: datetime | None = None) -> LifecycleDecision:
        asset = self._assets.get((tenant_id, asset_id))
        if asset is None:
            return LifecycleDecision(False, "asset_not_found")
        if asset.legal_hold:
            return LifecycleDecision(False, "legal_hold")
        policy = self._policies.get(asset.policy_id)
        if policy is None:
            return LifecycleDecision(False, "retention_policy_missing")
        when = now or datetime.now(timezone.utc)
        if when.tzinfo is None or when.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        due_at = asset.created_at + timedelta(days=policy.retention_days)
        if when < due_at:
            return LifecycleDecision(False, "retention_window_open", due_at)
        return LifecycleDecision(True, "retention_window_elapsed", due_at)

    def erase(self, request: ErasureRequest, asset_id: str, *, now: datetime | None = None) -> DeletionReceipt:
        key = (request.tenant_id, asset_id)
        asset = self._assets.get(key)
        if asset is None:
            raise ValueError("asset_not_found")
        if asset.legal_hold:
            raise ValueError("legal_hold")
        when = now or datetime.now(timezone.utc)
        decision = self.deletion_decision(request.tenant_id, asset_id, now=when)
        if not decision.eligible:
            raise ValueError(decision.reason)
        del self._assets[key]
        payload = f"{request.request_id}:{request.tenant_id}:{asset_id}:{when.isoformat()}".encode()
        receipt = DeletionReceipt(
            request_id=request.request_id,
            tenant_id=request.tenant_id,
            asset_id=asset_id,
            deleted_at=when,
            receipt_digest=hashlib.sha256(payload).hexdigest(),
        )
        self._receipts[key] = receipt
        return receipt

    def receipt(self, tenant_id: str, asset_id: str) -> DeletionReceipt | None:
        return self._receipts.get((tenant_id, asset_id))
