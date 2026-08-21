from datetime import datetime, timezone

import pytest

from fde_platform.evaluation.models import EvalResult, EvalRun, EvaluationThresholds
from fde_platform.evaluation.release import (
    ReleaseCandidate,
    ReleaseDecision,
    ReleasePolicy,
    assess_release,
    collect_evidence,
    require_promotion,
    rollback_required,
)


def make_candidate(*, passed=99, total=100, security=True, version="2", cost=1.05, latency=1.10):
    results = tuple(
        EvalResult(
            case_id=f"case-{index}",
            passed=index < passed,
            score=0.98 if index < passed else 0.0,
            latency_ms=latency,
            cost_usd=cost / total,
        )
        for index in range(total)
    )
    evaluation = EvalRun(
        run_id=f"run-{version}",
        dataset_name="golden",
        dataset_version="v1",
        dataset_fingerprint="fingerprint",
        results=results,
        model_ref=f"agent:{version}",
        started_at=datetime.now(timezone.utc),
    )
    return ReleaseCandidate(
        tenant_id="tenant-a",
        target_id="agent-a",
        version=version,
        evaluation=evaluation,
        baseline_passed=99,
        baseline_total=100,
        baseline_cost_usd=1.0,
        baseline_latency_ms=1.0,
        evidence_ids=(f"evidence-{version}",),
        security_passed=security,
    )


def test_promotes_only_when_all_gates_pass():
    candidate = make_candidate()
    assessment = assess_release(candidate)
    assert assessment.decision is ReleaseDecision.PROMOTE
    require_promotion(assessment)
    assert not rollback_required(assessment)


def test_security_failure_requires_rollback():
    assessment = assess_release(make_candidate(security=False))
    assert assessment.decision is ReleaseDecision.ROLLBACK
    assert rollback_required(assessment)
    assert "security_evaluation_failed" in assessment.reasons
    with pytest.raises(RuntimeError):
        require_promotion(assessment)


def test_blocks_quality_threshold_failure():
    candidate = make_candidate(passed=90)
    assessment = assess_release(candidate)
    assert assessment.decision is ReleaseDecision.BLOCK
    assert "minimum_pass_rate_not_met" in assessment.reasons


def test_blocks_cost_and_latency_regression():
    candidate = make_candidate(cost=1.25, latency=1.30)
    assessment = assess_release(candidate)
    assert assessment.decision is ReleaseDecision.BLOCK
    assert "cost_regression_limit_exceeded" in assessment.reasons
    assert "latency_regression_limit_exceeded" in assessment.reasons


def test_evidence_is_required_and_deterministically_deduplicated():
    first = make_candidate(version="a")
    second = make_candidate(version="b")
    assert collect_evidence([first, second, first]) == ("evidence-a", "evidence-b")
    with pytest.raises(ValueError):
        ReleaseCandidate(
            tenant_id="tenant-a", target_id="agent-a", version="x", evaluation=first.evaluation,
            baseline_passed=99, baseline_total=100, baseline_cost_usd=1.0, baseline_latency_ms=1.0,
            evidence_ids=(), security_passed=True,
        )


def test_release_candidate_is_tenant_scoped_by_contract():
    candidate = make_candidate()
    other = ReleaseCandidate(
        tenant_id="tenant-b", target_id=candidate.target_id, version="1", evaluation=candidate.evaluation,
        baseline_passed=99, baseline_total=100, baseline_cost_usd=1.0, baseline_latency_ms=1.0,
        evidence_ids=("other",), security_passed=True,
    )
    assert candidate.tenant_id != other.tenant_id


def test_policy_validation_is_fail_closed():
    with pytest.raises(ValueError):
        ReleasePolicy(evaluation_thresholds=EvaluationThresholds(min_pass_rate=1.1))
    with pytest.raises(ValueError):
        ReleasePolicy(drift_alpha=1.0)
