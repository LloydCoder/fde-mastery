"""Deterministic deployment gates for the six-domain FDE platform.

The gate deliberately separates repository readiness from customer-specific credentials.
It can run in CI with synthetic fixtures and in staging with real adapters.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class Gate(str, Enum):
    GOLDEN_DATASET = "golden_dataset"
    TOOL_INTEGRATION = "tool_integration"
    INGESTION = "ingestion"
    EVALUATION = "evaluation"
    STAGING = "staging"
    SHADOW = "shadow"
    HITL = "human_in_the_loop"
    CONTROLLED_ACTIONS = "controlled_actions"


@dataclass(frozen=True)
class GateResult:
    gate: Gate
    passed: bool
    evidence: str


REQUIRED_GATES = tuple(Gate)


def evaluate_readiness(evidence: Mapping[Gate, bool]) -> tuple[GateResult, ...]:
    """Evaluate all eight gates fail-closed.

    Missing evidence is a failure. Production configuration must therefore explicitly
    prove each gate rather than relying on defaults or implicit behavior.
    """
    return tuple(
        GateResult(gate, bool(evidence.get(gate, False)), "explicit evidence required")
        for gate in REQUIRED_GATES
    )


def is_ready(evidence: Mapping[Gate, bool]) -> bool:
    return all(result.passed for result in evaluate_readiness(evidence))


def require_ready(evidence: Mapping[Gate, bool]) -> None:
    results = evaluate_readiness(evidence)
    failed = [result.gate.value for result in results if not result.passed]
    if failed:
        raise RuntimeError("Enterprise deployment gate failed: " + ", ".join(failed))
