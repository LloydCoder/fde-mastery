"""Immutable evaluation contracts with dataset and run provenance."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
import hashlib
import json
from typing import Any, Mapping, Sequence


class EvalKind(StrEnum):
    GOLDEN = "golden"
    ADVERSARIAL = "adversarial"
    SAFETY = "safety"
    QUALITY = "quality"
    COST = "cost"


class PromotionDecision(StrEnum):
    PROMOTE = "promote"
    REJECT = "reject"


@dataclass(frozen=True, slots=True)
class EvalCase:
    case_id: str
    kind: EvalKind
    input: Mapping[str, Any]
    expected: Any = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id is required")
        if not self.input:
            raise ValueError("input is required")
        object.__setattr__(self, "input", dict(self.input))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def fingerprint(self) -> str:
        canonical = json.dumps(
            {"case_id": self.case_id, "kind": self.kind, "input": self.input, "expected": self.expected},
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True, slots=True)
class EvalDataset:
    name: str
    version: str
    cases: Sequence[EvalCase]
    source: str = "repository"

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.version.strip():
            raise ValueError("dataset name and version are required")
        if not self.cases:
            raise ValueError("dataset must contain at least one case")
        ids = [case.case_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("dataset case IDs must be unique")

    @property
    def fingerprint(self) -> str:
        joined = "".join(case.fingerprint for case in self.cases).encode("ascii")
        return hashlib.sha256(joined).hexdigest()


@dataclass(frozen=True, slots=True)
class EvalResult:
    case_id: str
    passed: bool
    score: float
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    reason: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0 and 1")
        if min(self.latency_ms, self.input_tokens, self.output_tokens, self.cost_usd) < 0:
            raise ValueError("evaluation measurements cannot be negative")


@dataclass(frozen=True, slots=True)
class EvaluationThresholds:
    min_pass_rate: float = 1.0
    min_mean_score: float = 0.95
    max_cost_usd: float | None = None
    max_mean_latency_ms: float | None = None
    max_safety_failures: int = 0

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_pass_rate <= 1.0 or not 0.0 <= self.min_mean_score <= 1.0:
            raise ValueError("quality thresholds must be between 0 and 1")
        if self.max_cost_usd is not None and self.max_cost_usd < 0:
            raise ValueError("max_cost_usd cannot be negative")
        if self.max_mean_latency_ms is not None and self.max_mean_latency_ms < 0:
            raise ValueError("max_mean_latency_ms cannot be negative")
        if self.max_safety_failures < 0:
            raise ValueError("max_safety_failures cannot be negative")


@dataclass(frozen=True, slots=True)
class EvalRun:
    run_id: str
    dataset_name: str
    dataset_version: str
    dataset_fingerprint: str
    results: tuple[EvalResult, ...]
    model_ref: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.run_id.strip() or not self.model_ref.strip():
            raise ValueError("run_id and model_ref are required")
        if not self.results:
            raise ValueError("evaluation run requires results")
        if self.started_at.tzinfo is None:
            raise ValueError("started_at must be timezone-aware")

    @property
    def pass_rate(self) -> float:
        return sum(result.passed for result in self.results) / len(self.results)

    @property
    def mean_score(self) -> float:
        return sum(result.score for result in self.results) / len(self.results)

    @property
    def total_cost_usd(self) -> float:
        return sum(result.cost_usd for result in self.results)

    @property
    def mean_latency_ms(self) -> float:
        return sum(result.latency_ms for result in self.results) / len(self.results)

    def decide(self, thresholds: EvaluationThresholds, safety_failure_count: int) -> PromotionDecision:
        checks = (
            self.pass_rate >= thresholds.min_pass_rate,
            self.mean_score >= thresholds.min_mean_score,
            thresholds.max_cost_usd is None or self.total_cost_usd <= thresholds.max_cost_usd,
            thresholds.max_mean_latency_ms is None or self.mean_latency_ms <= thresholds.max_mean_latency_ms,
            safety_failure_count <= thresholds.max_safety_failures,
        )
        return PromotionDecision.PROMOTE if all(checks) else PromotionDecision.REJECT
