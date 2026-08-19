"""Executable architecture rules for the enterprise platform foundation."""

from __future__ import annotations

import ast
from pathlib import Path

from fde_platform.architecture import FORBIDDEN_KERNEL_IMPORT_ROOTS, LEGACY_IMPORT_PREFIXES

ROOT = Path(__file__).resolve().parents[1]

PRODUCTION_ROOTS = (
    "fde_platform",
    "domains",
    "security",
    "persistence",
    "shared_orchestrator",
    "integrations",
    "observability",
    "evaluation",
    "custom_agents",
    "deployment",
)


def _python_files(root: Path):
    if not root.exists():
        return ()
    return root.rglob("*.py")


def _import_roots(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module.split(".", 1)[0]


def _imported_modules(path: Path) -> set[str]:
    return set(_import_roots(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))))


def test_platform_kernel_has_no_infrastructure_dependencies():
    """The kernel must remain framework/vendor/infrastructure agnostic."""
    violations: list[str] = []
    for path in _python_files(ROOT / "fde_platform"):
        forbidden = _imported_modules(path) & FORBIDDEN_KERNEL_IMPORT_ROOTS
        violations.extend(f"{path.relative_to(ROOT)} imports {name}" for name in sorted(forbidden))
    assert not violations, "Architecture boundary violations:\n" + "\n".join(violations)


def test_production_code_does_not_import_curriculum_months():
    """Month 1-6 curriculum implementations are compatibility history, not platform dependencies."""
    violations: list[str] = []
    for root_name in PRODUCTION_ROOTS:
        for path in _python_files(ROOT / root_name):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imports = set(_import_roots(tree))
            legacy = {name for name in imports if any(name.startswith(prefix) for prefix in LEGACY_IMPORT_PREFIXES)}
            violations.extend(f"{path.relative_to(ROOT)} imports {name}" for name in sorted(legacy))
    assert not violations, "Legacy dependency violations:\n" + "\n".join(violations)


def test_platform_contracts_are_importable_without_frameworks():
    """The new contracts/ports load without FastAPI or infrastructure adapters."""
    from fde_platform.contracts import AgentRequest, AgentResult, DomainDescriptor, ExecutionContext
    from fde_platform.ports import AgentPort, EventBusPort, ModelPort, RepositoryPort, ToolPort

    assert AgentRequest and AgentResult and DomainDescriptor and ExecutionContext
    assert AgentPort and EventBusPort and ModelPort and RepositoryPort and ToolPort


def test_required_architecture_roots_exist():
    for path in (ROOT / "fde_platform", ROOT / "fde_platform" / "contracts", ROOT / "fde_platform" / "ports"):
        assert path.is_dir(), f"Missing architecture root: {path.relative_to(ROOT)}"


def test_domain_plugins_depend_on_platform_not_reverse():
    """Domain packages may consume platform contracts; the kernel may not consume domains."""
    violations: list[str] = []
    for path in _python_files(ROOT / "domains"):
        imports = _imported_modules(path)
        forbidden = {name for name in imports if name in FORBIDDEN_KERNEL_IMPORT_ROOTS - {"domains"}}
        violations.extend(f"{path.relative_to(ROOT)} imports {name}" for name in sorted(forbidden))
    assert not violations, "Domain dependency violations:\n" + "\n".join(violations)
