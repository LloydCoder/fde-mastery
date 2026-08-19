from __future__ import annotations

from platformctl.manifest import manifest


def test_manifest_is_stable_and_complete() -> None:
    payload = manifest()
    assert payload["schema_version"] == "1.0"
    assert payload["platform_version"] == "1.11.0"
    capabilities = payload["capabilities"]
    assert len(capabilities) == 10
    names = {item["name"] for item in capabilities}
    assert names == {
        "identity",
        "runtime",
        "workflow",
        "policy",
        "tools",
        "models",
        "events",
        "evaluation",
        "observability",
        "resilience",
    }
