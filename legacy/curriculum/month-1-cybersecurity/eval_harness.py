"""Statistical evaluation framework for SOC Triage Agent."""
import json
import os
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

from schemas import RawSecurityLog, ThreatTriageReport
from agent import SOCTriageAgent

PROJECT_ROOT = Path(__file__).resolve().parent.parent
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class EvaluationHarness:
    """Benchmark agent triage performance against golden datasets."""

    def __init__(
        self,
        dataset_path: str,
        provider: str = "openai",
        model: str | None = None,
        fuzzy: bool = False,
    ):
        self.dataset_path = Path(dataset_path)
        self.agent = SOCTriageAgent(provider=provider, model=model)
        self.fuzzy = fuzzy  # Allow near-matches (e.g., ESCALATE_TO_SOC ≈ AUTO_CONTAIN for exfil)

    def load_dataset(self) -> list:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Golden dataset not found at {self.dataset_path}")
        with open(self.dataset_path, "r") as f:
            return json.load(f)

    def _action_compatible(self, expected: str, actual: str, severity: str, category: str) -> bool:
        """Fuzzy matching: some action disagreements are acceptable for the same event."""
        if expected == actual:
            return True
        # For active exfiltration, both AUTO_CONTAIN and ESCALATE_TO_SOC are defensible
        if category == "DATA_EXFILTRATION" and severity == "CRITICAL":
            if expected in ("AUTO_CONTAIN", "ESCALATE_TO_SOC") and actual in ("AUTO_CONTAIN", "ESCALATE_TO_SOC"):
                return True
        # For reconnaissance, both MONITOR and ESCALATE_TO_SOC can be acceptable
        if category == "RECONNAISSANCE":
            if expected in ("MONITOR", "ESCALATE_TO_SOC") and actual in ("MONITOR", "ESCALATE_TO_SOC"):
                return True
        return False

    def run_evaluation(self) -> dict:
        test_cases = self.load_dataset()
        total_tests = len(test_cases)
        passed_tests = 0
        failed_tests = 0
        results_log = []

        logger.info(f"Evaluation Harness: {total_tests} cases from {self.dataset_path.name}")

        for index, case in enumerate(test_cases, start=1):
            raw_log_data = case["input_log"]
            expected = case["expected_output"]

            try:
                log_entry = RawSecurityLog(**raw_log_data)
                report: ThreatTriageReport = self.agent.triage_log(log_entry)

                severity_match = report.severity.value == expected["severity"]
                category_match = report.category.value == expected["category"]

                if self.fuzzy:
                    action_match = self._action_compatible(
                        expected["recommended_action"],
                        report.recommended_action.value,
                        report.severity.value,
                        report.category.value,
                    )
                else:
                    action_match = report.recommended_action.value == expected["recommended_action"]

                test_passed = severity_match and category_match and action_match

                if test_passed:
                    passed_tests += 1
                    logger.success(f"Test #{index} [{log_entry.log_id}] PASSED")
                else:
                    failed_tests += 1
                    mismatches = []
                    if not severity_match:
                        mismatches.append(f"Severity: expected {expected['severity']} got {report.severity.value}")
                    if not category_match:
                        mismatches.append(f"Category: expected {expected['category']} got {report.category.value}")
                    if not action_match:
                        mismatches.append(f"Action: expected {expected['recommended_action']} got {report.recommended_action.value}")
                    logger.warning(
                        f"Test #{index} [{log_entry.log_id}] FAILED | " + " | ".join(mismatches)
                    )

                results_log.append({
                    "test_index": index,
                    "log_id": log_entry.log_id,
                    "passed": test_passed,
                    "expected": expected,
                    "actual": {
                        "severity": report.severity.value,
                        "category": report.category.value,
                        "recommended_action": report.recommended_action.value,
                    },
                })

            except Exception as e:
                failed_tests += 1
                logger.error(f"Test #{index} exception: {e}")
                results_log.append({"test_index": index, "passed": False, "error": str(e)})

        pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pass_rate_percentage": round(pass_rate, 2),
            "fuzzy_mode": self.fuzzy,
            "details": results_log,
        }
        logger.info(f"Done. Pass Rate: {summary['pass_rate_percentage']}% ({passed_tests}/{total_tests})")
        return summary


if __name__ == "__main__":
    harness = EvaluationHarness("golden_dataset.json", provider="openai")
    harness.run_evaluation()