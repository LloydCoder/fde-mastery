from datetime import datetime, timezone

import pytest

from fde_platform.reliability import (
    CorrectiveAction,
    IncidentRecord,
    IncidentRegistry,
    IncidentSeverity,
    IncidentStatus,
    ReliabilityDecision,
    SLIObservation,
    SLIType,
    SLO,
    calculate_error_budget,
)


def observation(good: int, total: int = 100) -> SLIObservation:
    return SLIObservation(good, total, datetime.now(timezone.utc))


def test_error_budget_normal() -> None:
    slo = SLO("availability", "tenant-a", SLIType.AVAILABILITY, 0.99)
    budget = calculate_error_budget(slo, (observation(999),))
    assert budget.compliance == pytest.approx(0.999)
    assert budget.decision is ReliabilityDecision.NORMAL
    assert not budget.exhausted


def test_error_budget_freezes_non_critical_at_80_percent() -> None:
    slo = SLO("quality", "tenant-a", SLIType.QUALITY, 0.99)
    budget = calculate_error_budget(slo, (observation(999), observation(998)))
    assert budget.consumed_ratio == pytest.approx(0.15, abs=0.01)
    assert budget.decision is ReliabilityDecision.NORMAL

    budget = calculate_error_budget(slo, (observation(995),))
    assert budget.consumed_ratio == pytest.approx(0.5)
    assert budget.decision is ReliabilityDecision.NORMAL

    budget = calculate_error_budget(slo, (observation(992),))
    assert budget.consumed_ratio == pytest.approx(0.8)
    assert budget.decision is ReliabilityDecision.FREEZE_NON_CRITICAL


def test_error_budget_exhaustion_is_fail_closed() -> None:
    slo = SLO("availability", "tenant-a", SLIType.AVAILABILITY, 0.99)
    budget = calculate_error_budget(slo, (observation(990),))
    assert budget.exhausted
    assert budget.remaining_ratio == 0
    assert budget.decision is ReliabilityDecision.FREEZE_ALL_BUT_CRITICAL


def test_invalid_sli_counts_are_rejected() -> None:
    with pytest.raises(ValueError):
        observation(101)
    with pytest.raises(ValueError):
        observation(-1)
    with pytest.raises(ValueError):
        SLIObservation(1, 1, datetime.now())


def test_incident_requires_tenant_and_severity() -> None:
    incident = IncidentRecord("INC-1", "tenant-a", IncidentSeverity.SEV2, "API degradation")
    assert incident.status is IncidentStatus.DETECTED
    assert incident.tenant_id == "tenant-a"


def test_incident_registry_is_tenant_scoped_and_fail_closed() -> None:
    registry = IncidentRegistry()
    registry.create(IncidentRecord("INC-1", "tenant-a", IncidentSeverity.SEV2, "API degradation"))
    assert registry.get("tenant-a", "INC-1").status is IncidentStatus.DETECTED
    with pytest.raises(KeyError):
        registry.get("tenant-b", "INC-1")
    updated = registry.transition("tenant-a", "INC-1", IncidentStatus.INVESTIGATING)
    assert updated.status is IncidentStatus.INVESTIGATING
    assert len(registry.list_tenant("tenant-b")) == 0


def test_corrective_action_requires_timezone_aware_due_date() -> None:
    with pytest.raises(ValueError):
        CorrectiveAction("CA-1", "tenant-a", "owner", "high", datetime.now(), "Fix alerting")
