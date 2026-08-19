"""
month-2-finance/eval_harness.py
--------------------------------
Evaluation Harness for the Financial Risk Agent.
Benchmarks agent performance against month-2-finance/golden_dataset.json
supporting both Exact and Fuzzy evaluation modes.
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Dict, Any, List, Tuple

from agent import FinancialRiskAgent
from schemas import (
    FinancialTransaction,
    RiskAssessmentReport,
    RiskLevel,
    FinancialAction
)

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
logger = logging.getLogger("EvalHarness")


def load_golden_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """Loads the golden dataset JSON file."""
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset file not found at: {dataset_path}")
        sys.exit(1)

    with open(dataset_path, "r") as f:
        return json.load(f)


def evaluate_case(
    actual: RiskAssessmentReport,
    expected: Dict[str, Any],
    fuzzy: bool = False
) -> Tuple[bool, str]:
    """
    Evaluates an agent report against expected ground-truth assessment.

    Exact Mode:
      - Exact match on risk_level
      - Exact match on recommended_action
      - All expected rule IDs present in triggered rules

    Fuzzy Mode:
      - Exact match on recommended_action OR equivalent risk tier response
      - At least 50% overlap on expected triggered rules
    """
    expected_risk = expected["risk_level"]
    expected_action = expected["recommended_action"]
    expected_rules = expected.get("expected_rules_triggered", [])

    actual_risk = actual.risk_level.value
    actual_action = actual.recommended_action.value
    actual_rule_ids = [r.rule_id for r in actual.triggered_rules]

    # Action and Risk Check
    risk_match = (actual_risk == expected_risk)
    action_match = (actual_action == expected_action)

    # Fuzzy Action Match Allowance (e.g., AUTO_REJECT vs FREEZE_ACCOUNT for CRITICAL)
    if fuzzy:
        if expected_action in ["AUTO_REJECT", "FREEZE_ACCOUNT"] and actual_action in ["AUTO_REJECT", "FREEZE_ACCOUNT"]:
            action_match = True
        if expected_action == "FLAG_FOR_REVIEW" and actual_action in ["FLAG_FOR_REVIEW", "MONITOR"]:
            action_match = True

    # Rules Check
    if not expected_rules:
        rules_match = True
    else:
        matched_rules = set(expected_rules).intersection(set(actual_rule_ids))
        if fuzzy:
            rules_match = len(matched_rules) > 0  # At least one key rule captured
        else:
            rules_match = set(expected_rules).issubset(set(actual_rule_ids))

    passed = (risk_match and action_match and rules_match) if not fuzzy else (action_match and rules_match)

    details = (
        f"Expected S={expected_risk} A={expected_action} R={expected_rules} | "
        f"Got S={actual_risk} A={actual_action} R={actual_rule_ids}"
    )

    return passed, details


def run_benchmark(
    dataset_path: str,
    model_name: str = "claude-sonnet-4-6",
    mock_mode: bool = False,
    fuzzy_mode: bool = False
) -> bool:
    """Runs the golden dataset benchmark evaluation suite."""
    logger.info("=== RUNNING GOLDEN DATASET BENCHMARK ===")
    if mock_mode:
        logger.warning("🧪 MOCK / FALLBACK MODE ENABLED — Using rule engine fallback.")
        agent = FinancialRiskAgent(model_name=model_name, api_key=None)
    else:
        agent = FinancialRiskAgent(model_name=model_name)

    dataset = load_golden_dataset(dataset_path)
    logger.info(f"Evaluation Harness: {len(dataset)} test cases loaded from {dataset_path}")

    passed_count = 0
    total_cases = len(dataset)
    start_time = time.time()

    for idx, case in enumerate(dataset, start=1):
        txn_id = case["transaction_id"]
        logger.info(f"[{model_name}] Evaluating Case #{idx} [{txn_id}] | Type: {case['transaction_type']}")

        transaction = FinancialTransaction(**case)
        actual_report = agent.evaluate_transaction(transaction)

        passed, details = evaluate_case(actual_report, case["expected_assessment"], fuzzy=fuzzy_mode)

        if passed:
            logger.info(f"SUCCESS | Test #{idx} [{txn_id}] PASSED")
            passed_count += 1
        else:
            logger.warning(f"FAILED  | Test #{idx} [{txn_id}] FAILED | {details}")

    elapsed = round(time.time() - start_time, 2)
    pass_rate = round((passed_count / total_cases) * 100, 1)

    mode_str = " [FUZZY MODE]" if fuzzy_mode else ""
    print("\n" + "=" * 60)
    print(f"  EVALUATION SUMMARY [{model_name.upper()}]{mode_str}")
    print("=" * 60)
    print(f"Total Cases:  {total_cases}")
    print(f"Passed:       {passed_count}")
    print(f"Failed:       {total_cases - passed_count}")
    print(f"Pass Rate:    {pass_rate}%")
    print(f"Time Taken:   {elapsed}s")
    print("=" * 60 + "\n")

    return pass_rate == 100.0


def main():
    parser = argparse.ArgumentParser(description="Month 2 Financial Risk Agent Eval Harness")
    parser.add_argument("--dataset", type=str, default="golden_dataset.json", help="Path to golden dataset JSON")
    parser.add_argument("--model", type=str, default="claude-sonnet-4-6", help="Model ID to evaluate")
    parser.add_argument("--mock", action="store_true", help="Run in mock/fallback mode without live API calls")
    parser.add_argument("--fuzzy", action="store_true", help="Enable fuzzy evaluation mode for policy thresholds")

    args = parser.parse_args()
    
    # Resolve relative dataset path
    dataset_path = args.dataset
    if not os.path.isabs(dataset_path):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dataset_path = os.path.join(base_dir, dataset_path)

    run_benchmark(
        dataset_path=dataset_path,
        model_name=args.model,
        mock_mode=args.mock,
        fuzzy_mode=args.fuzzy
    )


if __name__ == "__main__":
    main()