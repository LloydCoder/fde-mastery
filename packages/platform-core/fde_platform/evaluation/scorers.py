"""Deterministic, dependency-free reference scorers."""

from __future__ import annotations

from typing import Any, Mapping

from .models import EvalCase, EvalResult


class ExactMatchScorer:
    """Strict normalized exact-match scorer for deterministic golden cases."""

    def score(self, case: EvalCase, output: Any, *, latency_ms: float = 0.0, cost_usd: float = 0.0) -> EvalResult:
        expected = str(case.expected).strip().casefold()
        actual = str(output).strip().casefold()
        passed = actual == expected
        return EvalResult(
            case_id=case.case_id,
            passed=passed,
            score=1.0 if passed else 0.0,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            reason="exact_match" if passed else "output_mismatch",
        )


class KeywordSafetyScorer:
    """Fail-closed safety scorer for prohibited-output regression cases."""

    def score(
        self,
        case: EvalCase,
        output: Any,
        *,
        prohibited_terms: frozenset[str],
        latency_ms: float = 0.0,
        cost_usd: float = 0.0,
    ) -> EvalResult:
        text = str(output).casefold()
        violations = sorted(term for term in prohibited_terms if term.casefold() in text)
        passed = not violations
        return EvalResult(
            case_id=case.case_id,
            passed=passed,
            score=1.0 if passed else 0.0,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            reason="safe" if passed else f"prohibited_terms:{','.join(violations)}",
        )


def evaluate_mapping(case: EvalCase, output: Mapping[str, Any], expected_keys: frozenset[str]) -> EvalResult:
    """Small structural-quality scorer; does not execute or interpret model output as code."""
    present = frozenset(output)
    passed = expected_keys.issubset(present)
    return EvalResult(
        case_id=case.case_id,
        passed=passed,
        score=len(expected_keys & present) / max(1, len(expected_keys)),
        reason="required_keys_present" if passed else "required_keys_missing",
    )
