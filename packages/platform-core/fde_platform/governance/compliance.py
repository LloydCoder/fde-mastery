"""Provider-neutral governance, evidence and compliance posture contracts.

This layer records control intent and auditable evidence. It does not claim certification;
framework mappings are operational references and customer/legal applicability remains contextual.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping


class ComplianceFramework(str, Enum):
    NIST_AI_RMF = "nist-ai-rmf-1.0"
    NIST_GAI_PROFILE = "nist-ai-600-1"
    ISO_42001 = "iso-42001:2023"
    SOC2 = "soc2"


class ControlStatus(str, Enum):
    NOT_ASSESSED = "not_assessed"
    PARTIAL = "partial"
    PASS = "pass"
    FAIL = "fail"


class EvidenceStatus(str, Enum):
    CURRENT = "current"
    EXPIRED = "expired"
    REVOKED = "revoked"


class DataClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    SECRET = "secret"


@dataclass(frozen=True, slots=True)
class DataHandlingPolicy:
    classification: DataClassification
    allowed_model_data_classes: frozenset[DataClassification]
    export_allowed: bool
    human_review_required: bool

    def permits_model(self, requested: DataClassification) -> bool:
        rank = {
            DataClassification.PUBLIC: 0,
            DataClassification.INTERNAL: 1,
            DataClassification.CONFIDENTIAL: 2,
            DataClassification.RESTRICTED: 3,
            DataClassification.SECRET: 4,
        }
        return requested in self.allowed_model_data_classes and rank[requested] <= rank[self.classification]


@dataclass(frozen=True, slots=True)
class Control:
    control_id: str
    framework: ComplianceFramework
    title: str
    description: str
    owner_role: str
    required_evidence_types: frozenset[str] = field(default_factory=frozenset)
    severity: str = "medium"

    def __post_init__(self) -> None:
        if not self.control_id.strip() or not self.title.strip() or not self.description.strip():
            raise ValueError("control identity and description are required")
        if not self.owner_role.strip():
            raise ValueError("owner_role is required")
        if not self.required_evidence_types:
            raise ValueError("controls must define evidence types")
        if self.severity not in {"low", "medium", "high", "critical"}:
            raise ValueError("invalid severity")


@dataclass(frozen=True, slots=True)
class Evidence:
    evidence_id: str
    tenant_id: str
    control_id: str
    evidence_type: str
    source_uri: str
    content_digest: str
    collected_at: datetime
    expires_at: datetime | None = None
    status: EvidenceStatus = EvidenceStatus.CURRENT
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.evidence_id.strip() or not self.tenant_id.strip() or not self.control_id.strip():
            raise ValueError("evidence identity and tenant are required")
        if not self.evidence_type.strip() or not self.source_uri.startswith("https://"):
            raise ValueError("evidence type and HTTPS source URI are required")
        if not _is_sha256(self.content_digest):
            raise ValueError("content_digest must be sha256:<64 lowercase hex characters>")
        if self.collected_at.tzinfo is None or self.collected_at.utcoffset() is None:
            raise ValueError("collected_at must be timezone-aware")
        if self.expires_at is not None:
            if self.expires_at.tzinfo is None or self.expires_at.utcoffset() is None:
                raise ValueError("expires_at must be timezone-aware")
            if self.expires_at <= self.collected_at:
                raise ValueError("expires_at must be after collected_at")

    def is_current(self, *, now: datetime | None = None) -> bool:
        if self.status is not EvidenceStatus.CURRENT:
            return False
        moment = now or datetime.now(timezone.utc)
        if moment.tzinfo is None or moment.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        return self.expires_at is None or moment < self.expires_at


@dataclass(frozen=True, slots=True)
class Attestation:
    tenant_id: str
    control_id: str
    status: ControlStatus
    assessor: str
    assessed_at: datetime
    evidence_ids: tuple[str, ...] = ()
    rationale: str = ""

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.control_id.strip() or not self.assessor.strip():
            raise ValueError("attestation identity is required")
        if self.assessed_at.tzinfo is None or self.assessed_at.utcoffset() is None:
            raise ValueError("assessed_at must be timezone-aware")
        if self.status is ControlStatus.PASS and not self.evidence_ids:
            raise ValueError("passing controls require evidence")
        if self.status is ControlStatus.FAIL and not self.rationale.strip():
            raise ValueError("failed controls require rationale")


@dataclass(frozen=True, slots=True)
class CompliancePosture:
    tenant_id: str
    framework: ComplianceFramework
    generated_at: datetime
    controls: Mapping[str, ControlStatus]
    current_evidence: int
    expired_evidence: int

    @property
    def score(self) -> float:
        if not self.controls:
            return 0.0
        weights = {
            ControlStatus.PASS: 1.0,
            ControlStatus.PARTIAL: 0.5,
            ControlStatus.NOT_ASSESSED: 0.0,
            ControlStatus.FAIL: 0.0,
        }
        return round(100.0 * sum(weights[s] for s in self.controls.values()) / len(self.controls), 2)

    @property
    def audit_ready(self) -> bool:
        return self.expired_evidence == 0 and all(
            status is ControlStatus.PASS for status in self.controls.values()
        )


class GovernanceRegistry:
    """Tenant-scoped reference registry for controls, evidence and attestations."""

    def __init__(self) -> None:
        self._controls: dict[str, Control] = {}
        self._evidence: dict[tuple[str, str], Evidence] = {}
        self._attestations: dict[tuple[str, str], Attestation] = {}

    def register_control(self, control: Control) -> None:
        if control.control_id in self._controls:
            raise ValueError("control already registered")
        self._controls[control.control_id] = control

    def add_evidence(self, evidence: Evidence) -> None:
        if evidence.control_id not in self._controls:
            raise KeyError("control not found")
        key = (evidence.tenant_id, evidence.evidence_id)
        if key in self._evidence:
            raise ValueError("evidence already exists")
        self._evidence[key] = evidence

    def attest(self, attestation: Attestation) -> None:
        if attestation.control_id not in self._controls:
            raise KeyError("control not found")
        for evidence_id in attestation.evidence_ids:
            evidence = self._evidence.get((attestation.tenant_id, evidence_id))
            if evidence is None or evidence.control_id != attestation.control_id or not evidence.is_current():
                raise ValueError("attestation references missing or non-current evidence")
        self._attestations[(attestation.tenant_id, attestation.control_id)] = attestation

    def posture(self, tenant_id: str, framework: ComplianceFramework, *, now: datetime | None = None) -> CompliancePosture:
        moment = now or datetime.now(timezone.utc)
        if moment.tzinfo is None or moment.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        controls: dict[str, ControlStatus] = {}
        for control_id, control in self._controls.items():
            if control.framework is not framework:
                continue
            attestation = self._attestations.get((tenant_id, control_id))
            controls[control_id] = attestation.status if attestation else ControlStatus.NOT_ASSESSED
        tenant_evidence = [e for (tenant, _), e in self._evidence.items() if tenant == tenant_id]
        current = sum(e.is_current(now=moment) for e in tenant_evidence)
        expired = sum(not e.is_current(now=moment) for e in tenant_evidence)
        return CompliancePosture(tenant_id, framework, moment, controls, current, expired)

    def audit_pack(self, tenant_id: str, framework: ComplianceFramework, *, now: datetime | None = None) -> bytes:
        posture = self.posture(tenant_id, framework, now=now)
        evidence = [
            e for (tenant, _), e in self._evidence.items()
            if tenant == tenant_id and e.control_id in posture.controls
        ]
        payload = {
            "tenant_id": tenant_id,
            "framework": framework.value,
            "generated_at": posture.generated_at.isoformat(),
            "score": posture.score,
            "audit_ready": posture.audit_ready,
            "controls": dict(sorted((k, v.value) for k, v in posture.controls.items())),
            "evidence": [
                {
                    "evidence_id": e.evidence_id,
                    "control_id": e.control_id,
                    "type": e.evidence_type,
                    "source_uri": e.source_uri,
                    "content_digest": e.content_digest,
                    "status": e.status.value,
                }
                for e in sorted(evidence, key=lambda item: item.evidence_id)
            ],
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def _is_sha256(value: str) -> bool:
    return len(value) == 71 and value.startswith("sha256:") and all(c in "0123456789abcdef" for c in value[7:])
