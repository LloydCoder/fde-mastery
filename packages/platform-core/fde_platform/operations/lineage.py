"""Auditable AI decision lineage without recording chain-of-thought."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True, slots=True)
class DecisionEvidence:
    input_refs: tuple[str, ...] = ()
    retrieval_refs: tuple[str, ...] = ()
    policy_decisions: tuple[str, ...] = ()
    tool_invocations: tuple[str, ...] = ()
    model: str = ""
    model_version: str = ""
    approval_ref: str | None = None
    output_ref: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)


class DecisionLineage:
    """Append-only evidence index keyed by a platform execution ID."""

    def __init__(self) -> None:
        self._items: dict[str, DecisionEvidence] = {}

    def record(self, execution_id: str, evidence: DecisionEvidence) -> None:
        if not execution_id.strip():
            raise ValueError("execution_id is required")
        if execution_id in self._items:
            raise ValueError("decision lineage is immutable")
        self._items[execution_id] = evidence

    def get(self, execution_id: str) -> DecisionEvidence:
        return self._items[execution_id]
