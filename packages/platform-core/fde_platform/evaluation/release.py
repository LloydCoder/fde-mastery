"""Continuous evaluation and release intelligence.

This module turns existing evaluation primitives into a deterministic promotion decision.
It does not execute deployments; callers must connect the result to the existing deployment
and policy boundaries. Missing evidence fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping

from evaluation.drift import DriftResult, detect_drift


class EvaluationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class PromotionDecision(str, Enum):
    PROMOTE = "promote"
    BLOCK = "block"
    ROLLBACK = "rollback"


@dataclass(frozen=True, slots=True)
class EvaluationMetric:
    name: str
    baseline: float
    current: float
    minimum: float | None = None
    maximum: float | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("metric name is required")
        if not all(value == value for value in (self.baseline, self.current)):
            raise ValueError("metric values must not be NaN")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("minimum cannot exceed maximum")
        if self.baseline < 0 or self.current < 0:
            raise ValueError("metric values cannot be negative")

    @property
    def passed(self) -> bool:
        return (self.minimum is None or self.current >= self.minimum) and (
            self.maximum is None or self.current <= self.maximum
        )

    @property
    def regression_ratio(self) -> float:
        if self.baseline == 0:
            return 0.0 if self.current == 0 else float("inf")
        return (self.current - self.baseline) / self.baseline


@dataclass(frozen=True, slots=True)
class EvaluationRun:
    run_id: str
    tenant_id: str
    target_id: str
    version: str
    status: EvaluationStatus
    metrics: tuple[EvaluationMetric, ...]
    baseline_passed: int
    baseline_total: int
    current_passed: int
    current_total: int
    evidence_ids: tuple[str, ...] = ()
    security_passed: bool = False
    evaluator_version: str = "1"

    def __post_init__(self) -> None:
        if not self.run_id.strip() or not self.tenant_id.strip() or not self.target_id.strip() or not self.version.strip():
            raise ValueError("run, tenant, target and version identifiers are required")
        for passed, total in ((self.baseline_passed, self.baseline_total), (self.current_passed, self.current_total)):
            if total <= 0 or not 0 <= passed <= total:
                raise ValueError("evaluation counts must be valid and non-empty")
        if not self.evidence_ids:
            raise ValueError("evaluation evidence is required")
        if not self.evaluator_version.strip():
            raise ValueError("evaluator version is required")


@dataclass(frozen=True, slots=True)
class ReleasePolicy:
    minimum_pass_rate: float = 0.95
    maximum_cost_regression: float = 0.20
    maximum_latency_regression: float = 0.20
    catastrophic_pass_rate: float = 0.80
    drift_alpha: float = 0.01
    minimum_drift_drop: float = 0.05
    require_security_pass: bool = True

    def __post_init__(self) -> None:
        if not 0 <= self.minimum_pass_rate <= 1:
            raise ValueError("minimum_pass_rate must be between 0 and 1")
        if not 0 <= self.catastrophic_pass_rate <= self.minimum_pass_rate:
            raise ValueError("catastrophic_pass_rate must not exceed minimum_pass_rate")
        if self.maximum_cost_regression < 0 or self.maximum_latency_regression < 0:
            raise ValueError("regression limits cannot be negative")
        if not 0 < self.drift_alpha < 1 or self.minimum_drift_drop < 0:
            raise ValueError("invalid drift policy")


@dataclass(frozen=True, slots=True)
class ReleaseAssessment:
    decision: PromotionDecision
    reasons: tuple[str, ...]
    drift: DriftResult
    failed_metrics: tuple[str, ...]
    evidence_ids: tuple[str, ...]


def _regression_reasons(run: EvaluationRun, policy: ReleasePolicy) -> list[str]:
    reasons: list[str] = []
    for metric in run.metrics:
        name = metric.name.lower()
        if "cost" in name and metric.regression_ratio > policy.maximum_cost_regression:
            reasons.append("cost_regression_limit_exceeded")
        if "latency" in name and metric.regression_ratio > policy.maximum_latency_regression:
            reasons.append("latency_regression_limit_exceeded")
    return reasons


def assess_release(run: EvaluationRun, policy: ReleasePolicy = ReleasePolicy()) -> ReleaseAssessment:
    """Return a fail-closed promotion decision for an immutable evaluation run."""
    reasons: list[str] = []
    failed_metrics: list[str] = [metric.name for metric in run.metrics if not metric.passed]
    current_rate = run.current_passed / run.current_total
    drift = detect_drift(
        run.baseline_passed,
        run.baseline_total,
        run.current_passed,
        run.current_total,
        alpha=policy.drift_alpha,
        minimum_drop=policy.minimum_drift_drop,
    )

    if run.status is not EvaluationStatus.PASSED:
        reasons.append("evaluation_status_not_passed")
    if current_rate < policy.minimum_pass_rate:
        reasons.append("minimum_pass_rate_not_met")
    if failed_metrics:
        reasons.append("metric_threshold_failed")
    if drift.drifted:
        reasons.append("statistically_significant_regression")
    if policy.require_security_pass and not run.security_passed:
        reasons.append("security_evaluation_failed")
    reasons.extend(_regression_reasons(run, policy))

    catastrophic = current_rate < policy.catastrophic_pass_rate or (
        not run.security_passed and policy.require_security_pass
    )
    if catastrophic:
        decision = PromotionDecision.ROLLBACK if reasons else PromotionDecision.PROMOTE
    else:
        decision = PromotionDecision.PROMOTE if not reasons else PromotionDecision.BLOCK
    return ReleaseAssessment(decision, tuple(dict.fromkeys(reasons)), drift, tuple(failed_metrics), run.evidence_ids)


def compare_runs(current: EvaluationRun, candidate: EvaluationRun) -> Mapping[str, float]:
    """Compare two runs only when they belong to the same tenant and target."""
    if current.tenant_id != candidate.tenant_id or current.target_id != candidate.target_id:
        raise ValueError("runs must share tenant and target")
    old = {metric.name: metric.current for metric in current.metrics}
    new = {metric.name: metric.current for metric in candidate.metrics}
    names = old.keys() & new.keys()
    return {name: new[name] - old[name] for name in names}


def require_promotion(assessment: ReleaseAssessment) -> None:
    if assessment.decision is not PromotionDecision.PROMOTE:
        raise RuntimeError("release promotion blocked: " + ", ".join(assessment.reasons))


def rollback_required(assessment: ReleaseAssessment) -> bool:
    return assessment.decision is PromotionDecision.ROLLBACK


def collect_evidence(runs: Iterable[EvaluationRun]) -> tuple[str, ...]:
    """Return deterministic, de-duplicated evidence IDs in evaluation order."""
    seen: set[str] = set()
    result: list[str] = []
    for run in runs:
        for evidence_id in run.evidence_ids:
            if evidence_id not in seen:
                seen.add(evidence_id)
                result.append(evidence_id)
    return tuple(result)
