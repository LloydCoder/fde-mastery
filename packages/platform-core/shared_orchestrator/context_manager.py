"""Cross-domain context manager — enables multi-domain memory."""

from typing import Any, Dict, List, Optional


class ContextManager:
    """Maintains shared context across domain agents for a single client."""

    def __init__(self, client_id: str):
        self.client_id = client_id
        self._context: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []

    def set(self, key: str, value: Any) -> None:
        self._context[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._context.get(key, default)

    def log_interaction(self, domain: str, request_id: str, result: Dict[str, Any]) -> None:
        self._history.append({
            "domain": domain,
            "request_id": request_id,
            "result_summary": {k: str(v)[:100] for k, v in result.items()},
        })

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if limit:
            return self._history[-limit:]
        return self._history.copy()

    def cross_domain_risk_score(self) -> float:
        """Compute an aggregate risk score across all domains."""
        scores = []
        for entry in self._history:
            if "risk_score" in entry.get("result_summary", {}):
                try:
                    scores.append(float(entry["result_summary"]["risk_score"]))
                except (ValueError, TypeError):
                    pass
        return sum(scores) / len(scores) if scores else 0.0