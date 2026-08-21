from datetime import datetime, timedelta, timezone

import pytest

from fde_platform.privacy import (
    DataAsset,
    DataClass,
    ErasureRequest,
    PrivacyRegistry,
    ProcessingPurpose,
    RetentionPolicy,
)

NOW = datetime(2026, 8, 21, tzinfo=timezone.utc)


def policy(days=30):
    return RetentionPolicy("customer-service", ProcessingPurpose.SERVICE_DELIVERY, days)


def asset(**overrides):
    values = {
        "asset_id": "asset-1",
        "tenant_id": "tenant-a",
        "data_class": DataClass.PII,
        "purpose": ProcessingPurpose.SERVICE_DELIVERY,
        "policy_id": "customer-service",
        "created_at": NOW - timedelta(days=31),
    }
    values.update(overrides)
    return DataAsset(**values)


def request():
    return ErasureRequest("req-1", "tenant-a", NOW)


def test_retention_is_tenant_scoped_and_fail_closed():
    registry = PrivacyRegistry()
    registry.register_policy(policy())
    registry.register_asset(asset())
    assert registry.deletion_decision("tenant-a", "asset-1", now=NOW).eligible
    assert registry.deletion_decision("tenant-b", "asset-1", now=NOW).reason == "asset_not_found"


def test_retention_window_blocks_early_deletion():
    registry = PrivacyRegistry()
    registry.register_policy(policy(30))
    registry.register_asset(asset(created_at=NOW - timedelta(days=29)))
    decision = registry.deletion_decision("tenant-a", "asset-1", now=NOW)
    assert decision.eligible is False
    assert decision.reason == "retention_window_open"


def test_legal_hold_blocks_deletion():
    registry = PrivacyRegistry()
    registry.register_policy(policy())
    registry.register_asset(asset(legal_hold=True))
    assert registry.deletion_decision("tenant-a", "asset-1", now=NOW).reason == "legal_hold"
    with pytest.raises(ValueError, match="legal_hold"):
        registry.erase(request(), "asset-1", now=NOW)


def test_erasure_removes_asset_and_creates_integrity_receipt():
    registry = PrivacyRegistry()
    registry.register_policy(policy())
    registry.register_asset(asset())
    receipt = registry.erase(request(), "asset-1", now=NOW)
    assert receipt.request_id == "req-1"
    assert len(receipt.receipt_digest) == 64
    assert registry.deletion_decision("tenant-a", "asset-1", now=NOW).reason == "asset_not_found"
    assert registry.receipt("tenant-a", "asset-1") == receipt


def test_unknown_policy_and_mismatched_purpose_are_rejected():
    registry = PrivacyRegistry()
    with pytest.raises(ValueError, match="unknown retention policy"):
        registry.register_asset(asset())
    registry.register_policy(policy())
    with pytest.raises(ValueError, match="purpose"):
        registry.register_asset(asset(purpose=ProcessingPurpose.ANALYTICS))


def test_sensitive_pii_analytics_is_rejected_by_default():
    with pytest.raises(ValueError, match="sensitive PII"):
        asset(data_class=DataClass.SENSITIVE_PII, purpose=ProcessingPurpose.ANALYTICS)


def test_naive_timestamps_are_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        asset(created_at=datetime(2026, 8, 21))
    with pytest.raises(ValueError, match="timezone-aware"):
        ErasureRequest("req", "tenant-a", datetime(2026, 8, 21))
