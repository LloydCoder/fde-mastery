from datetime import datetime, timezone

import pytest

from fde_platform.customer_value import (
    CustomerValueCalculator,
    Direction,
    EvidenceStatus,
    MetricKind,
    ValueMetric,
    ValueObservation,
    ValuePlan,
    ValueTarget,
    decimal_value,
    evidence_digest,
)


NOW = datetime(2026, 8, 21, 18, 0, tzinfo=timezone.utc)


def metric(direction=Direction.DECREASE):
    return ValueMetric(
        metric_id="case_resolution_time",
        name="Case resolution time",
        kind=MetricKind.DURATION,
        unit="s",
        direction=direction,
        lower_bound=0,
    )


def test_customer_value_calculates_bounded_progress_and_achievement():
    target = ValueTarget(metric(), baseline=100.0, target=60.0)
    plan = ValuePlan("tenant-a", "eng-1", "Reduce resolution time", (target,))
    observation = ValueObservation("tenant-a", target.metric.metric_id, 50.0, NOW, "evidence-1", EvidenceStatus.VERIFIED)

    report = CustomerValueCalculator().calculate(plan, [observation])

    assert report.achieved_count == 1
    assert report.achievement_ratio == 1.0
    assert report.results[0].absolute_change == -50.0
    assert report.results[0].relative_change == -0.5
    assert report.results[0].target_progress == 1.0
    assert report.results[0].evidence_refs == ("evidence-1",)


def test_cross_tenant_observation_is_ignored():
    target = ValueTarget(metric(Direction.INCREASE), baseline=10.0, target=20.0)
    plan = ValuePlan("tenant-a", "eng-1", "Increase throughput", (target,))
    foreign = ValueObservation("tenant-b", target.metric.metric_id, 100.0, NOW, "foreign")

    report = CustomerValueCalculator().calculate(plan, [foreign])

    assert report.results == ()
    assert report.achieved_count == 0


def test_rejected_evidence_is_ignored():
    target = ValueTarget(metric(), baseline=100.0, target=60.0)
    plan = ValuePlan("tenant-a", "eng-1", "Reduce resolution time", (target,))
    rejected = ValueObservation("tenant-a", target.metric.metric_id, 1.0, NOW, "bad", EvidenceStatus.REJECTED)

    assert CustomerValueCalculator().calculate(plan, [rejected]).results == ()


def test_observation_requires_timezone_and_bounded_metadata():
    with pytest.raises(ValueError):
        ValueObservation("tenant", "metric", 1.0, datetime(2026, 8, 21), "evidence")
    with pytest.raises(ValueError):
        ValueObservation("tenant", "metric", 1.0, NOW, "evidence", metadata={str(i): "x" for i in range(33)})


def test_metric_rejects_non_finite_values():
    with pytest.raises(ValueError):
        metric().validate_value(float("inf"))


def test_zero_baseline_has_no_division_error():
    target = ValueTarget(metric(Direction.INCREASE), baseline=0.0, target=10.0)
    plan = ValuePlan("tenant-a", "eng-1", "Increase", (target,))
    observation = ValueObservation("tenant-a", target.metric.metric_id, 5.0, NOW, "e1")

    result = CustomerValueCalculator().calculate(plan, [observation]).results[0]

    assert result.relative_change is None
    assert result.target_progress == 0.5
    assert not result.achieved


def test_evidence_digest_is_deterministic_and_changes_with_evidence():
    first = ValueObservation("tenant", "m", 1.0, NOW, "e1")
    second = ValueObservation("tenant", "m", 2.0, NOW, "e2")

    assert evidence_digest([first, second]) == evidence_digest([second, first])
    assert evidence_digest([first]) != evidence_digest([second])


def test_decimal_parser_rejects_non_finite_values():
    assert decimal_value("10.25") == decimal_value("10.250")
    with pytest.raises(ValueError):
        decimal_value("NaN")
    with pytest.raises(ValueError):
        decimal_value("Infinity")
