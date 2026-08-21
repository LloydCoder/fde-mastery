"""Customer value realization contracts for FDE engagements.

The value plane turns an engagement objective into measurable, tenant-scoped outcomes.
It deliberately separates *observed evidence* from calculated value so customer claims
remain auditable and never become synthetic success metrics.

The module is framework-agnostic and does not emit telemetry itself. Adapters may map the
stable metric identifiers to OpenTelemetry instruments while keeping high-cardinality IDs
out of metric attributes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from hashlib import sha256
from math import isfinite
from typing import Iterable, Mapping


class MetricKind(StrEnum):
    COUNT = "count"
    RATE = "rate"
    DURATION = "duration"
    CURRENCY = "currency"
    RATIO = "ratio"


class Direction(StrEnum):
    INCREASE = "increase"
    DECREASE = "decrease"
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class EvidenceStatus(StrEnum):
    OBSERVED = "observed"
    VERIFIED = "verified"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ValueMetric:
    """Bounded definition of a customer outcome metric."""

    metric_id: str
    name: str
    kind: MetricKind
    unit: str
    direction: Direction
    description: str = ""
    lower_bound: float | None = None
    upper_bound: float | None = None

    def __post_init__(self) -> None:
        for value, label in ((self.metric_id, "metric_id"), (self.name, "name"), (self.unit, "unit")):
            if not value or len(value) > 128:
                raise ValueError(f"{label} must be 1-128 characters")
        if len(self.description) > 1024:
            raise ValueError("description must be <= 1024 characters")
        if self.lower_bound is not None and not isfinite(self.lower_bound):
            raise ValueError("lower_bound must be finite")
        if self.upper_bound is not None and not isfinite(self.upper_bound):
            raise ValueError("upper_bound must be finite")
        if self.lower_bound is not None and self.upper_bound is not None and self.lower_bound > self.upper_bound:
            raise ValueError("lower_bound cannot exceed upper_bound")

    def validate_value(self, value: float) -> float:
        if not isfinite(value):
            raise ValueError("metric value must be finite")
        if self.lower_bound is not None and value < self.lower_bound:
            raise ValueError("metric value is below the configured lower bound")
        if self.upper_bound is not None and value > self.upper_bound:
            raise ValueError("metric value is above the configured upper bound")
        return value


@dataclass(frozen=True, slots=True)
class ValueObservation:
    """Immutable evidence-backed measurement.

    ``evidence_ref`` is an identifier for evidence held by the governance/evidence plane;
    raw customer content must not be embedded here.
    """

    tenant_id: str
    metric_id: str
    value: float
    observed_at: datetime
    evidence_ref: str
    status: EvidenceStatus = EvidenceStatus.OBSERVED
    source: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.metric_id.strip() or not self.evidence_ref.strip():
            raise ValueError("tenant_id, metric_id and evidence_ref are required")
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        if not isfinite(self.value):
            raise ValueError("observation value must be finite")
        if len(self.source) > 128:
            raise ValueError("source must be <= 128 characters")
        if len(self.metadata) > 32:
            raise ValueError("metadata is limited to 32 bounded attributes")
        for key, value in self.metadata.items():
            if len(key) > 64 or len(value) > 256:
                raise ValueError("metadata keys/values exceed bounded limits")


@dataclass(frozen=True, slots=True)
class ValueTarget:
    metric: ValueMetric
    baseline: float
    target: float
    due_at: datetime | None = None

    def __post_init__(self) -> None:
        self.metric.validate_value(self.baseline)
        self.metric.validate_value(self.target)
        if self.due_at is not None and self.due_at.tzinfo is None:
            raise ValueError("due_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class ValuePlan:
    """Tenant-scoped customer value contract."""

    tenant_id: str
    engagement_id: str
    objective: str
    targets: tuple[ValueTarget, ...]

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.engagement_id.strip():
            raise ValueError("tenant_id and engagement_id are required")
        if not self.objective.strip() or len(self.objective) > 2048:
            raise ValueError("objective must be 1-2048 characters")
        ids = [target.metric.metric_id for target in self.targets]
        if not self.targets or len(ids) != len(set(ids)):
            raise ValueError("value plan requires unique, non-empty targets")


@dataclass(frozen=True, slots=True)
class MetricResult:
    metric_id: str
    baseline: float
    target: float
    latest: float
    absolute_change: float
    relative_change: float | None
    target_progress: float
    achieved: bool
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ValueReport:
    tenant_id: str
    engagement_id: str
    objective: str
    generated_at: datetime
    results: tuple[MetricResult, ...]
    achieved_count: int
    total_count: int

    @property
    def achievement_ratio(self) -> float:
        return self.achieved_count / self.total_count if self.total_count else 0.0


class CustomerValueCalculator:
    """Deterministic value realization calculator.

    A target is achieved according to its declared direction. Progress is bounded to 0..1;
    this prevents over-performance from producing misleading percentages above 100%.
    """

    @staticmethod
    def _progress(direction: Direction, baseline: float, target: float, latest: float) -> float:
        denominator = target - baseline
        if denominator == 0:
            return 1.0 if latest == target else 0.0
        if direction in (Direction.INCREASE, Direction.MAXIMIZE):
            raw = (latest - baseline) / denominator
        else:
            raw = (baseline - latest) / (baseline - target)
        return max(0.0, min(1.0, raw))

    @staticmethod
    def _achieved(direction: Direction, target: float, latest: float) -> bool:
        if direction in (Direction.INCREASE, Direction.MAXIMIZE):
            return latest >= target
        return latest <= target

    def calculate(self, plan: ValuePlan, observations: Iterable[ValueObservation]) -> ValueReport:
        observations_by_metric: dict[str, list[ValueObservation]] = {target.metric.metric_id: [] for target in plan.targets}
        for observation in observations:
            if observation.tenant_id != plan.tenant_id:
                continue
            if observation.metric_id in observations_by_metric and observation.status is not EvidenceStatus.REJECTED:
                observations_by_metric[observation.metric_id].append(observation)

        results: list[MetricResult] = []
        for target in plan.targets:
            evidence = sorted(observations_by_metric[target.metric.metric_id], key=lambda item: item.observed_at)
            if not evidence:
                continue
            latest = target.metric.validate_value(evidence[-1].value)
            absolute = latest - target.baseline
            relative = None if target.baseline == 0 else absolute / abs(target.baseline)
            results.append(
                MetricResult(
                    metric_id=target.metric.metric_id,
                    baseline=target.baseline,
                    target=target.target,
                    latest=latest,
                    absolute_change=absolute,
                    relative_change=relative,
                    target_progress=self._progress(target.metric.direction, target.baseline, target.target, latest),
                    achieved=self._achieved(target.metric.direction, target.target, latest),
                    evidence_refs=tuple(item.evidence_ref for item in evidence),
                )
            )

        achieved_count = sum(result.achieved for result in results)
        return ValueReport(
            tenant_id=plan.tenant_id,
            engagement_id=plan.engagement_id,
            objective=plan.objective,
            generated_at=datetime.now(timezone.utc),
            results=tuple(results),
            achieved_count=achieved_count,
            total_count=len(plan.targets),
        )


def evidence_digest(observations: Iterable[ValueObservation]) -> str:
    """Return a deterministic digest over evidence references and measurements.

    This is an integrity aid, not a replacement for the governance evidence registry.
    """
    rows = sorted(
        f"{item.tenant_id}|{item.metric_id}|{item.value!r}|{item.observed_at.isoformat()}|{item.evidence_ref}|{item.status.value}"
        for item in observations
    )
    return sha256("\n".join(rows).encode("utf-8")).hexdigest()


def decimal_value(value: str) -> Decimal:
    """Parse a decimal customer value without accepting NaN/Infinity."""
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid decimal value") from exc
    if not parsed.is_finite():
        raise ValueError("decimal value must be finite")
    return parsed
