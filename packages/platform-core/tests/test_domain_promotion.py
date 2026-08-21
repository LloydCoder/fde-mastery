from __future__ import annotations

import json
from pathlib import Path

from domains.registry import DOMAIN_CATALOG, get_domain_registration, validate_catalog


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "golden_datasets" / "domain_smoke_cases.json"


def test_domain_catalog_is_complete_and_fail_closed():
    validate_catalog()
    assert set(DOMAIN_CATALOG) == {
        "cybersecurity",
        "finance",
        "healthtech",
        "logistics",
        "legal",
        "revops",
        "procurement",
        "custom",
    }
    for registration in DOMAIN_CATALOG.values():
        registration.descriptor.validate()
        assert registration.descriptor.human_approval_required is True
        assert registration.descriptor.evaluation_suite
        assert registration.descriptor.representative_dataset == "golden_datasets/domain_smoke_cases.json"


def test_representative_dataset_covers_every_promoted_domain():
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert set(payload["cases"]) == set(DOMAIN_CATALOG)
    for domain_id, registration in DOMAIN_CATALOG.items():
        assert registration.fixture_key == domain_id
        assert payload["cases"][domain_id]


def test_native_and_compatibility_factories_are_loadable(monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "true")
    monkeypatch.setenv("FDE_MONTH1_PROVIDER", "openai")

    for domain_id, registration in DOMAIN_CATALOG.items():
        factory = registration.load_factory()
        assert callable(factory)
        agent = factory()
        assert hasattr(agent, "evaluate")
        assert agent.health()["status"] == "ready"
        capabilities = agent.capabilities()
        assert capabilities.get("human_in_the_loop") is True


def test_custom_domain_is_deterministic_and_has_no_autonomous_side_effects():
    agent = get_domain_registration("custom").instantiate()
    result = agent.evaluate({"risk_level": "low", "confidence": 0.95, "reasons": ["synthetic"]})
    assert result.requires_human_review is False
    assert agent.capabilities()["autonomous_side_effects"] is False


def test_unknown_domain_fails_closed():
    try:
        get_domain_registration("does-not-exist")
    except KeyError as exc:
        assert "unknown domain" in str(exc)
    else:
        raise AssertionError("unknown domains must fail closed")
