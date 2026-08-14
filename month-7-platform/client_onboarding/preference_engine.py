"""Client-specific preference overrides for severity rubrics."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from ..schemas import ClientConfig, Domain
except ImportError:
    from schemas import ClientConfig, Domain


# Default rubrics per domain
DEFAULT_RUBRICS = {
    Domain.CYBERSECURITY: {
        "auto_contain_threshold": 95,
        "escalate_threshold": 70,
        "monitor_threshold": 30,
        "ignore_threshold": 0,
    },
    Domain.FINANCE: {
        "auto_reject_threshold": 95,
        "flag_for_review_threshold": 60,
        "monitor_threshold": 30,
        "approve_threshold": 0,
    },
    Domain.HEALTHTECH: {
        "immediate_intervention_threshold": 95,
        "escalate_threshold": 70,
        "monitor_threshold": 40,
        "routine_threshold": 0,
    },
    Domain.LOGISTICS: {
        "auto_reroute_threshold": 90,
        "escalate_threshold": 70,
        "monitor_threshold": 40,
        "standard_threshold": 0,
    },
    Domain.LEGAL: {
        "reject_contract_threshold": 90,
        "escalate_counsel_threshold": 60,
        "amend_threshold": 30,
        "approve_threshold": 0,
    },
    Domain.REVOPS: {
        "churn_risk_threshold": 90,
        "deal_desk_threshold": 60,
        "nurture_threshold": 30,
        "auto_assign_threshold": 0,
    },
}


class PreferenceEngine:
    def __init__(self, client_config: ClientConfig):
        self.client_id = client_config.client_id
        self.overrides = client_config.custom_rubric_overrides or {}

    def get_rubric(self, domain: Domain) -> Dict[str, Any]:
        """Return domain rubric with client overrides applied."""
        base = DEFAULT_RUBRICS.get(domain, {}).copy()
        domain_overrides = self.overrides.get(domain.value, {})
        base.update(domain_overrides)
        return base

    def override_rubric(self, domain: Domain, key: str, value: Any) -> None:
        """Dynamically update a rubric value for this client."""
        if domain.value not in self.overrides:
            self.overrides[domain.value] = {}
        self.overrides[domain.value][key] = value

    def save(self, out_dir: str = "preferences") -> str:
        path = Path(out_dir) / self.client_id
        path.mkdir(parents=True, exist_ok=True)
        file_path = path / "rubric_overrides.json"
        with open(file_path, "w") as f:
            json.dump(self.overrides, f, indent=2)
        return str(file_path)