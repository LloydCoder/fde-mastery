"""Continuous evaluation and release intelligence built on the platform evaluation plane.

The release layer composes existing immutable EvalRun/EvaluationThresholds contracts with
security, drift, evidence and regression controls. It never deploys or authorizes actions.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from evaluation.drift import DriftResult, detect_drift

from .models import EvalRun, EvaluationThresholds


class ReleaseDecision(StrEnum):
    PROMOTE = "promote"
    BLOCK = "block"
    ROLLBACK = "rollback"


@dataclass(frozen=True, slots=True)
class ReleaseCandidate:
    tenant_id: str
    target_id: str
    version: str
    evaluation: EvalRun
    baseline_passed: int
    baseline_total: int
    baseline_cost_usd: float
    baseline_latency_ms: float
    evidence_ids: tuple[str, ...]
    security_passed: bool
    evaluator_version: str = "1"

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.target_id.strip() or not self.version.strip():
            raise ValueError("tenant, target and version identifiers are required")
        if self.baseline_total <= 0 or not 0 <= self.baseline_passed <= self.baseline_total:
            raise ValueError("baseline evaluation counts are invalid")
        if self.baseline_cost_usd < 0 or self.baseline_latency_ms < 0:
            raise ValueError("baseline measurements cannot be negative")
        if not self.evidence_ids:
            raise ValueError("evaluation evidence is required")
        if not self.evaluator_version.strip():
            raise ValueError("evaluator version is required")


@dataclass(frozen=True, slots=True)
class ReleasePolicy:
    evaluation_thresholds: EvaluationThresholds = EvaluationThresholds()
    maximum_cost_regression: float = 0.20
    maximum_latency_regression: float = 0.20
    catastrophic_pass_rate: float = 0.80
    drift_alpha: float = 0.01
    minimum_drift_drop: float = 0.05
    require_security_pass: bool = True

    def __post_init__(self) -> None:
        if self.maximum_cost_regression < 0 or self.maximum_latency_regression < 0:
            raise ValueError("regression limits cannot be negative")
        if not 0 <= self.catastrophic_pass_rate <= self.evaluation_thresholds.min_pass_rate:
            raise ValueError("catastrophic_pass_rate must not exceed minimum pass rate")
        if not 0 < self.drift_alpha < 1 or self.minimum_drift_drop < 0:
            raise ValueError("invalid drift policy")


@dataclass(frozen=True, slots=True)
class ReleaseAssessment:
    decision: ReleaseDecision
    reasons: tuple[str, ...]
    drift: DriftResult
    evidence_ids: tuple[str, ...]


def _relative_regression(baseline: float, current: float) -> float:
    if baseline == 0:
        return 0.0 if current == 0 else float("inf")
    return (current - baseline) / baseline


def assess_release(candidate: ReleaseCandidate, policy: ReleasePolicy = ReleasePolicy()) -> ReleaseAssessment:
    """Return a fail-closed release decision for one immutable evaluation candidate."""
    evaluation = candidate.evaluation
    reasons: list[str] = []
    current_passed = sum(result.passed for result in evaluation.results)
    drift = detect_drift(
        candidate.baseline_passed,
        candidate.baseline_total,
        current_passed,
        len(evaluation.results),
        alpha=policy.drift_alpha,
        minimum_drop=policy.minimum_drift_drop,
    )

    if evaluation.pass_rate < policy.evaluation_thresholds.min_pass_rate:
        reasons.append("minimum_pass_rate_not_met")
    if evaluation.mean_score < policy.evaluation_thresholds.min_mean_score:
        reasons.append("minimum_mean_score_not_met")
    if policy.evaluation_thresholds.max_cost_usd is not None and evaluation.total_cost_usd > policy.evaluation_thresholds.max_cost_usd:
        reasons.append("maximum_cost_threshold_exceeded")
    if policy.evaluation_thresholds.max_mean_latency_ms is not None and evaluation.mean_latency_ms > policy.evaluation_thresholds.max_mean_latency_ms:
        reasons.append("maximum_latency_threshold_exceeded")
    if drift.drifted:
        reasons.append("statistically_significant_regression")
    if _relative_regression(candidate.baseline_cost_usd, evaluation.total_cost_usd) > policy.maximum_cost_regression:
        reasons.append("cost_regression_limit_exceeded")
    if _relative_regression(candidate.baseline_latency_ms, evaluation.mean_latency_ms) > policy.maximum_latency_regression:
        reasons.append("latency_regression_limit_exceeded")
    if policy.require_security_pass and not candidate.security_passed:
        reasons.append("security_evaluation_failed")

    if not reasons:
        return ReleaseAssessment(ReleaseDecision.PROMOTE, (), drift, candidate.evidence_ids)

    catastrophic = evaluation.pass_rate < policy.catastrophic_pass_rate or (
        policy.require_security_pass and not candidate.security_passed
    )
    decision = ReleaseDecision.ROLLBACK if catastrophic else ReleaseDecision.BLOCK
    return ReleaseAssessment(decision, tuple(dict.fromkeys(reasons)), drift, candidate.evidence_ids)


def require_promotion(assessment: ReleaseAssessment) -> None:
    if assessment.decision is not ReleaseDecision.PROMOTE:
        raise RuntimeError("release promotion blocked: " + ", ".join(assessment.reasons))


def rollback_required(assessment: ReleaseAssessment) -> bool:
    return assessment.decision is ReleaseDecision.ROLLBACK


def collect_evidence(candidates: Iterable[ReleaseCandidate]) -> tuple[str, ...]:
    """Return deterministic, de-duplicated evidence IDs in candidate order."""
    seen: set[str] = set()
    result: list[str] = []
    for candidate in candidates:
        for evidence_id in candidate.evidence_ids:
            if evidence_id not in seen:
                seen.add(evidence_id)
                result.append(evidence_id)
    return tuple(result)
