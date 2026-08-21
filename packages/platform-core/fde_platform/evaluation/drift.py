"""Statistical evaluation drift detection owned by the production evaluation boundary."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DriftResult:
    baseline_rate: float
    current_rate: float
    absolute_drop: float
    z_score: float
    drifted: bool


def detect_drift(
    baseline_passed: int,
    baseline_total: int,
    current_passed: int,
    current_total: int,
    alpha: float = 0.01,
    minimum_drop: float = 0.05,
) -> DriftResult:
    """Detect a material pass-rate regression using a two-proportion z-test."""
    if min(baseline_total, current_total) <= 0 or not (
        0 <= baseline_passed <= baseline_total and 0 <= current_passed <= current_total
    ):
        raise ValueError("invalid evaluation counts")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if minimum_drop < 0:
        raise ValueError("minimum_drop cannot be negative")

    baseline_rate = baseline_passed / baseline_total
    current_rate = current_passed / current_total
    pooled = (baseline_passed + current_passed) / (baseline_total + current_total)
    standard_error = math.sqrt(
        max(pooled * (1 - pooled) * (1 / baseline_total + 1 / current_total), 1e-12)
    )
    z_score = (current_rate - baseline_rate) / standard_error
    critical = 2.576 if alpha <= 0.01 else 1.96
    absolute_drop = baseline_rate - current_rate
    return DriftResult(
        baseline_rate,
        current_rate,
        absolute_drop,
        z_score,
        absolute_drop >= minimum_drop and z_score <= -critical,
    )
