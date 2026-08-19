"""Generate deterministic, versioned synthetic golden cases for CI and staging.

The generator intentionally uses synthetic data. Customer data must never be committed.
"""
from __future__ import annotations

import json
from pathlib import Path

DOMAINS = ("cybersecurity", "finance", "healthtech", "logistics", "legal", "revops", "procurement")
LABELS = ("benign", "suspicious", "malicious", "ambiguous")
CASES_PER_DOMAIN = 100
VERSION = "2026.08.18-v2"


def build_case(domain: str, index: int) -> dict[str, object]:
    label = LABELS[index % len(LABELS)]
    return {
        "id": f"{domain}-{index + 1:04d}",
        "dataset_version": VERSION,
        "domain": domain,
        "label": label,
        "input": {"synthetic": True, "event_index": index, "scenario": f"{domain}-{label}"},
        "expected": {"disposition": label, "requires_human_review": label in {"malicious", "ambiguous"}},
    }


def generate(output: Path) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for domain in DOMAINS:
            for index in range(CASES_PER_DOMAIN):
                handle.write(json.dumps(build_case(domain, index), sort_keys=True) + "\n")
    return len(DOMAINS) * CASES_PER_DOMAIN


if __name__ == "__main__":
    count = generate(Path("evaluation/golden/generated-v1.jsonl"))
    print(f"generated {count} synthetic golden cases")
