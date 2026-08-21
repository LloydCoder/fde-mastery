"""Provider-neutral extension marketplace security contracts.

The module deliberately stops at the control-plane boundary: it validates an extension,
its requested capabilities and supply-chain evidence, then records a tenant-scoped
promotion decision. It never executes extension code.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_EXTENSION_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class Capability(str, Enum):
    READ_CONTEXT = "context.read"
    READ_TOOLS = "tools.read"
    INVOKE_TOOLS = "tools.invoke"
    READ_MODELS = "models.read"
    READ_EVENTS = "events.read"
    EMIT_EVENTS = "events.emit"
    NETWORK_EGRESS = "network.egress"
    WRITE_DATA = "data.write"
    ADMIN = "platform.admin"


class ExtensionState(str, Enum):
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    APPROVED = "approved"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class ArtifactProvenance:
    subject_digest: str
    predicate_type: str
    builder_id: str
    source_uri: str
    source_digest: str

    def __post_init__(self) -> None:
        if not _SHA256.fullmatch(self.subject_digest):
            raise ValueError("subject_digest must be a sha256 digest")
        if not self.predicate_type.startswith("https://"):
            raise ValueError("predicate_type must use HTTPS")
        if not self.builder_id.strip() or not self.source_uri.startswith("https://"):
            raise ValueError("builder_id and source_uri are required and source_uri must use HTTPS")
        if not _SHA256.fullmatch(self.source_digest):
            raise ValueError("source_digest must be a sha256 digest")


@dataclass(frozen=True, slots=True)
class SignatureEnvelope:
    algorithm: str
    key_id: str
    signature: str

    def __post_init__(self) -> None:
        if self.algorithm != "ed25519":
            raise ValueError("only ed25519 signatures are supported")
        if not self.key_id.strip() or not self.signature.strip():
            raise ValueError("key_id and signature are required")


@dataclass(frozen=True, slots=True)
class ExtensionManifest:
    extension_id: str
    version: str
    publisher: str
    api_min: str
    api_max: str
    capabilities: frozenset[Capability]
    artifact_digest: str
    provenance: ArtifactProvenance
    signature: SignatureEnvelope
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not _EXTENSION_ID.fullmatch(self.extension_id):
            raise ValueError("invalid extension_id")
        if not _SEMVER.fullmatch(self.version):
            raise ValueError("version must be semantic versioning")
        if not self.publisher.strip():
            raise ValueError("publisher is required")
        if not _SEMVER.fullmatch(self.api_min) or not _SEMVER.fullmatch(self.api_max):
            raise ValueError("api_min and api_max must be semantic versions")
        if not self.capabilities:
            raise ValueError("an extension must request at least one capability")
        if Capability.ADMIN in self.capabilities and len(self.capabilities) > 1:
            raise ValueError("platform.admin cannot be combined with other capabilities")
        if not _SHA256.fullmatch(self.artifact_digest):
            raise ValueError("artifact_digest must be a sha256 digest")
        if self.provenance.subject_digest != self.artifact_digest:
            raise ValueError("provenance subject must match artifact digest")

    def canonical_payload(self) -> bytes:
        """Canonical bytes excluding the signature, suitable for signing/verifying."""
        payload = {
            "extension_id": self.extension_id,
            "version": self.version,
            "publisher": self.publisher,
            "api_min": self.api_min,
            "api_max": self.api_max,
            "capabilities": sorted(cap.value for cap in self.capabilities),
            "artifact_digest": self.artifact_digest,
            "provenance": {
                "subject_digest": self.provenance.subject_digest,
                "predicate_type": self.provenance.predicate_type,
                "builder_id": self.provenance.builder_id,
                "source_uri": self.provenance.source_uri,
                "source_digest": self.provenance.source_digest,
            },
            "metadata": dict(sorted(self.metadata.items())),
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()

    def verify_signature(self, trusted_keys: Mapping[str, bytes]) -> bool:
        key_bytes = trusted_keys.get(self.signature.key_id)
        if key_bytes is None:
            return False
        try:
            Ed25519PublicKey.from_public_bytes(key_bytes).verify(
                base64.b64decode(self.signature.signature, validate=True), self.canonical_payload()
            )
            return True
        except (ValueError, InvalidSignature):
            return False


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    allowed: bool
    state: ExtensionState
    reasons: tuple[str, ...]


class PromotionGate:
    """Fail-closed admission and promotion policy for extensions."""

    def evaluate(
        self,
        manifest: ExtensionManifest,
        *,
        tenant_id: str,
        current_api: str,
        trusted_keys: Mapping[str, bytes],
        approved_publishers: frozenset[str],
        required_capabilities: frozenset[Capability] = frozenset(),
    ) -> PromotionDecision:
        reasons: list[str] = []
        if not tenant_id.strip():
            reasons.append("tenant_required")
        if not manifest.verify_signature(trusted_keys):
            reasons.append("signature_untrusted")
        if manifest.publisher not in approved_publishers:
            reasons.append("publisher_not_approved")
        if required_capabilities and not required_capabilities.issubset(manifest.capabilities):
            reasons.append("required_capability_missing")
        if not _api_in_range(current_api, manifest.api_min, manifest.api_max):
            reasons.append("api_incompatible")
        if reasons:
            return PromotionDecision(False, ExtensionState.SUBMITTED, tuple(reasons))
        return PromotionDecision(True, ExtensionState.APPROVED, ())


class ExtensionRegistry:
    """In-memory reference registry with mandatory tenant isolation and immutable identity."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], tuple[ExtensionManifest, ExtensionState]] = {}

    def register(self, tenant_id: str, manifest: ExtensionManifest) -> None:
        tenant = tenant_id.strip()
        if not tenant:
            raise ValueError("tenant_id is required")
        key = (tenant, manifest.extension_id)
        if key in self._items:
            raise ValueError("extension already registered for tenant")
        self._items[key] = (manifest, ExtensionState.SUBMITTED)

    def promote(self, tenant_id: str, extension_id: str, decision: PromotionDecision) -> None:
        key = (tenant_id, extension_id)
        item = self._items.get(key)
        if item is None:
            raise KeyError("extension not found")
        if not decision.allowed:
            raise ValueError("cannot promote rejected extension")
        manifest, _ = item
        self._items[key] = (manifest, decision.state)

    def get(self, tenant_id: str, extension_id: str) -> tuple[ExtensionManifest, ExtensionState]:
        item = self._items.get((tenant_id, extension_id))
        if item is None:
            raise KeyError("extension not found")
        return item

    def digest(self, tenant_id: str, extension_id: str) -> str:
        manifest, _ = self.get(tenant_id, extension_id)
        return "sha256:" + hashlib.sha256(manifest.canonical_payload()).hexdigest()


def _semver_tuple(version: str) -> tuple[int, int, int]:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
    if match is None:
        raise ValueError("invalid semantic version")
    return tuple(int(part) for part in match.groups())


def _api_in_range(current: str, minimum: str, maximum: str) -> bool:
    value = _semver_tuple(current)
    return _semver_tuple(minimum) <= value <= _semver_tuple(maximum)
