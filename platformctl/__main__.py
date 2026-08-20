"""Command-line entry point for platform inspection and readiness checks."""

from __future__ import annotations

import argparse
import importlib
import json

from .manifest import manifest


_CHECKS = {
    "control_plane": "fde_platform.control_plane",
    "tenant_context": "fde_platform.identity",
    "durable_workflow_contract": "fde_platform.workflow",
    "policy_enforcement": "fde_platform.trust",
    "approval_controls": "fde_platform.approvals",
    "sandbox_policy": "fde_platform.runtime.sandbox",
    "model_gateway": "fde_platform.models",
    "tool_gateway": "fde_platform.tools",
    "mcp_a2a_boundaries": "fde_platform.protocols",
    "decision_lineage": "fde_platform.operations",
    "deployment_profiles": "fde_platform.deployment",
}


def doctor() -> dict[str, str]:
    """Run dependency-free import/readiness checks and fail closed on errors."""
    result: dict[str, str] = {}
    for name, module_name in _CHECKS.items():
        try:
            importlib.import_module(module_name)
        except Exception:
            result[name] = "FAIL"
        else:
            result[name] = "PASS"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="platformctl")
    parser.add_argument("command", choices=("manifest", "doctor"), help="inspect platform readiness")
    args = parser.parse_args()
    if args.command == "manifest":
        print(json.dumps(manifest(), indent=2, sort_keys=True))
        return 0
    result = doctor()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(value == "PASS" for value in result.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
