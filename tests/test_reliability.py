from datetime import datetime, timezone

import pytest

from reliability import (
    CorrectiveAction,
    ErrorBudget,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    Postmortem,
    ReliabilityAction,
    SLI,
    SLO,
    incidents_for_tenant,
)


def test_sli_compliance_and_empty_window() -> None:
    assert SLI("availability", 990, 1000).compliance == pytest.approx(0.99)
    assert SLI("availability", 0, 0).compliance == 1.0


def test_error_budget_derives_remaining_and_action() -> None:
    slo = SLO("availability", 0.999)
    assert slo.error_budget_fraction == pytest.approx(0.001)
    assert ErrorBudget(slo, 0.0005).action is ReliabilityAction.NORMAL
    assert ErrorBudget(slo, 0.0008).action is ReliabilityAction.FREEZE_NON_CRITICAL
    assert ErrorBudget(slo, 0.001).exhausted
    assert ErrorBudget(slo, 0.001).action is ReliabilityAction.FREEZE_CHANGES


def test_slo_rejects_invalid_target() -> None:
    with pytest.raises(ValueError):
        SLO("bad", 0.0)
    with pytest.raises(ValueError):
        SLO("bad", 1.1)


def test_incident_lifecycle_is_explicit_and_tenant_bound() -> None:
    now = datetime.now(timezone.utc)
    incident = Incident("inc-1", "tenant-a", "api", IncidentSeverity.P1, "API outage", now)
    incident = incident.transition(IncidentStatus.TRIAGED, actor_tenant_id="tenant-a")
    incident = incident.transition(IncidentStatus.MITIGATING, actor_tenant_id="tenant-a")
    with pytest.raises(PermissionError):
        incident.transition(IncidentStatus.RECOVERING, actor_tenant_id="tenant-b")
    with pytest.raises(ValueError):
        incident.transition(IncidentStatus.CLOSED, actor_tenant_id="tenant-a")


def test_incident_requires_timezone_aware_detection_time() -> None:
    with pytest.raises(ValueError):
        Incident("inc-1", "tenant-a", "api", IncidentSeverity.P2, "failure", datetime.now())


def test_postmortem_and_corrective_action_require_timezone_aware_times() -> None:
    now = datetime.now(timezone.utc)
    postmortem = Postmortem("inc-1", "tenant-a", "5 minutes unavailable", "bad release")
    assert postmortem.completed_at.tzinfo is not None
    action = CorrectiveAction("a-1", "inc-1", "tenant-a", "add canary gate", IncidentSeverity.P1, "owner", now)
    assert action.completed is False


def test_tenant_filter_is_fail_closed_by_selection() -> None:
    now = datetime.now(timezone.utc)
    incidents = (
        Incident("a", "tenant-a", "api", IncidentSeverity.P2, "a", now),
        Incident("b", "tenant-b", "api", IncidentSeverity.P2, "b", now),
    )
    assert tuple(i.incident_id for i in incidents_for_tenant(incidents, "tenant-a")) == ("a",)
