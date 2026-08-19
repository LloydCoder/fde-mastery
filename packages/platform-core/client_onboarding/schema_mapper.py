"""Auto-map client data fields to domain schemas."""

import json
from pathlib import Path
from typing import Any, Dict, List

try:
    from ..schemas import Domain
except ImportError:
    from schemas import Domain


# Domain-specific field mapping templates
DOMAIN_SCHEMA_TEMPLATES = {
    Domain.CYBERSECURITY: {
        "required": ["event_id", "timestamp", "source_ip", "severity", "event_type", "raw_log"],
        "mappings": {
            "event_id": ["event_id", "id", "log_id", "alert_id"],
            "timestamp": ["timestamp", "ts", "time", "datetime", "created_at"],
            "source_ip": ["source_ip", "src_ip", "ip_address", "client_ip", "origin_ip"],
            "severity": ["severity", "level", "priority", "impact"],
            "event_type": ["event_type", "type", "category", "alert_type"],
            "raw_log": ["raw_log", "message", "log", "payload", "body"],
        },
    },
    Domain.FINANCE: {
        "required": ["transaction_id", "timestamp", "amount", "currency", "source_country", "destination_country", "transaction_type"],
        "mappings": {
            "transaction_id": ["transaction_id", "txn_id", "id", "payment_id"],
            "timestamp": ["timestamp", "ts", "time", "created_at"],
            "amount": ["amount", "value", "total", "sum"],
            "currency": ["currency", "ccy", "curr"],
            "source_country": ["source_country", "from_country", "origin_country", "sender_country"],
            "destination_country": ["destination_country", "to_country", "target_country", "recipient_country"],
            "transaction_type": ["transaction_type", "txn_type", "type", "payment_type"],
        },
    },
    Domain.HEALTHTECH: {
        "required": ["patient_id", "timestamp", "event_type", "clinical_notes"],
        "mappings": {
            "patient_id": ["patient_id", "mrn", "patient_mrn", "subject_id"],
            "timestamp": ["timestamp", "ts", "time", "recorded_at"],
            "event_type": ["event_type", "type", "adverse_event_type", "event_category"],
            "clinical_notes": ["clinical_notes", "notes", "description", "narrative"],
        },
    },
    Domain.LOGISTICS: {
        "required": ["shipment_id", "timestamp", "origin_port", "destination_port", "cargo_type"],
        "mappings": {
            "shipment_id": ["shipment_id", "tracking_id", "id", "bol_number"],
            "timestamp": ["timestamp", "ts", "time", "departure_time"],
            "origin_port": ["origin_port", "from_port", "departure_port", "source_port"],
            "destination_port": ["destination_port", "to_port", "arrival_port", "target_port"],
            "cargo_type": ["cargo_type", "type", "commodity", "goods_type"],
        },
    },
    Domain.LEGAL: {
        "required": ["contract_id", "contract_type", "jurisdiction", "clauses"],
        "mappings": {
            "contract_id": ["contract_id", "id", "agreement_id", "doc_id"],
            "contract_type": ["contract_type", "type", "agreement_type", "doc_type"],
            "jurisdiction": ["jurisdiction", "governing_law", "law", "governing_jurisdiction"],
            "clauses": ["clauses", "sections", "terms", "provisions"],
        },
    },
    Domain.REVOPS: {
        "required": ["opportunity_id", "account_name", "arr_usd", "deal_stage", "lead_source"],
        "mappings": {
            "opportunity_id": ["opportunity_id", "opp_id", "id", "deal_id"],
            "account_name": ["account_name", "company", "customer", "account"],
            "arr_usd": ["arr_usd", "annual_recurring_revenue_usd", "arr", "revenue"],
            "deal_stage": ["deal_stage", "stage", "pipeline_stage", "status"],
            "lead_source": ["lead_source", "source", "channel", "origin"],
        },
    },
}


def infer_schema_mapping(domain: Domain, sample_records: List[Dict[str, Any]]) -> Dict[str, str]:
    """Given sample client records, infer field-to-schema mappings."""
    if not sample_records:
        raise ValueError("No sample records provided for schema inference.")

    template = DOMAIN_SCHEMA_TEMPLATES.get(domain)
    if not template:
        raise ValueError(f"No schema template defined for domain: {domain}")

    # Use first record to infer field names
    sample = sample_records[0]
    sample_keys = set(k.lower() for k in sample.keys())

    mapping: Dict[str, str] = {}
    unmatched: List[str] = []

    for schema_field, candidate_keys in template["mappings"].items():
        matched = False
        for ck in candidate_keys:
            if ck.lower() in sample_keys:
                # Find the actual case-sensitive key from sample
                actual_key = next(k for k in sample.keys() if k.lower() == ck.lower())
                mapping[schema_field] = actual_key
                matched = True
                break
        if not matched:
            unmatched.append(schema_field)

    return {
        "domain": domain.value,
        "mappings": mapping,
        "unmatched_required": unmatched,
        "coverage": len(mapping) / len(template["mappings"]),
    }


def apply_mapping(raw_record: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
    """Apply inferred mapping to transform a raw record into schema-compliant format."""
    result = {}
    for schema_field, client_field in mapping.items():
        result[schema_field] = raw_record.get(client_field)
    # Preserve extra fields in metadata
    used_keys = set(mapping.values())
    extras = {k: v for k, v in raw_record.items() if k not in used_keys}
    if extras:
        result["metadata"] = extras
    return result


def save_mapping(client_id: str, domain: Domain, mapping_result: Dict[str, Any], out_dir: str = "mappings") -> str:
    """Persist schema mapping to disk."""
    path = Path(out_dir) / client_id
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / f"{domain.value}_mapping.json"
    with open(file_path, "w") as f:
        json.dump(mapping_result, f, indent=2)
    return str(file_path)