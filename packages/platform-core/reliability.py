"""Incident and SRE control-plane primitives.

The module is deliberately side-effect free: persistence, alert delivery and deployment
systems remain behind their existing platform boundaries. It models SLI/SLO/error-budget
state, incident lifecycle, postmortems and corrective actions with tenant-safe contracts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable


class IncidentSeverity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class IncidentStatus(str, Enum):
    DETECTED = "detected"
    TRIAGED = "triaged"
    CONTAINED = "contained"
    MITIGATING = "mitigating"
    RECOVERING = "recovering"
    RESOLVED = "resolved"
    CLOSED = "closed"


_ALLOWED_TRANSITIONS: dict[IncidentStatus, frozenset[IncidentStatus]] = {
    IncidentStatus.DETECTED: frozenset({IncidentStatus.TRIAGED}),
    IncidentStatus.TRIAGED: frozenset({IncidentStatus.CONTAINED, IncidentStatus.MITIGATING}),
    IncidentStatus.CONTAINED: frozenset({IncidentStatus.MITIGATING}),
    IncidentStatus.MITIGATING: frozenset({IncidentStatus.RECOVERING}),
    IncidentStatus.RECOVERING: frozenset({IncidentStatus.RESOLVED}),
    IncidentStatus.RESOLVED: frozenset({IncidentStatus.CLOSED}),
    IncidentStatus.CLOSED: frozenset(),
}


class ReliabilityAction(str, Enum):
    NORMAL = "normal"
    FREEZE_NON_CRITICAL = "freeze_non_critical"
    FREEZE_CHANGES = "freeze_changes"


@dataclass(frozen=True, slots=True)
class SLI:
    name: str
    good_events: int
    total_events: int

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("SLI name is required")
        if self.total_events < 0 or self.good_events < 0 or self.good_events > self.total_events:
            raise ValueError("SLI event counts are invalid")

    @property
    def compliance(self) -> float:
        return 1.0 if self.total_events == 0 else self.good_events / self.total_events


@dataclass(frozen=True, slots=True)
class SLO:
    name: str
    target: float
    window_days: int = 28

    def __post_init__(self) -> None:
        if not self.name.strip() or not 0.0 < self.target <= 1.0:
            raise ValueError("SLO name and target are invalid")
        if self.window_days <= 0:
            raise ValueError("SLO window_days must be positive")

    @property
    def error_budget_fraction(self) -> float:
        return 1.0 - self.target


@dataclass(frozen=True, slots=True)
class ErrorBudget:
    slo: SLO
    consumed_fraction: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.consumed_fraction:
            raise ValueError("consumed_fraction cannot be negative")

    @property
    def remaining_fraction(self) -> float:
        return max(0.0, self.slo.error_budget_fraction - self.consumed_fraction)

    @property
    def exhausted(self) -> bool:
        return self.consumed_fraction >= self.slo.error_budget_fraction

    @property
    def action(self) -> ReliabilityAction:
        if self.exhausted:
            return ReliabilityAction.FREEZE_CHANGES
        if self.consumed_fraction >= self.slo.error_budget_fraction * 0.8:
            return ReliabilityAction.FREEZE_NON_CRITICAL
        return ReliabilityAction.NORMAL


@dataclass(frozen=True, slots=True)
class Incident:
    incident_id: str
    tenant_id: str
    service: str
    severity: IncidentSeverity
    title: str
    detected_at: datetime
    status: IncidentStatus = IncidentStatus.DETECTED
    owner: str | None = None
    error_budget_impact_fraction: float = 0.0

    def __post_init__(self) -> None:
        if not self.incident_id.strip() or not self.tenant_id.strip() or not self.service.strip():
            raise ValueError("incident identity, tenant and service are required")
        if not self.title.strip():
            raise ValueError("incident title is required")
        if self.detected_at.tzinfo is None:
            raise ValueError("detected_at must be timezone-aware")
        if self.error_budget_impact_fraction < 0:
            raise ValueError("error budget impact cannot be negative")

    def transition(self, new_status: IncidentStatus, *, actor_tenant_id: str) -> "Incident":
        if actor_tenant_id != self.tenant_id:
            raise PermissionError("cross-tenant incident transition denied")
        if new_status not in _ALLOWED_TRANSITIONS[self.status]:
            raise ValueError(f"invalid incident transition: {self.status.value} -> {new_status.value}")
        return Incident(
            incident_id=self.incident_id,
            tenant_id=self.tenant_id,
            service=self.service,
            severity=self.severity,
            title=self.title,
            detected_at=self.detected_at,
            status=new_status,
            owner=self.owner,
            error_budget_impact_fraction=self.error_budget_impact_fraction,
        )


@dataclass(frozen=True, slots=True)
class Postmortem:
    incident_id: str
    tenant_id: str
    impact: str
    root_cause: str
    contributing_factors: tuple[str, ...] = ()
    detection_gaps: tuple[str, ...] = ()
    follow_up_actions: tuple[str, ...] = ()
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.incident_id.strip() or not self.tenant_id.strip():
            raise ValueError("postmortem identity is required")
        if not self.impact.strip() or not self.root_cause.strip():
            raise ValueError("postmortem impact and root cause are required")
        if self.completed_at.tzinfo is None:
            raise ValueError("completed_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class CorrectiveAction:
    action_id: str
    incident_id: str
    tenant_id: str
    description: str
    priority: IncidentSeverity
    owner: str
    due_at: datetime
    completed: bool = False

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.action_id, self.incident_id, self.tenant_id, self.description, self.owner)):
            raise ValueError("corrective action identity and ownership are required")
        if self.due_at.tzinfo is None:
            raise ValueError("due_at must be timezone-aware")


def incidents_for_tenant(incidents: Iterable[Incident], tenant_id: str) -> tuple[Incident, ...]:
    """Return only incidents belonging to the caller's tenant."""
    return tuple(incident for incident in incidents if incident.tenant_id == tenant_id)
