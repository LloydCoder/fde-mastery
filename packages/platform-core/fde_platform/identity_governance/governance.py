"""Provider-neutral identity governance and delegated-access contracts.

This layer manages roles, permissions, bindings and provisioning state. It is
not an authorization replacement: the existing policy decision point remains
the final authority for every request.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping


_MAX_PERMISSIONS = 128
_MAX_ROLES = 256
_MAX_METADATA = 32


class SubjectType(str, Enum):
    USER = "user"
    GROUP = "group"
    SERVICE_ACCOUNT = "service_account"


@dataclass(frozen=True, slots=True)
class Permission:
    resource: str
    action: str

    def __post_init__(self) -> None:
        if not self.resource.strip() or not self.action.strip():
            raise ValueError("resource and action are required")
        if len(self.resource) > 128 or len(self.action) > 64:
            raise ValueError("permission fields are bounded")

    @property
    def key(self) -> str:
        return f"{self.resource}:{self.action}"


@dataclass(frozen=True, slots=True)
class Role:
    role_id: str
    name: str
    permissions: tuple[Permission, ...]
    managed: bool = False

    def __post_init__(self) -> None:
        if not self.role_id.strip() or not self.name.strip():
            raise ValueError("role identity is required")
        if not self.permissions or len(self.permissions) > _MAX_PERMISSIONS:
            raise ValueError("role must contain between 1 and 128 permissions")
        if len({permission.key for permission in self.permissions}) != len(self.permissions):
            raise ValueError("role contains duplicate permissions")


@dataclass(frozen=True, slots=True)
class RoleBinding:
    binding_id: str
    tenant_id: str
    subject_id: str
    subject_type: SubjectType
    role_id: str
    scope_id: str
    created_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for value, name, limit in (
            (self.binding_id, "binding_id", 128),
            (self.tenant_id, "tenant_id", 128),
            (self.subject_id, "subject_id", 256),
            (self.role_id, "role_id", 128),
            (self.scope_id, "scope_id", 256),
        ):
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
                raise ValueError(f"{name} is required and bounded")
        for timestamp, name in ((self.created_at, "created_at"), (self.expires_at, "expires_at"), (self.revoked_at, "revoked_at")):
            if timestamp is not None and (timestamp.tzinfo is None or timestamp.utcoffset() is None):
                raise ValueError(f"{name} must be timezone-aware")
        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")
        if len(self.metadata) > _MAX_METADATA:
            raise ValueError("metadata exceeds maximum cardinality")

    def active_at(self, when: datetime) -> bool:
        if when.tzinfo is None or when.utcoffset() is None:
            raise ValueError("when must be timezone-aware")
        if self.revoked_at is not None and when >= self.revoked_at:
            return False
        return when >= self.created_at and (self.expires_at is None or when < self.expires_at)


@dataclass(frozen=True, slots=True)
class ProvisioningChange:
    change_id: str
    tenant_id: str
    subject_id: str
    subject_type: SubjectType
    operation: str
    occurred_at: datetime
    source: str

    def __post_init__(self) -> None:
        for value, name in ((self.change_id, "change_id"), (self.tenant_id, "tenant_id"), (self.subject_id, "subject_id"), (self.operation, "operation"), (self.source, "source")):
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > 256:
                raise ValueError(f"{name} is required and bounded")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")


class GovernanceRegistry:
    """Reference identity-governance registry; final authorization stays in the PDP."""

    def __init__(self) -> None:
        self._roles: dict[str, Role] = {}
        self._bindings: dict[str, RoleBinding] = {}
        self._provisioning: dict[str, ProvisioningChange] = {}

    def register_role(self, role: Role) -> None:
        if len(self._roles) >= _MAX_ROLES and role.role_id not in self._roles:
            raise ValueError("role registry capacity exceeded")
        if role.role_id in self._roles:
            raise ValueError("role already registered")
        self._roles[role.role_id] = role

    def bind(self, binding: RoleBinding) -> None:
        if binding.role_id not in self._roles:
            raise ValueError("binding references unknown role")
        if binding.binding_id in self._bindings:
            raise ValueError("binding already registered")
        self._bindings[binding.binding_id] = binding

    def revoke(self, binding_id: str, when: datetime) -> None:
        binding = self._bindings.get(binding_id)
        if binding is None:
            raise ValueError("binding_not_found")
        if when.tzinfo is None or when.utcoffset() is None:
            raise ValueError("when must be timezone-aware")
        if binding.revoked_at is not None:
            return
        self._bindings[binding_id] = RoleBinding(
            binding_id=binding.binding_id,
            tenant_id=binding.tenant_id,
            subject_id=binding.subject_id,
            subject_type=binding.subject_type,
            role_id=binding.role_id,
            scope_id=binding.scope_id,
            created_at=binding.created_at,
            expires_at=binding.expires_at,
            revoked_at=when,
            metadata=binding.metadata,
        )

    def effective_permissions(self, tenant_id: str, subject_id: str, scope_id: str, *, now: datetime | None = None) -> frozenset[str]:
        when = now or datetime.now(timezone.utc)
        permissions: set[str] = set()
        for binding in self._bindings.values():
            if binding.tenant_id != tenant_id or binding.subject_id != subject_id or binding.scope_id != scope_id:
                continue
            if not binding.active_at(when):
                continue
            permissions.update(permission.key for permission in self._roles[binding.role_id].permissions)
        return frozenset(permissions)

    def record_provisioning_change(self, change: ProvisioningChange) -> None:
        if change.change_id in self._provisioning:
            raise ValueError("change already recorded")
        self._provisioning[change.change_id] = change
