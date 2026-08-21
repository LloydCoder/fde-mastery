from datetime import datetime, timedelta, timezone

import pytest

from fde_platform.governance import (
    Attestation,
    ComplianceFramework,
    Control,
    ControlStatus,
    DataClassification,
    DataHandlingPolicy,
    Evidence,
    GovernanceRegistry,
)


NOW = datetime(2026, 8, 21, 15, 0, tzinfo=timezone.utc)


def control() -> Control:
    return Control(
        control_id="GOV-1",
        framework=ComplianceFramework.NIST_AI_RMF,
        title="AI risk governance",
        description="AI risks are governed and documented.",
        owner_role="AI Governance Lead",
        required_evidence_types=frozenset({"policy", "assessment"}),
    )


def evidence(expires: datetime | None = None, *, tenant: str = "tenant-a") -> Evidence:
    return Evidence(
        evidence_id="ev-1",
        tenant_id=tenant,
        control_id="GOV-1",
        evidence_type="policy",
        source_uri="https://example.com/evidence/ev-1",
        content_digest="sha256:" + "a" * 64,
        collected_at=NOW - timedelta(days=1),
        expires_at=expires,
    )


def test_pass_attestation_requires_current_tenant_bound_evidence():
    registry = GovernanceRegistry()
    registry.register_control(control())
    registry.add_evidence(evidence(NOW + timedelta(days=1)))
    registry.attest(Attestation(
        tenant_id="tenant-a",
        control_id="GOV-1",
        status=ControlStatus.PASS,
        assessor="reviewer",
        assessed_at=NOW,
        evidence_ids=("ev-1",),
    ))
    posture = registry.posture("tenant-a", ComplianceFramework.NIST_AI_RMF, now=NOW)
    assert posture.score == 100.0
    assert posture.audit_ready


def test_cross_tenant_evidence_cannot_support_attestation():
    registry = GovernanceRegistry()
    registry.register_control(control())
    registry.add_evidence(evidence(tenant="tenant-b"))
    with pytest.raises(ValueError, match="missing or non-current"):
        registry.attest(Attestation(
            tenant_id="tenant-a",
            control_id="GOV-1",
            status=ControlStatus.PASS,
            assessor="reviewer",
            assessed_at=NOW,
            evidence_ids=("ev-1",),
        ))


def test_expired_evidence_blocks_audit_readiness():
    registry = GovernanceRegistry()
    registry.register_control(control())
    registry.add_evidence(evidence(NOW - timedelta(minutes=1)))
    posture = registry.posture("tenant-a", ComplianceFramework.NIST_AI_RMF, now=NOW)
    assert posture.expired_evidence == 1
    assert not posture.audit_ready


def test_failed_control_requires_rationale():
    with pytest.raises(ValueError, match="rationale"):
        Attestation(
            tenant_id="tenant-a",
            control_id="GOV-1",
            status=ControlStatus.FAIL,
            assessor="reviewer",
            assessed_at=NOW,
        )


def test_data_handling_policy_is_fail_closed_for_higher_classification():
    policy = DataHandlingPolicy(
        classification=DataClassification.CONFIDENTIAL,
        allowed_model_data_classes=frozenset({DataClassification.PUBLIC, DataClassification.INTERNAL}),
        export_allowed=False,
        human_review_required=True,
    )
    assert policy.permits_model(DataClassification.INTERNAL)
    assert not policy.permits_model(DataClassification.CONFIDENTIAL)
    assert not policy.permits_model(DataClassification.RESTRICTED)


def test_audit_pack_is_deterministic_for_fixed_timestamp():
    registry = GovernanceRegistry()
    registry.register_control(control())
    registry.add_evidence(evidence(NOW + timedelta(days=1)))
    registry.attest(Attestation(
        tenant_id="tenant-a",
        control_id="GOV-1",
        status=ControlStatus.PASS,
        assessor="reviewer",
        assessed_at=NOW,
        evidence_ids=("ev-1",),
    ))
    first = registry.audit_pack("tenant-a", ComplianceFramework.NIST_AI_RMF, now=NOW)
    second = registry.audit_pack("tenant-a", ComplianceFramework.NIST_AI_RMF, now=NOW)
    assert first == second
