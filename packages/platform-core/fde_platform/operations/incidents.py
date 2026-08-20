"""Minimal AI incident lifecycle for operational containment and evidence."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Incident:
    incident_id: str
    tenant_id: str
    severity: str
    title: str
    status: str = "detected"
    agent_id: str | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.incident_id, self.tenant_id, self.severity, self.title)):
            raise ValueError("incident identity is required")
        if self.severity not in {"SEV-1", "SEV-2", "SEV-3", "SEV-4"}:
            raise ValueError("invalid incident severity")
        if self.status not in {"detected", "contained", "investigating", "remediated", "closed"}:
            raise ValueError("invalid incident status")


class IncidentService:
    _transitions = {
        "detected": {"contained", "investigating"},
        "contained": {"investigating", "remediated"},
        "investigating": {"contained", "remediated"},
        "remediated": {"closed"},
        "closed": set(),
    }

    def __init__(self) -> None:
        self._items: dict[str, Incident] = {}

    def create(self, incident: Incident) -> Incident:
        if incident.incident_id in self._items:
            raise ValueError("incident already exists")
        self._items[incident.incident_id] = incident
        return incident

    def transition(self, incident_id: str, status: str) -> Incident:
        current = self._items[incident_id]
        if status not in self._transitions[current.status]:
            raise ValueError(f"invalid incident transition: {current.status} -> {status}")
        updated = Incident(current.incident_id, current.tenant_id, current.severity, current.title, status, current.agent_id, current.evidence_refs)
        self._items[incident_id] = updated
        return updated

    def get(self, incident_id: str) -> Incident:
        return self._items[incident_id]
