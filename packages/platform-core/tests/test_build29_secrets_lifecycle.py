from datetime import datetime, timedelta, timezone

import pytest

from fde_platform.secrets import (
    SecretAccessGrant,
    SecretLifecycleRegistry,
    SecretRef,
    SecretState,
    SecretType,
)

NOW = datetime(2026, 8, 21, tzinfo=timezone.utc)


def secret(**overrides):
    values = {
        "secret_id": "api-1",
        "tenant_id": "tenant-a",
        "provider": "vault",
        "external_ref": "kv/tenant-a/api-1",
        "secret_type": SecretType.API_KEY,
        "consumer_id": "agent-a",
        "purpose": "integration",
        "created_at": NOW - timedelta(days=10),
        "rotation_interval_days": 30,
    }
    values.update(overrides)
    return SecretRef(**values)


def grant(**overrides):
    values = {
        "grant_id": "grant-1",
        "tenant_id": "tenant-a",
        "secret_id": "api-1",
        "subject_id": "agent-a",
        "scope_id": "integration-a",
        "granted_at": NOW - timedelta(hours=1),
        "expires_at": NOW + timedelta(hours=1),
        "purpose": "integration",
    }
    values.update(overrides)
    return SecretAccessGrant(**values)


def test_access_is_tenant_and_scope_bound():
    registry = SecretLifecycleRegistry()
    registry.register(secret())
    registry.grant(grant())
    assert registry.access_decision("tenant-a", "api-1", "agent-a", "integration-a", now=NOW).allowed
    assert not registry.access_decision("tenant-b", "api-1", "agent-a", "integration-a", now=NOW).allowed
    assert not registry.access_decision("tenant-a", "api-1", "agent-a", "other", now=NOW).allowed


def test_revoked_and_expired_secrets_fail_closed():
    registry = SecretLifecycleRegistry()
    registry.register(secret(state=SecretState.REVOKED))
    registry.grant(grant())
    assert registry.access_decision("tenant-a", "api-1", "agent-a", "integration-a", now=NOW).reason == "secret_inactive"


def test_rotation_due_blocks_access():
    registry = SecretLifecycleRegistry()
    registry.register(secret(created_at=NOW - timedelta(days=31)))
    registry.grant(grant())
    assert registry.access_decision("tenant-a", "api-1", "agent-a", "integration-a", now=NOW).reason == "rotation_required"


def test_rotation_resets_due_window():
    registry = SecretLifecycleRegistry()
    registry.register(secret(created_at=NOW - timedelta(days=31)))
    registry.grant(grant())
    rotated = NOW - timedelta(hours=1)
    registry.transition("tenant-a", "api-1", SecretState.ACTIVE, rotated_at=rotated)
    assert registry.access_decision("tenant-a", "api-1", "agent-a", "integration-a", now=NOW).allowed


def test_revoked_secret_cannot_be_reactivated():
    registry = SecretLifecycleRegistry()
    registry.register(secret(state=SecretState.REVOKED))
    with pytest.raises(ValueError, match="reactivated"):
        registry.transition("tenant-a", "api-1", SecretState.ACTIVE)


def test_duplicate_grants_and_unknown_secrets_fail():
    registry = SecretLifecycleRegistry()
    with pytest.raises(ValueError, match="secret_not_found"):
        registry.grant(grant())
    registry.register(secret())
    registry.grant(grant())
    with pytest.raises(ValueError, match="already registered"):
        registry.grant(grant())


def test_secret_material_is_never_part_of_the_contract():
    ref = secret()
    assert "value" not in ref.__dataclass_fields__
    assert "secret" not in ref.__dataclass_fields__


def test_naive_timestamps_are_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        secret(created_at=datetime(2026, 8, 21))
