"""Deterministic evaluation harness with explicit model adapter boundary."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable, Mapping
from uuid import uuid4

from .models import EvalCase, EvalDataset, EvalResult, EvalRun, EvaluationThresholds, PromotionDecision


@dataclass(frozen=True, slots=True)
class EvaluationHarness:
    """Execute trusted evaluation adapters; case data never becomes executable code."""

    def run(
        self,
        dataset: EvalDataset,
        evaluator: Callable[[EvalCase], tuple[Any, float]],
        scorer: Callable[[EvalCase, Any], EvalResult],
        *,
        model_ref: str,
    ) -> EvalRun:
        results: list[EvalResult] = []
        for case in dataset.cases:
            started = perf_counter()
            output, cost = evaluator(case)
            elapsed_ms = (perf_counter() - started) * 1000
            result = scorer(case, output)
            results.append(
                EvalResult(
                    case_id=result.case_id,
                    passed=result.passed,
                    score=result.score,
                    latency_ms=elapsed_ms,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    cost_usd=cost,
                    reason=result.reason,
                )
            )
        return EvalRun(
            run_id=str(uuid4()),
            dataset_name=dataset.name,
            dataset_version=dataset.version,
            dataset_fingerprint=dataset.fingerprint,
            results=tuple(results),
            model_ref=model_ref,
        )

    @staticmethod
    def promotion(
        run: EvalRun,
        thresholds: EvaluationThresholds,
        *,
        safety_failure_count: int,
    ) -> PromotionDecision:
        return run.decide(thresholds, safety_failure_count)
