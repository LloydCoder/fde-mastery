"""Deterministic SLI/SLO, incident, and corrective-action contracts.

The module is intentionally side-effect free. Existing observability, authorization,
deployment, and durable-workflow boundaries remain responsible for execution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SLIType(str, Enum):
    AVAILABILITY = "availability"
    LATENCY = "latency"
    CORRECTNESS = "correctness"
    QUALITY = "quality"


class ReliabilityDecision(str, Enum):
    NORMAL = "normal"
    FREEZE_NON_CRITICAL = "freeze_non_critical"
    FREEZE_ALL_BUT_CRITICAL = "freeze_all_but_critical"


class IncidentSeverity(str, Enum):
    SEV1 = "SEV-1"
    SEV2 = "SEV-2"
    SEV3 = "SEV-3"
    SEV4 = "SEV-4"


class IncidentStatus(str, Enum):
    DETECTED = "detected"
    CONTAINED = "contained"
    INVESTIGATING = "investigating"
    REMEDIATED = "remediated"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class SLIObservation:
    good_events: int
    total_events: int
    observed_at: datetime

    def __post_init__(self) -> None:
        if self.good_events < 0 or self.total_events <= 0 or self.good_events > self.total_events:
            raise ValueError("SLI event counts are invalid")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")

    @property
    def compliance(self) -> float:
        return self.good_events / self.total_events


@dataclass(frozen=True, slots=True)
class SLO:
    name: str
    tenant_id: str
    sli_type: SLIType
    target: float
    window_days: int = 30

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.tenant_id.strip():
            raise ValueError("SLO identity is required")
        if not 0 < self.target <= 1:
            raise ValueError("SLO target must be in (0, 1]")
        if self.window_days <= 0 or self.window_days > 366:
            raise ValueError("window_days must be between 1 and 366")


@dataclass(frozen=True, slots=True)
class ErrorBudget:
    target: float
    compliance: float
    consumed_ratio: float
    remaining_ratio: float
    exhausted: bool
    decision: ReliabilityDecision


def calculate_error_budget(slo: SLO, observations: tuple[SLIObservation, ...]) -> ErrorBudget:
    if not observations:
        raise ValueError("at least one SLI observation is required")
    total = sum(item.total_events for item in observations)
    good = sum(item.good_events for item in observations)
    compliance = good / total
    allowed_failure = 1.0 - slo.target
    actual_failure = 1.0 - compliance
    consumed = 1.0 if allowed_failure == 0 and actual_failure > 0 else (actual_failure / allowed_failure if allowed_failure else 0.0)
    consumed = max(0.0, min(1.0, consumed))
    remaining = max(0.0, 1.0 - consumed)
    if consumed >= 1.0:
        decision = ReliabilityDecision.FREEZE_ALL_BUT_CRITICAL
    elif consumed >= 0.8:
        decision = ReliabilityDecision.FREEZE_NON_CRITICAL
    else:
        decision = ReliabilityDecision.NORMAL
    return ErrorBudget(slo.target, compliance, consumed, remaining, consumed >= 1.0, decision)


@dataclass(frozen=True, slots=True)
class IncidentRecord:
    incident_id: str
    tenant_id: str
    severity: IncidentSeverity
    title: str
    status: IncidentStatus = IncidentStatus.DETECTED
    detected_at: datetime | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.incident_id.strip() or not self.tenant_id.strip() or not self.title.strip():
            raise ValueError("incident identity is required")
        if self.detected_at is not None and (self.detected_at.tzinfo is None or self.detected_at.utcoffset() is None):
            raise ValueError("detected_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class Postmortem:
    incident_id: str
    tenant_id: str
    impact: str
    root_cause: str
    contributing_factors: tuple[str, ...] = ()
    detection_gaps: tuple[str, ...] = ()
    follow_up_action_ids: tuple[str, ...] = ()
    completed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class CorrectiveAction:
    action_id: str
    tenant_id: str
    owner: str
    priority: str
    due_at: datetime
    description: str
    completed: bool = False

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.action_id, self.tenant_id, self.owner, self.priority, self.description)):
            raise ValueError("corrective-action identity and ownership are required")
        if self.due_at.tzinfo is None or self.due_at.utcoffset() is None:
            raise ValueError("due_at must be timezone-aware")
