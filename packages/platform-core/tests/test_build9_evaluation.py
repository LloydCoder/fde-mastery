from __future__ import annotations

from fde_platform.evaluation import (
    EvalCase,
    EvalDataset,
    EvalKind,
    EvalResult,
    EvaluationHarness,
    EvaluationThresholds,
    ExactMatchScorer,
    KeywordSafetyScorer,
    PromotionDecision,
)


def test_dataset_fingerprint_is_deterministic_and_case_ids_are_unique() -> None:
    cases = (
        EvalCase("case-1", EvalKind.GOLDEN, {"prompt": "2+2"}, "4"),
        EvalCase("case-2", EvalKind.GOLDEN, {"prompt": "3+3"}, "6"),
    )
    dataset = EvalDataset("golden", "1.0.0", cases)
    assert len(dataset.fingerprint) == 64
    assert dataset.fingerprint == EvalDataset("golden", "1.0.0", cases).fingerprint


def test_exact_match_scorer_is_strict_and_normalized() -> None:
    case = EvalCase("case-1", EvalKind.GOLDEN, {"prompt": "hello"}, "YES")
    result = ExactMatchScorer().score(case, " yes ")
    assert result.passed
    assert result.score == 1.0


def test_safety_scorer_fails_closed_on_prohibited_terms() -> None:
    case = EvalCase("case-1", EvalKind.SAFETY, {"prompt": "unsafe"})
    result = KeywordSafetyScorer().score(case, "This contains SECRET", prohibited_terms=frozenset({"secret"}))
    assert not result.passed
    assert result.score == 0.0
    assert "prohibited_terms" in result.reason


def test_harness_records_provenance_cost_and_latency() -> None:
    dataset = EvalDataset("golden", "1.0.0", (EvalCase("case-1", EvalKind.GOLDEN, {"x": 1}, "ok"),))
    harness = EvaluationHarness()
    run = harness.run(
        dataset,
        lambda _case: ("ok", 0.002),
        lambda case, output: ExactMatchScorer().score(case, output),
        model_ref="provider/model@1.0.0",
    )
    assert run.dataset_fingerprint == dataset.fingerprint
    assert run.total_cost_usd == 0.002
    assert run.results[0].latency_ms >= 0


def test_promotion_gate_rejects_quality_or_safety_regressions() -> None:
    run = __import__("fde_platform.evaluation", fromlist=["EvalRun"]).EvalRun(
        run_id="run-1",
        dataset_name="golden",
        dataset_version="1.0.0",
        dataset_fingerprint="a" * 64,
        results=(EvalResult("case-1", False, 0.5),),
        model_ref="provider/model@1.0.0",
    )
    thresholds = EvaluationThresholds(min_pass_rate=1.0, min_mean_score=0.95)
    assert run.decide(thresholds, safety_failure_count=0) == PromotionDecision.REJECT
    assert run.decide(thresholds, safety_failure_count=1) == PromotionDecision.REJECT
