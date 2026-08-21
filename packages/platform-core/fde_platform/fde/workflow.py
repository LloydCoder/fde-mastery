"""FDE lifecycle workflow definitions and promotion gates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from fde_platform.fde.engagement import EngagementStage, FDEEngagement
from fde_platform.workflow.models import WorkflowDefinition, WorkflowStep


@dataclass(frozen=True, slots=True)
class FDEStageGate:
    """Required controls for a lifecycle stage."""

    stage: EngagementStage
    required_evidence: tuple[str, ...]
    requires_human_approval: bool = False


_STAGE_GATES: tuple[FDEStageGate, ...] = (
    FDEStageGate(EngagementStage.DISCOVERY, ("requirement",)),
    FDEStageGate(EngagementStage.WORKFLOW_MAPPING, ("requirement",)),
    FDEStageGate(EngagementStage.VALUE_CASE, ("baseline",)),
    FDEStageGate(EngagementStage.ARCHITECTURE, ("design",)),
    FDEStageGate(EngagementStage.BUILD, ("design",)),
    FDEStageGate(EngagementStage.EVALUATION, ("evaluation",)),
    FDEStageGate(EngagementStage.PILOT, ("evaluation", "approval"), True),
    FDEStageGate(EngagementStage.SHADOW, ("evaluation", "approval"), True),
    FDEStageGate(EngagementStage.PRODUCTION, ("deployment", "approval"), True),
    FDEStageGate(EngagementStage.OPERATE, ("operations",)),
    FDEStageGate(EngagementStage.TRANSFER, ("handoff", "operations"), True),
    FDEStageGate(EngagementStage.RETIRED, ("operations",)),
)


class FDEWorkflowError(ValueError):
    """Raised when an FDE workflow cannot be promoted safely."""


class FDEWorkflow:
    """Immutable workflow projection over an FDE engagement.

    This object creates a provider-neutral durable workflow definition. The
    existing workflow runtime remains the only component allowed to execute
    activities; this layer only defines lifecycle semantics and gates.
    """

    def __init__(self, engagement: FDEEngagement) -> None:
        self.engagement = engagement

    @staticmethod
    def gates() -> tuple[FDEStageGate, ...]:
        return _STAGE_GATES

    @staticmethod
    def gate_for(stage: EngagementStage) -> FDEStageGate:
        return next(gate for gate in _STAGE_GATES if gate.stage == stage)

    def validate_stage(self, stage: EngagementStage) -> None:
        gate = self.gate_for(stage)
        evidence_kinds = {item.kind.value for item in self.engagement.evidence}
        missing = [kind for kind in gate.required_evidence if kind not in evidence_kinds]
        if missing:
            raise FDEWorkflowError(
                f"stage {stage.value} requires evidence: {', '.join(missing)}"
            )
        if gate.requires_human_approval and "approval" not in evidence_kinds:
            raise FDEWorkflowError(f"stage {stage.value} requires explicit human approval evidence")

    def to_workflow_definition(self, *, version: str = "1.0.0") -> WorkflowDefinition:
        """Compile the lifecycle into the existing durable workflow contract."""
        if not version.strip():
            raise FDEWorkflowError("workflow version is required")
        steps = tuple(
            WorkflowStep(
                step_id=stage.value,
                activity=f"fde.engagement.{stage.value}",
            )
            for stage in EngagementStage
        )
        return WorkflowDefinition(
            workflow_id=self.engagement.workflow_id,
            version=version,
            steps=steps,
        )

    def promotion_report(self) -> Mapping[str, object]:
        """Return deterministic, audit-friendly readiness information."""
        report: dict[str, object] = {
            "engagement_id": str(self.engagement.engagement_id),
            "tenant_id": self.engagement.tenant_id,
            "stage": self.engagement.stage.value,
            "status": self.engagement.status.value,
            "ready": True,
            "blocking_reasons": [],
        }
        try:
            self.validate_stage(self.engagement.stage)
        except FDEWorkflowError as exc:
            report["ready"] = False
            report["blocking_reasons"] = [str(exc)]
        return report
