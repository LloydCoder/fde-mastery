"""Evaluation harness for RevOps & Enterprise Automation Engine."""

import json
import logging
import sys
from pathlib import Path

try:
    from .agent import RevOpsAgent
    from .schemas import OpportunityPayload
except ImportError:
    from agent import RevOpsAgent
    from schemas import OpportunityPayload

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("EvalHarness")


def run_benchmark(dataset_path: str = "golden_dataset.json"):
    logger.info("=== RUNNING MONTH 6: REVOPS & ENTERPRISE AUTOMATION BENCHMARK ===")

    path = Path(dataset_path)
    if not path.exists():
        logger.error(f"Dataset not found: {dataset_path}")
        sys.exit(1)

    with open(path, "r") as f:
        cases = json.load(f)

    agent = RevOpsAgent()
    passed = 0
    total = len(cases)

    for idx, case in enumerate(cases, 1):
        case_id = case["case_id"]
        description = case["description"]
        payload = OpportunityPayload(**case["payload"])
        expected = case["expected_result"]

        result = agent.evaluate(payload)

        tier_match = result.risk_tier.value == expected["risk_tier"]
        action_match = result.recommended_action.value == expected["action"]
        flags_match = set(result.exception_flags) == set(expected["exception_flags"])

        if tier_match and action_match and flags_match:
            logger.info(f"SUCCESS | Case #{idx} [{case_id}] PASSED")
            logger.info(f"        -> Description: {description}")
            logger.info(
                f"        -> Tier: {result.risk_tier.value} | Action: {result.recommended_action.value} | Flags: {result.exception_flags}"
            )
            passed += 1
        else:
            logger.warning(f"FAILED  | Case #{idx} [{case_id}] FAILED")
            logger.warning(
                f"        Expected: Tier={expected['risk_tier']}, Action={expected['action']}, Flags={expected['exception_flags']}"
            )
            logger.warning(
                f"        Got:      Tier={result.risk_tier.value}, Action={result.recommended_action.value}, Flags={result.exception_flags}"
            )

    print("\n" + "=" * 60)
    print(" EVALUATION SUMMARY [REVOPS & ENTERPRISE AUTOMATION]")
    print("=" * 60)
    print(f" Total Cases: {total}")
    print(f" Passed:      {passed}")
    print(f" Failed:      {total - passed}")
    print(f" Pass Rate:   {(passed / total) * 100:.1f}%")
    print("=" * 60 + "\n")

    return passed == total


if __name__ == "__main__":
    ok = run_benchmark()
    sys.exit(0 if ok else 1)