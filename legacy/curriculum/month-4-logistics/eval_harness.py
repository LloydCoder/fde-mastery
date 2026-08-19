"""
Evaluation Harness for Month 4: Supply Chain & Logistics Engine
Benchmarks agent performance against golden_dataset.json
"""

import json
import logging
import sys
import os

try:
    from agent import LogisticsAgent
    from schemas import ShipmentPayload
except ImportError:
    from .agent import LogisticsAgent
    from .schemas import ShipmentPayload

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
logger = logging.getLogger("EvalHarness")


def run_benchmark():
    logger.info("=== RUNNING MONTH 4: LOGISTICS GOLDEN DATASET BENCHMARK ===")

    dataset_path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
    if not os.path.exists(dataset_path):
        dataset_path = "golden_dataset.json"

    with open(dataset_path, "r") as f:
        cases = json.load(f)

    agent = LogisticsAgent()
    passed = 0
    total = len(cases)

    for idx, case in enumerate(cases, 1):
        case_id = case["case_id"]
        description = case["description"]
        payload = ShipmentPayload(**case["payload"])
        expected = case["expected_result"]

        result = agent.evaluate(payload)

        tier_match = result.risk_tier.value == expected["risk_tier"]
        action_match = result.recommended_action.value == expected["action"]
        flags_match = set(result.exception_flags) == set(expected["exception_flags"])

        if tier_match and action_match and flags_match:
            logger.info(f"SUCCESS | Case #{idx} [{case_id}] PASSED")
            logger.info(f"        -> {description}")
            logger.info(f"        -> Tier: {result.risk_tier.value} | Action: {result.recommended_action.value} | Flags: {result.exception_flags}")
            passed += 1
        else:
            logger.warning(f"FAILED  | Case #{idx} [{case_id}] FAILED")
            logger.warning(f"        Expected: Tier={expected['risk_tier']}, Action={expected['action']}, Flags={expected['exception_flags']}")
            logger.warning(f"        Got:      Tier={result.risk_tier.value}, Action={result.recommended_action.value}, Flags={result.exception_flags}")

    print("\n" + "=" * 60)
    print(" EVALUATION SUMMARY [LOGISTICS & SUPPLY CHAIN]")
    print("=" * 60)
    print(f" Total Cases: {total}")
    print(f" Passed:      {passed}")
    print(f" Failed:      {total - passed}")
    print(f" Pass Rate:   {(passed / total) * 100:.1f}%")
    print("=" * 60 + "\n")

    return passed == total


if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)