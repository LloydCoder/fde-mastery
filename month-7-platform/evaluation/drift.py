"""Versioned evaluation drift detection using a two-proportion z-test."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class DriftResult:
    baseline_rate: float
    current_rate: float
    absolute_drop: float
    z_score: float
    drifted: bool


def detect_drift(baseline_passed: int, baseline_total: int, current_passed: int, current_total: int, alpha: float = 0.01, minimum_drop: float = 0.05) -> DriftResult:
    if min(baseline_total, current_total) <= 0 or not (0 <= baseline_passed <= baseline_total and 0 <= current_passed <= current_total):
        raise ValueError("invalid evaluation counts")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    p1 = baseline_passed / baseline_total
    p2 = current_passed / current_total
    pooled = (baseline_passed + current_passed) / (baseline_total + current_total)
    se = math.sqrt(max(pooled * (1 - pooled) * (1 / baseline_total + 1 / current_total), 1e-12))
    z = (p2 - p1) / se
    critical = 2.576 if alpha <= 0.01 else 1.96
    drop = p1 - p2
    return DriftResult(p1, p2, drop, z, drop >= minimum_drop and z <= -critical)
