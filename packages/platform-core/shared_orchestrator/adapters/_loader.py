"""Utilities for loading the legacy Month 1-6 agents safely.

The domain projects intentionally remain standalone applications and their
folders contain hyphens, so they are not normal Python packages. Several
agents also import their local ``schemas`` module as a top-level import.
This loader gives each domain an isolated module namespace and temporarily
binds its local schemas while importing the agent.
"""

from __future__ import annotations

import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType


PLATFORM_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PLATFORM_ROOT.parent.parent
LEGACY_CURRICULUM_ROOT = REPO_ROOT / "legacy" / "curriculum"


@contextmanager
def _schema_alias(schema_module: ModuleType):
    previous = sys.modules.get("schemas")
    sys.modules["schemas"] = schema_module
    try:
        yield
    finally:
        if previous is None:
            sys.modules.pop("schemas", None)
        else:
            sys.modules["schemas"] = previous


def load_domain_agent(domain_dir: str) -> ModuleType:
    """Load a standalone legacy domain ``agent.py`` in an isolated namespace."""
    domain_path = LEGACY_CURRICULUM_ROOT / domain_dir
    schema_path = domain_path / "schemas.py"
    agent_path = domain_path / "agent.py"

    if not schema_path.is_file() or not agent_path.is_file():
        raise FileNotFoundError(f"Missing domain agent files in {domain_path}")

    safe_name = domain_dir.replace("-", "_")

    schema_spec = importlib.util.spec_from_file_location(
        f"fde_domain_{safe_name}_schemas", schema_path
    )
    if schema_spec is None or schema_spec.loader is None:
        raise ImportError(f"Unable to load schema module for {domain_dir}")
    schema_module = importlib.util.module_from_spec(schema_spec)
    sys.modules[schema_spec.name] = schema_module
    schema_spec.loader.exec_module(schema_module)

    agent_spec = importlib.util.spec_from_file_location(
        f"fde_domain_{safe_name}_agent", agent_path
    )
    if agent_spec is None or agent_spec.loader is None:
        raise ImportError(f"Unable to load agent module for {domain_dir}")
    agent_module = importlib.util.module_from_spec(agent_spec)
    sys.modules[agent_spec.name] = agent_module

    with _schema_alias(schema_module):
        agent_spec.loader.exec_module(agent_module)

    return agent_module
