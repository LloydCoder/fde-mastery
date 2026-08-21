from fde_platform.fde.engagement import (
    AcceptanceCriterion,
    EngagementEvidence,
    EngagementStage,
    EvidenceKind,
    FDEEngagement,
    MetricDefinition,
)
from fde_platform.fde.workflow import FDEWorkflow, FDEWorkflowError


def make_engagement() -> FDEEngagement:
    return FDEEngagement(
        tenant_id="tenant-a",
        client_id="client-a",
        project_id="project-a",
        domain_id="logistics",
        workflow_id="shipment-exception-resolution",
        owner_id="fde-1",
        objective="Reduce manual shipment exception handling time",
        metrics=(
            MetricDefinition(
                metric_id="resolution-time",
                name="Resolution time",
                unit="minutes",
                baseline_value=60,
                target_value=20,
                measurement_method="median production resolution time",
            ),
        ),
        acceptance_criteria=(
            AcceptanceCriterion(
                criterion_id="requirements",
                description="Customer requirements are documented",
                evidence_kind=EvidenceKind.REQUIREMENT,
            ),
            AcceptanceCriterion(
                criterion_id="baseline",
                description="Baseline measurement is reproducible",
                evidence_kind=EvidenceKind.BASELINE,
            ),
            AcceptanceCriterion(
                criterion_id="evaluation",
                description="Evaluation results meet the agreed gate",
                evidence_kind=EvidenceKind.EVALUATION,
            ),
            AcceptanceCriterion(
                criterion_id="pilot-approval",
                description="Customer approves controlled pilot",
                evidence_kind=EvidenceKind.APPROVAL,
            ),
            AcceptanceCriterion(
                criterion_id="deployment",
                description="Deployment evidence exists",
                evidence_kind=EvidenceKind.DEPLOYMENT,
            ),
        ),
    )


def evidence(kind: EvidenceKind, suffix: str, criterion_id: str | None = None) -> EngagementEvidence:
    return EngagementEvidence(
        evidence_id=f"{kind.value}-{suffix}",
        kind=kind,
        reference=f"evidence://{kind.value}/{suffix}",
        criterion_id=criterion_id,
    )


def test_lifecycle_requires_evidence_before_advance() -> None:
    engagement = make_engagement()
    try:
        engagement.advance(EngagementStage.WORKFLOW_MAPPING)
    except ValueError as exc:
        assert "requirements" in str(exc)
    else:
        raise AssertionError("missing requirement evidence must block transition")

    engagement.add_evidence(evidence(EvidenceKind.REQUIREMENT, "001", "requirements"))
    transition = engagement.advance(EngagementStage.WORKFLOW_MAPPING)
    assert transition.next_stage is EngagementStage.WORKFLOW_MAPPING


def test_invalid_transition_fails_closed() -> None:
    engagement = make_engagement()
    try:
        engagement.advance(EngagementStage.PRODUCTION)
    except ValueError as exc:
        assert "invalid engagement transition" in str(exc)
    else:
        raise AssertionError("invalid transition must fail closed")


def test_production_gate_requires_approval_and_deployment_evidence() -> None:
    engagement = make_engagement()
    for kind, criterion in (
        (EvidenceKind.REQUIREMENT, "requirements"),
        (EvidenceKind.BASELINE, "baseline"),
        (EvidenceKind.DESIGN, None),
        (EvidenceKind.EVALUATION, "evaluation"),
    ):
        engagement.add_evidence(evidence(kind, "001", criterion))
    engagement.stage = EngagementStage.PILOT
    workflow = FDEWorkflow(engagement)

    try:
        workflow.validate_stage(EngagementStage.PRODUCTION)
    except FDEWorkflowError as exc:
        assert "deployment" in str(exc)
    else:
        raise AssertionError("production must require deployment evidence")

    engagement.add_evidence(evidence(EvidenceKind.DEPLOYMENT, "001", "deployment"))
    try:
        workflow.validate_stage(EngagementStage.PRODUCTION)
    except FDEWorkflowError as exc:
        assert "approval" in str(exc)
    else:
        raise AssertionError("production must require explicit approval evidence")

    engagement.add_evidence(evidence(EvidenceKind.APPROVAL, "001", "pilot-approval"))
    workflow.validate_stage(EngagementStage.PRODUCTION)


def test_compiles_to_existing_durable_workflow_contract() -> None:
    engagement = make_engagement()
    workflow = FDEWorkflow(engagement)
    definition = workflow.to_workflow_definition(version="1.0.0")
    assert definition.workflow_id == engagement.workflow_id
    assert definition.steps[0].activity == "fde.engagement.discovery"
    assert definition.steps[-1].activity == "fde.engagement.retired"


def test_promotion_report_is_tenant_scoped() -> None:
    engagement = make_engagement()
    report = FDEWorkflow(engagement).promotion_report()
    assert report["tenant_id"] == "tenant-a"
    assert report["stage"] == "discovery"
    assert report["ready"] is False
    assert report["blocking_reasons"]
