from datetime import datetime, timedelta, timezone

import pytest

from fde_platform.identity_governance import (
    GovernanceRegistry,
    Permission,
    ProvisioningChange,
    Role,
    RoleBinding,
    SubjectType,
)

NOW = datetime(2026, 8, 21, tzinfo=timezone.utc)


def admin_role():
    return Role(
        "operator",
        "Operator",
        (Permission("engagement", "read"), Permission("engagement", "write")),
    )


def binding(**overrides):
    values = {
        "binding_id": "b-1",
        "tenant_id": "tenant-a",
        "subject_id": "user-a",
        "subject_type": SubjectType.USER,
        "role_id": "operator",
        "scope_id": "engagement-a",
        "created_at": NOW - timedelta(hours=1),
    }
    values.update(overrides)
    return RoleBinding(**values)


def test_permissions_are_tenant_and_scope_bound():
    registry = GovernanceRegistry()
    registry.register_role(admin_role())
    registry.bind(binding())
    assert registry.effective_permissions("tenant-a", "user-a", "engagement-a", now=NOW) == frozenset({"engagement:read", "engagement:write"})
    assert registry.effective_permissions("tenant-b", "user-a", "engagement-a", now=NOW) == frozenset()
    assert registry.effective_permissions("tenant-a", "user-a", "other", now=NOW) == frozenset()


def test_expired_and_revoked_bindings_are_not_effective():
    registry = GovernanceRegistry()
    registry.register_role(admin_role())
    registry.bind(binding(expires_at=NOW + timedelta(hours=1)))
    assert registry.effective_permissions("tenant-a", "user-a", "engagement-a", now=NOW)
    registry.revoke("b-1", NOW)
    assert registry.effective_permissions("tenant-a", "user-a", "engagement-a", now=NOW) == frozenset()


def test_unknown_role_and_duplicate_binding_fail_closed():
    registry = GovernanceRegistry()
    with pytest.raises(ValueError, match="unknown role"):
        registry.bind(binding(role_id="missing"))
    registry.register_role(admin_role())
    registry.bind(binding())
    with pytest.raises(ValueError, match="already registered"):
        registry.bind(binding())


def test_managed_role_can_still_be_explicitly_registered():
    registry = GovernanceRegistry()
    registry.register_role(Role("viewer", "Viewer", (Permission("engagement", "read"),), managed=True))
    assert registry.effective_permissions("tenant-a", "user-a", "engagement-a", now=NOW) == frozenset()


def test_provisioning_changes_are_idempotency_protected():
    registry = GovernanceRegistry()
    change = ProvisioningChange("c-1", "tenant-a", "user-a", SubjectType.USER, "deactivate", NOW, "scim")
    registry.record_provisioning_change(change)
    with pytest.raises(ValueError, match="already recorded"):
        registry.record_provisioning_change(change)


def test_naive_timestamps_are_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        binding(created_at=datetime(2026, 8, 21))
