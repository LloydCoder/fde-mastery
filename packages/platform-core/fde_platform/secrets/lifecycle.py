"""Provider-neutral metadata and policy boundary for secrets and keys.

Secret/key material is never accepted by these contracts. A SecretRef points to
an external secrets manager/KMS object and governs who may request access and
when rotation/revocation is required.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Mapping


_MAX_METADATA = 32


class SecretType(str, Enum):
    API_KEY = "api_key"
    DATABASE_CREDENTIAL = "database_credential"
    OAUTH_CLIENT_SECRET = "oauth_client_secret"
    SIGNING_KEY = "signing_key"
    ENCRYPTION_KEY = "encryption_key"
    CERTIFICATE = "certificate"


class SecretState(str, Enum):
    ACTIVE = "active"
    ROTATION_DUE = "rotation_due"
    ROTATING = "rotating"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class SecretRef:
    secret_id: str
    tenant_id: str
    provider: str
    external_ref: str
    secret_type: SecretType
    consumer_id: str
    purpose: str
    created_at: datetime
    rotation_interval_days: int
    expires_at: datetime | None = None
    state: SecretState = SecretState.ACTIVE
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for value, name, limit in (
            (self.secret_id, "secret_id", 128),
            (self.tenant_id, "tenant_id", 128),
            (self.provider, "provider", 128),
            (self.external_ref, "external_ref", 512),
            (self.consumer_id, "consumer_id", 256),
            (self.purpose, "purpose", 256),
        ):
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
                raise ValueError(f"{name} is required and bounded")
        if self.rotation_interval_days < 1 or self.rotation_interval_days > 3650:
            raise ValueError("rotation interval must be between 1 and 3650 days")
        for timestamp, name in ((self.created_at, "created_at"), (self.expires_at, "expires_at")):
            if timestamp is not None and (timestamp.tzinfo is None or timestamp.utcoffset() is None):
                raise ValueError(f"{name} must be timezone-aware")
        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")
        if len(self.metadata) > _MAX_METADATA:
            raise ValueError("metadata exceeds maximum cardinality")
        if any(not isinstance(k, str) or not isinstance(v, str) for k, v in self.metadata.items()):
            raise ValueError("metadata must contain strings")

    def rotation_due_at(self) -> datetime:
        return self.created_at + timedelta(days=self.rotation_interval_days)


@dataclass(frozen=True, slots=True)
class SecretAccessGrant:
    grant_id: str
    tenant_id: str
    secret_id: str
    subject_id: str
    scope_id: str
    granted_at: datetime
    expires_at: datetime
    purpose: str

    def __post_init__(self) -> None:
        for value, name in (
            (self.grant_id, "grant_id"),
            (self.tenant_id, "tenant_id"),
            (self.secret_id, "secret_id"),
            (self.subject_id, "subject_id"),
            (self.scope_id, "scope_id"),
            (self.purpose, "purpose"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        if self.granted_at.tzinfo is None or self.granted_at.utcoffset() is None:
            raise ValueError("granted_at must be timezone-aware")
        if self.expires_at.tzinfo is None or self.expires_at.utcoffset() is None:
            raise ValueError("expires_at must be timezone-aware")
        if self.expires_at <= self.granted_at:
            raise ValueError("grant expiry must be after grant creation")

    def active_at(self, when: datetime) -> bool:
        if when.tzinfo is None or when.utcoffset() is None:
            raise ValueError("when must be timezone-aware")
        return self.granted_at <= when < self.expires_at


@dataclass(frozen=True, slots=True)
class SecretAccessDecision:
    allowed: bool
    reason: str


class SecretLifecycleRegistry:
    """Reference metadata registry; secret material remains in an external vault/KMS."""

    def __init__(self) -> None:
        self._secrets: dict[tuple[str, str], SecretRef] = {}
        self._grants: dict[str, SecretAccessGrant] = {}

    def register(self, secret: SecretRef) -> None:
        key = (secret.tenant_id, secret.secret_id)
        if key in self._secrets:
            raise ValueError("secret already registered")
        self._secrets[key] = secret

    def grant(self, access: SecretAccessGrant) -> None:
        if (access.tenant_id, access.secret_id) not in self._secrets:
            raise ValueError("secret_not_found")
        if access.grant_id in self._grants:
            raise ValueError("grant already registered")
        self._grants[access.grant_id] = access

    def access_decision(self, tenant_id: str, secret_id: str, subject_id: str, scope_id: str, *, now: datetime | None = None) -> SecretAccessDecision:
        when = now or datetime.now(timezone.utc)
        secret = self._secrets.get((tenant_id, secret_id))
        if secret is None:
            return SecretAccessDecision(False, "secret_not_found")
        if secret.state in {SecretState.REVOKED, SecretState.EXPIRED}:
            return SecretAccessDecision(False, "secret_inactive")
        if secret.expires_at is not None and when >= secret.expires_at:
            return SecretAccessDecision(False, "secret_expired")
        if when >= secret.rotation_due_at() and secret.state is not SecretState.ROTATING:
            return SecretAccessDecision(False, "rotation_required")
        for grant in self._grants.values():
            if (
                grant.tenant_id == tenant_id
                and grant.secret_id == secret_id
                and grant.subject_id == subject_id
                and grant.scope_id == scope_id
                and grant.active_at(when)
            ):
                return SecretAccessDecision(True, "access_granted")
        return SecretAccessDecision(False, "access_not_granted")

    def transition(self, tenant_id: str, secret_id: str, state: SecretState) -> None:
        key = (tenant_id, secret_id)
        secret = self._secrets.get(key)
        if secret is None:
            raise ValueError("secret_not_found")
        if secret.state is SecretState.REVOKED and state is not SecretState.REVOKED:
            raise ValueError("revoked secret cannot be reactivated")
        self._secrets[key] = SecretRef(
            secret_id=secret.secret_id,
            tenant_id=secret.tenant_id,
            provider=secret.provider,
            external_ref=secret.external_ref,
            secret_type=secret.secret_type,
            consumer_id=secret.consumer_id,
            purpose=secret.purpose,
            created_at=secret.created_at,
            rotation_interval_days=secret.rotation_interval_days,
            expires_at=secret.expires_at,
            state=state,
            metadata=secret.metadata,
        )
