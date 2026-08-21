"""Provider-neutral FDE engagement lifecycle contracts.

The lifecycle models the delivery and operating loop around a production AI
workflow. It deliberately does not execute side effects; execution remains the
responsibility of the existing workflow, policy, tool, model and approval
planes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EngagementStage(str, Enum):
    DISCOVERY = "discovery"
    WORKFLOW_MAPPING = "workflow_mapping"
    VALUE_CASE = "value_case"
    ARCHITECTURE = "architecture"
    BUILD = "build"
    EVALUATION = "evaluation"
    PILOT = "pilot"
    SHADOW = "shadow"
    PRODUCTION = "production"
    OPERATE = "operate"
    TRANSFER = "transfer"
    RETIRED = "retired"


class EngagementStatus(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EvidenceKind(str, Enum):
    REQUIREMENT = "requirement"
    BASELINE = "baseline"
    DESIGN = "design"
    EVALUATION = "evaluation"
    APPROVAL = "approval"
    DEPLOYMENT = "deployment"
    OPERATIONS = "operations"
    HANDOFF = "handoff"


class MetricDefinition(BaseModel):
    """A measurable value metric with an immutable baseline."""

    model_config = ConfigDict(frozen=True)

    metric_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    unit: str = Field(min_length=1, max_length=64)
    baseline_value: float
    target_value: float
    measurement_method: str = Field(min_length=1, max_length=512)

    @field_validator("metric_id", "name", "unit", "measurement_method")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class AcceptanceCriterion(BaseModel):
    """Explicit condition required before an engagement stage can advance."""

    model_config = ConfigDict(frozen=True)

    criterion_id: str = Field(min_length=1, max_length=128)
    stage: EngagementStage
    description: str = Field(min_length=1, max_length=512)
    evidence_kind: EvidenceKind
    required: bool = True


class EngagementEvidence(BaseModel):
    """Reference to evidence; payloads stay outside the lifecycle contract."""

    model_config = ConfigDict(frozen=True)

    evidence_id: str = Field(min_length=1, max_length=128)
    kind: EvidenceKind
    reference: str = Field(min_length=1, max_length=1024)
    checksum: str | None = Field(default=None, max_length=128)
    criterion_id: str | None = Field(default=None, max_length=128)


@dataclass(frozen=True, slots=True)
class StageTransition:
    """Auditable transition result without performing external side effects."""

    engagement_id: UUID
    previous_stage: EngagementStage
    next_stage: EngagementStage
    required_criteria: tuple[str, ...]


_ALLOWED_TRANSITIONS: dict[EngagementStage, frozenset[EngagementStage]] = {
    EngagementStage.DISCOVERY: frozenset({EngagementStage.WORKFLOW_MAPPING}),
    EngagementStage.WORKFLOW_MAPPING: frozenset({EngagementStage.VALUE_CASE}),
    EngagementStage.VALUE_CASE: frozenset({EngagementStage.ARCHITECTURE}),
    EngagementStage.ARCHITECTURE: frozenset({EngagementStage.BUILD}),
    EngagementStage.BUILD: frozenset({EngagementStage.EVALUATION}),
    EngagementStage.EVALUATION: frozenset({EngagementStage.PILOT}),
    EngagementStage.PILOT: frozenset({EngagementStage.SHADOW, EngagementStage.PRODUCTION}),
    EngagementStage.SHADOW: frozenset({EngagementStage.PRODUCTION}),
    EngagementStage.PRODUCTION: frozenset({EngagementStage.OPERATE}),
    EngagementStage.OPERATE: frozenset({EngagementStage.TRANSFER, EngagementStage.RETIRED}),
    EngagementStage.TRANSFER: frozenset({EngagementStage.RETIRED}),
    EngagementStage.RETIRED: frozenset(),
}


class FDEEngagement(BaseModel):
    """Tenant-scoped FDE engagement with explicit value and evidence gates."""

    model_config = ConfigDict(validate_assignment=True)

    engagement_id: UUID = Field(default_factory=uuid4)
    tenant_id: str = Field(min_length=1, max_length=128)
    client_id: str = Field(min_length=1, max_length=128)
    project_id: str = Field(min_length=1, max_length=128)
    domain_id: str = Field(min_length=1, max_length=128)
    workflow_id: str = Field(min_length=1, max_length=128)
    owner_id: str = Field(min_length=1, max_length=128)
    stage: EngagementStage = EngagementStage.DISCOVERY
    status: EngagementStatus = EngagementStatus.ACTIVE
    objective: str = Field(min_length=1, max_length=1024)
    metrics: tuple[MetricDefinition, ...] = ()
    acceptance_criteria: tuple[AcceptanceCriterion, ...] = ()
    evidence: tuple[EngagementEvidence, ...] = ()
    attributes: Mapping[str, str] = Field(default_factory=dict)

    @field_validator("tenant_id", "client_id", "project_id", "domain_id", "workflow_id", "owner_id", "objective")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value

    def add_evidence(self, evidence: EngagementEvidence) -> None:
        if any(item.evidence_id == evidence.evidence_id for item in self.evidence):
            raise ValueError("evidence_id already exists")
        self.evidence = (*self.evidence, evidence)

    def _missing_required_criteria(self, target: EngagementStage) -> tuple[str, ...]:
        required = tuple(
            criterion
            for criterion in self.acceptance_criteria
            if criterion.required and criterion.stage is target
        )
        missing: list[str] = []
        for criterion in required:
            satisfied = any(
                item.kind is criterion.evidence_kind
                and (item.criterion_id is None or item.criterion_id == criterion.criterion_id)
                for item in self.evidence
            )
            if not satisfied:
                missing.append(criterion.criterion_id)
        return tuple(missing)

    def can_advance(self, target: EngagementStage) -> bool:
        if self.status != EngagementStatus.ACTIVE:
            return False
        if target not in _ALLOWED_TRANSITIONS[self.stage]:
            return False
        return not self._missing_required_criteria(target)

    def advance(self, target: EngagementStage) -> StageTransition:
        if self.status != EngagementStatus.ACTIVE:
            raise ValueError("only active engagements can advance")
        if target not in _ALLOWED_TRANSITIONS[self.stage]:
            raise ValueError(f"invalid engagement transition: {self.stage.value} -> {target.value}")
        missing = self._missing_required_criteria(target)
        if missing:
            raise ValueError(f"required evidence is missing: {', '.join(missing)}")
        previous = self.stage
        self.stage = target
        if target == EngagementStage.RETIRED:
            self.status = EngagementStatus.COMPLETED
        return StageTransition(self.engagement_id, previous, target, missing)

    def block(self) -> None:
        if self.status in {EngagementStatus.COMPLETED, EngagementStatus.CANCELLED}:
            raise ValueError("terminal engagement cannot be blocked")
        self.status = EngagementStatus.BLOCKED

    def resume(self) -> None:
        if self.status != EngagementStatus.BLOCKED:
            raise ValueError("engagement is not blocked")
        self.status = EngagementStatus.ACTIVE

    def cancel(self) -> None:
        if self.status == EngagementStatus.COMPLETED:
            raise ValueError("completed engagement cannot be cancelled")
        self.status = EngagementStatus.CANCELLED
