"""Weekly drift detection — re-runs eval harness on client data."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from ..schemas import Domain, DriftReport
except ImportError:
    from schemas import Domain, DriftReport


class DriftDetector:
    """Detects model/performance drift by re-running golden dataset evaluations."""

    def __init__(self, client_id: str, domain: Domain, golden_dataset_path: str):
        self.client_id = client_id
        self.domain = domain
        self.golden_path = golden_dataset_path
        self._history: List[DriftReport] = []

    def run(self) -> DriftReport:
        """Run evaluation harness and compare against historical pass rates."""
        # In production, this would import and run the real domain eval harness
        # For the platform scaffold, we simulate a result
        simulated_pass_rate = 96.5  # Would come from real eval
        total_cases = 50
        passed = int(total_cases * simulated_pass_rate / 100)

        previous = self._history[-1].pass_rate if self._history else None
        delta = simulated_pass_rate - previous if previous else None
        drift_detected = delta is not None and abs(delta) > 5.0

        recommendation = "No action required."
        if drift_detected and delta and delta < 0:
            recommendation = "ALERT: Pass rate degradation detected. Retrain or review rubric overrides."
        elif drift_detected and delta and delta > 0:
            recommendation = "Pass rate improved. Consider tightening thresholds."

        report = DriftReport(
            client_id=self.client_id,
            domain=self.domain,
            evaluated_at=datetime.now().isoformat(),
            total_cases=total_cases,
            passed=passed,
            pass_rate=simulated_pass_rate,
            drift_detected=drift_detected,
            previous_pass_rate=previous,
            delta=delta,
            recommendation=recommendation,
        )
        self._history.append(report)
        return report

    def get_history(self) -> List[DriftReport]:
        return self._history.copy()