import pytest

from fde_platform.evaluation.release import (
    EvaluationMetric,
    EvaluationRun,
    EvaluationStatus,
    PromotionDecision,
    ReleasePolicy,
    assess_release,
    collect_evidence,
    compare_runs,
    require_promotion,
    rollback_required,
)


def make_run(*, passed=99, total=100, security=True, status=EvaluationStatus.PASSED, version="2", cost=1.05, latency=1.10):
    return EvaluationRun(
        run_id=f"run-{version}",
        tenant_id="tenant-a",
        target_id="agent-a",
        version=version,
        status=status,
        metrics=(
            EvaluationMetric("quality", 0.98, passed / total, minimum=0.95),
            EvaluationMetric("cost", 1.0, cost, maximum=1.20),
            EvaluationMetric("latency", 1.0, latency, maximum=1.20),
        ),
        baseline_passed=99,
        baseline_total=100,
        current_passed=passed,
        current_total=total,
        evidence_ids=(f"evidence-{version}",),
        security_passed=security,
    )


def test_promotes_only_when_all_gates_pass():
    assessment = assess_release(make_run())
    assert assessment.decision is PromotionDecision.PROMOTE
    require_promotion(assessment)
    assert not rollback_required(assessment)


def test_security_failure_requires_rollback():
    assessment = assess_release(make_run(security=False))
    assert assessment.decision is PromotionDecision.ROLLBACK
    assert rollback_required(assessment)
    assert "security_evaluation_failed" in assessment.reasons
    with pytest.raises(RuntimeError):
        require_promotion(assessment)


def test_blocks_quality_threshold_failure():
    assessment = assess_release(make_run(passed=90))
    assert assessment.decision is PromotionDecision.BLOCK
    assert "minimum_pass_rate_not_met" in assessment.reasons


def test_blocks_non_passed_status_even_with_good_scores():
    assessment = assess_release(make_run(status=EvaluationStatus.FAILED))
    assert assessment.decision is PromotionDecision.BLOCK
    assert "evaluation_status_not_passed" in assessment.reasons


def test_blocks_cost_and_latency_regression():
    assessment = assess_release(make_run(cost=1.25, latency=1.30))
    assert assessment.decision is PromotionDecision.BLOCK
    assert "cost_regression_limit_exceeded" in assessment.reasons
    assert "latency_regression_limit_exceeded" in assessment.reasons


def test_evidence_is_required_and_deterministically_deduplicated():
    with pytest.raises(ValueError):
        make_run(version="")
    first = make_run(version="a")
    second = make_run(version="b")
    assert collect_evidence([first, second, first]) == ("evidence-a", "evidence-b")


def test_compare_runs_is_tenant_and_target_scoped():
    current = make_run(version="old")
    candidate = make_run(version="new")
    assert compare_runs(current, candidate)["quality"] == 0.0

    other = EvaluationRun(
        run_id="other", tenant_id="tenant-b", target_id="agent-a", version="1",
        status=EvaluationStatus.PASSED, metrics=current.metrics,
        baseline_passed=99, baseline_total=100, current_passed=99, current_total=100,
        evidence_ids=("evidence-other",), security_passed=True,
    )
    with pytest.raises(ValueError):
        compare_runs(current, other)


def test_policy_validation_is_fail_closed():
    with pytest.raises(ValueError):
        ReleasePolicy(minimum_pass_rate=1.1)
    with pytest.raises(ValueError):
        ReleasePolicy(drift_alpha=1.0)
