"""Flags model degradation by tracking confidence scores over time."""

from datetime import datetime
from typing import Any, Dict, List, Optional


class ConfidenceTracker:
    """Tracks per-client, per-domain confidence scores to flag degradation."""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self._scores: Dict[str, List[float]] = {}
        self._timestamps: Dict[str, List[str]] = {}

    def record(self, client_id: str, domain: str, confidence: float) -> None:
        key = f"{client_id}:{domain}"
        if key not in self._scores:
            self._scores[key] = []
            self._timestamps[key] = []

        self._scores[key].append(confidence)
        self._timestamps[key].append(datetime.now().isoformat())

        # Trim to window
        if len(self._scores[key]) > self.window_size:
            self._scores[key] = self._scores[key][-self.window_size:]
            self._timestamps[key] = self._timestamps[key][-self.window_size:]

    def get_stats(self, client_id: str, domain: str) -> Dict[str, Any]:
        key = f"{client_id}:{domain}"
        scores = self._scores.get(key, [])
        if not scores:
            return {"mean": 0.0, "min": 0.0, "degradation_alert": False}

        mean_conf = sum(scores) / len(scores)
        min_conf = min(scores)
        degradation_alert = mean_conf < 0.85 or min_conf < 0.70

        return {
            "client_id": client_id,
            "domain": domain,
            "window_size": len(scores),
            "mean_confidence": round(mean_conf, 3),
            "min_confidence": round(min_conf, 3),
            "degradation_alert": degradation_alert,
            "last_recorded": self._timestamps[key][-1] if self._timestamps[key] else None,
        }

    def list_monitored(self) -> List[str]:
        return list(self._scores.keys())