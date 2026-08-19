"""Generate golden dataset from client sample data."""

import json
import random
from pathlib import Path
from typing import Any, Dict, List

try:
    from ..schemas import Domain
except ImportError:
    from schemas import Domain


def generate_golden_dataset(
    domain: Domain,
    sample_records: List[Dict[str, Any]],
    target_cases: int = 50,
    out_dir: str = "golden_datasets",
) -> str:
    """Generate a synthetic golden dataset for a client based on their data patterns."""
    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)

    cases = []

    if domain == Domain.CYBERSECURITY:
        cases = _generate_cyber_cases(sample_records, target_cases)
    elif domain == Domain.FINANCE:
        cases = _generate_finance_cases(sample_records, target_cases)
    elif domain == Domain.HEALTHTECH:
        cases = _generate_healthtech_cases(sample_records, target_cases)
    elif domain == Domain.LOGISTICS:
        cases = _generate_logistics_cases(sample_records, target_cases)
    elif domain == Domain.LEGAL:
        cases = _generate_legal_cases(sample_records, target_cases)
    elif domain == Domain.REVOPS:
        cases = _generate_revops_cases(sample_records, target_cases)
    else:
        raise ValueError(f"Unsupported domain: {domain}")

    file_path = path / f"{domain.value}_golden.json"
    with open(file_path, "w") as f:
        json.dump(cases, f, indent=2)

    return str(file_path)


def _generate_cyber_cases(samples: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    actions = ["AUTO_CONTAIN", "ESCALATE_TO_SOC", "MONITOR", "IGNORE_FALSE_POSITIVE"]
    cases = []
    for i in range(n):
        sev = severities[i % 4]
        cases.append({
            "case_id": f"CYB-CLIENT-{i+1:03d}",
            "raw_log": samples[i % len(samples)] if samples else {"event_type": "firewall_alert", "severity": sev},
            "expected_assessment": {
                "severity": sev,
                "recommended_action": actions[i % 4],
                "confidence": 0.95,
            }
        })
    return cases


def _generate_finance_cases(samples: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    risks = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    actions = ["AUTO_REJECT", "FLAG_FOR_REVIEW", "MONITOR", "APPROVE"]
    cases = []
    for i in range(n):
        cases.append({
            "case_id": f"FIN-CLIENT-{i+1:03d}",
            "transaction": samples[i % len(samples)] if samples else {"amount": 1000.0, "currency": "USD"},
            "expected_assessment": {
                "risk_level": risks[i % 4],
                "recommended_action": actions[i % 4],
                "expected_rules_triggered": [],
            }
        })
    return cases


def _generate_healthtech_cases(samples: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    tiers = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    actions = ["IMMEDIATE_INTERVENTION", "ESCALATE_TO_SPECIALIST", "MONITOR", "ROUTINE_FOLLOW_UP"]
    cases = []
    for i in range(n):
        cases.append({
            "case_id": f"HLT-CLIENT-{i+1:03d}",
            "patient_record": samples[i % len(samples)] if samples else {"patient_id": f"PT-{i}", "event_type": "adverse_event"},
            "expected_assessment": {
                "clinical_risk_tier": tiers[i % 4],
                "recommended_action": actions[i % 4],
                "expected_icd10_codes": [],
            }
        })
    return cases


def _generate_logistics_cases(samples: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    risks = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    actions = ["AUTO_REROUTE", "ESCALATE_TO_LOGISTICS_MANAGER", "MONITOR", "STANDARD_PROCESSING"]
    cases = []
    for i in range(n):
        cases.append({
            "case_id": f"LOG-CLIENT-{i+1:03d}",
            "shipment": samples[i % len(samples)] if samples else {"shipment_id": f"SH-{i}", "cargo_type": "electronics"},
            "expected_assessment": {
                "risk_level": risks[i % 4],
                "recommended_action": actions[i % 4],
                "expected_rules_triggered": [],
            }
        })
    return cases


def _generate_legal_cases(samples: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    risks = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    actions = ["REJECT_CONTRACT", "ESCALATE_LEGAL_COUNSEL", "AMEND_CLAUSE", "APPROVE_STANDARD"]
    cases = []
    for i in range(n):
        cases.append({
            "case_id": f"LEG-CLIENT-{i+1:03d}",
            "document": samples[i % len(samples)] if samples else {"contract_id": f"CTR-{i}", "contract_type": "MSA"},
            "expected_result": {
                "risk_tier": risks[i % 4],
                "action": actions[i % 4],
                "exception_flags": [],
            }
        })
    return cases


def _generate_revops_cases(samples: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    risks = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    actions = ["FLAG_CHURN_RISK", "ESCALATE_DEAL_DESK", "TRIGGER_ENRICHMENT_NURTURE", "AUTO_ASSIGN_ENTERPRISE_AE"]
    cases = []
    for i in range(n):
        cases.append({
            "case_id": f"REV-CLIENT-{i+1:03d}",
            "payload": samples[i % len(samples)] if samples else {"opportunity_id": f"OPP-{i}", "account_name": "Acme Corp"},
            "expected_result": {
                "risk_tier": risks[i % 4],
                "action": actions[i % 4],
                "exception_flags": [],
            }
        })
    return cases