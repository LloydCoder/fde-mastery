"""Platform-level evaluation harness — validates onboarding + deployment."""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

from client_onboarding.schema_mapper import infer_schema_mapping, save_mapping
from client_onboarding.preference_engine import PreferenceEngine
from client_onboarding.golden_generator import generate_golden_dataset
from observability.drift_detector import DriftDetector
from observability.confidence_tracker import ConfidenceTracker
from observability.billing_meter import BillingMeter
from shared_orchestrator.router import AgentRouter
from shared_orchestrator.escalation_matrix import EscalationMatrix
from schemas import ClientConfig, Domain

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("PlatformEval")


class PlatformEvalHarness:
    """End-to-end platform evaluation: onboarding → deployment → observability."""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    def run(self) -> Dict[str, Any]:
        logger.info("=== PLATFORM LAYER EVALUATION ===")
        passed = 0
        total = 0

        # Test 1: Schema Mapper
        total += 1
        try:
            sample = [{"event_id": "E1", "timestamp": "2026-01-01", "src_ip": "10.0.0.1", "severity": "HIGH"}]
            mapping = infer_schema_mapping(Domain.CYBERSECURITY, sample)
            assert mapping["coverage"] > 0.5
            logger.info("✅ Schema Mapper: PASS")
            passed += 1
        except Exception as e:
            logger.warning(f"❌ Schema Mapper: FAIL — {e}")

        # Test 2: Preference Engine
        total += 1
        try:
            config = ClientConfig(client_id="test-corp", client_name="Test Corp", domains=[Domain.CYBERSECURITY])
            pref = PreferenceEngine(config)
            rubric = pref.get_rubric(Domain.CYBERSECURITY)
            assert "auto_contain_threshold" in rubric
            logger.info("✅ Preference Engine: PASS")
            passed += 1
        except Exception as e:
            logger.warning(f"❌ Preference Engine: FAIL — {e}")

        # Test 3: Golden Dataset Generator
        total += 1
        try:
            path = generate_golden_dataset(Domain.FINANCE, [], target_cases=10)
            with open(path, "r") as f:
                cases = json.load(f)
            assert len(cases) == 10
            logger.info("✅ Golden Generator: PASS")
            passed += 1
        except Exception as e:
            logger.warning(f"❌ Golden Generator: FAIL — {e}")

        # Test 4: Agent Router
        total += 1
        try:
            router = AgentRouter()
            assert router.list_domains() == []
            logger.info("✅ Agent Router: PASS")
            passed += 1
        except Exception as e:
            logger.warning(f"❌ Agent Router: FAIL — {e}")

        # Test 5: Escalation Matrix
        total += 1
        try:
            esc = EscalationMatrix()
            record = esc.escalate("test-corp", Domain.LEGAL, "REQ-001", "Critical contract violation")
            assert record.status == "open"
            open_cases = esc.list_open("test-corp")
            assert len(open_cases) == 1
            logger.info("✅ Escalation Matrix: PASS")
            passed += 1
        except Exception as e:
            logger.warning(f"❌ Escalation Matrix: FAIL — {e}")

        # Test 6: Drift Detector
        total += 1
        try:
            detector = DriftDetector("test-corp", Domain.CYBERSECURITY, "test.json")
            report = detector.run()
            assert report.pass_rate > 0
            logger.info("✅ Drift Detector: PASS")
            passed += 1
        except Exception as e:
            logger.warning(f"❌ Drift Detector: FAIL — {e}")

        # Test 7: Confidence Tracker
        total += 1
        try:
            tracker = ConfidenceTracker()
            tracker.record("test-corp", "cybersecurity", 0.94)
            stats = tracker.get_stats("test-corp", "cybersecurity")
            assert stats["mean_confidence"] == 0.94
            logger.info("✅ Confidence Tracker: PASS")
            passed += 1
        except Exception as e:
            logger.warning(f"❌ Confidence Tracker: FAIL — {e}")

        # Test 8: Billing Meter
        total += 1
        try:
            meter = BillingMeter()
            meter.record_call("test-corp", "cybersecurity", tier="growth")
            meter.record_call("test-corp", "finance", tier="growth")
            invoice = meter.generate_invoice("test-corp")
            assert invoice.total_calls == 2
            assert invoice.total_billed_usd > 0
            logger.info("✅ Billing Meter: PASS")
            passed += 1
        except Exception as e:
            logger.warning(f"❌ Billing Meter: FAIL — {e}")

        pass_rate = (passed / total) * 100 if total else 0
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"  PLATFORM EVALUATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"  Total Tests: {total}")
        logger.info(f"  Passed:      {passed}")
        logger.info(f"  Failed:      {total - passed}")
        logger.info(f"  Pass Rate:   {pass_rate:.1f}%")
        logger.info("=" * 60)

        return {"total": total, "passed": passed, "failed": total - passed, "pass_rate": pass_rate}


def main():
    harness = PlatformEvalHarness()
    result = harness.run()
    sys.exit(0 if result["failed"] == 0 else 1)


if __name__ == "__main__":
    main()