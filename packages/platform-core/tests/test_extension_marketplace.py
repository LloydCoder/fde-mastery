import base64
import hashlib

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from fde_platform.extensions import (
    ArtifactProvenance,
    Capability,
    ExtensionManifest,
    ExtensionRegistry,
    ExtensionState,
    PromotionGate,
    SignatureEnvelope,
)


def public_bytes(key: Ed25519PrivateKey) -> bytes:
    return key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def make_manifest(private_key: Ed25519PrivateKey, *, publisher: str = "acme") -> ExtensionManifest:
    artifact = "sha256:" + hashlib.sha256(b"extension-artifact").hexdigest()
    provenance = ArtifactProvenance(
        subject_digest=artifact,
        predicate_type="https://slsa.dev/provenance/v1",
        builder_id="https://github.com/actions/runner",
        source_uri="https://github.com/acme/extension",
        source_digest="sha256:" + "1" * 64,
    )
    unsigned = ExtensionManifest(
        extension_id="acme.ticketing",
        version="1.2.3",
        publisher=publisher,
        api_min="1.20.0",
        api_max="1.99.0",
        capabilities=frozenset({Capability.READ_CONTEXT, Capability.INVOKE_TOOLS}),
        artifact_digest=artifact,
        provenance=provenance,
        signature=SignatureEnvelope("ed25519", "acme-prod", "placeholder"),
        metadata={"display_name": "Ticketing"},
    )
    signature = base64.b64encode(private_key.sign(unsigned.canonical_payload())).decode()
    return ExtensionManifest(
        extension_id=unsigned.extension_id,
        version=unsigned.version,
        publisher=unsigned.publisher,
        api_min=unsigned.api_min,
        api_max=unsigned.api_max,
        capabilities=unsigned.capabilities,
        artifact_digest=unsigned.artifact_digest,
        provenance=unsigned.provenance,
        signature=SignatureEnvelope("ed25519", "acme-prod", signature),
        metadata=unsigned.metadata,
    )


def test_signature_and_provenance_are_verified():
    key = Ed25519PrivateKey.generate()
    manifest = make_manifest(key)
    assert manifest.verify_signature({"acme-prod": public_bytes(key)})
    assert not manifest.verify_signature({"other": public_bytes(key)})


def test_promotion_is_fail_closed_for_unapproved_publisher():
    key = Ed25519PrivateKey.generate()
    manifest = make_manifest(key, publisher="unapproved")
    decision = PromotionGate().evaluate(
        manifest,
        tenant_id="tenant-a",
        current_api="1.21.0",
        trusted_keys={"acme-prod": public_bytes(key)},
        approved_publishers=frozenset({"acme"}),
    )
    assert not decision.allowed
    assert "publisher_not_approved" in decision.reasons


def test_promotion_rejects_api_mismatch():
    key = Ed25519PrivateKey.generate()
    manifest = make_manifest(key)
    decision = PromotionGate().evaluate(
        manifest,
        tenant_id="tenant-a",
        current_api="2.0.0",
        trusted_keys={"acme-prod": public_bytes(key)},
        approved_publishers=frozenset({"acme"}),
    )
    assert not decision.allowed
    assert "api_incompatible" in decision.reasons


def test_registry_is_tenant_scoped_and_requires_promotion():
    key = Ed25519PrivateKey.generate()
    manifest = make_manifest(key)
    registry = ExtensionRegistry()
    registry.register("tenant-a", manifest)
    with pytest.raises(KeyError):
        registry.get("tenant-b", manifest.extension_id)
    decision = PromotionGate().evaluate(
        manifest,
        tenant_id="tenant-a",
        current_api="1.21.0",
        trusted_keys={"acme-prod": public_bytes(key)},
        approved_publishers=frozenset({"acme"}),
    )
    registry.promote("tenant-a", manifest.extension_id, decision)
    _, state = registry.get("tenant-a", manifest.extension_id)
    assert state is ExtensionState.APPROVED


def test_manifest_rejects_admin_mixed_with_other_capabilities():
    artifact = "sha256:" + "a" * 64
    provenance = ArtifactProvenance(
        subject_digest=artifact,
        predicate_type="https://slsa.dev/provenance/v1",
        builder_id="builder",
        source_uri="https://example.com/source",
        source_digest="sha256:" + "b" * 64,
    )
    with pytest.raises(ValueError, match="platform.admin"):
        ExtensionManifest(
            extension_id="bad.extension",
            version="1.0.0",
            publisher="acme",
            api_min="1.0.0",
            api_max="1.9.0",
            capabilities=frozenset({Capability.ADMIN, Capability.READ_CONTEXT}),
            artifact_digest=artifact,
            provenance=provenance,
            signature=SignatureEnvelope("ed25519", "key", "x"),
        )
