from __future__ import annotations

from platformctl.manifest import manifest


def test_manifest_is_stable_and_complete() -> None:
    payload = manifest()
    assert payload["schema_version"] == "2.0"
    assert payload["platform_version"] == "1.12.0"
    capabilities = payload["capabilities"]
    assert len(capabilities) == 18
    names = {item["name"] for item in capabilities}
    assert names == {
        "identity",
        "control-plane",
        "runtime",
        "workflow",
        "worker",
        "policy",
        "approvals",
        "sandbox",
        "tools",
        "models",
        "events",
        "protocols",
        "evaluation",
        "lineage",
        "finops",
        "incidents",
        "deployment",
        "observability",
    }
