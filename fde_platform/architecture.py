"""Architecture metadata and dependency-boundary definitions.

The boundary lists are executable architecture policy: tests use them to prevent
framework, infrastructure, and legacy curriculum code from leaking into the
platform kernel.
"""

from typing import Final

PLATFORM_KERNEL: Final[str] = "fde_platform"

FORBIDDEN_KERNEL_IMPORT_ROOTS: Final[frozenset[str]] = frozenset(
    {
        "fastapi",
        "sqlalchemy",
        "psycopg",
        "anthropic",
        "openai",
        "requests",
        "deployment",
        "persistence",
        "security",
        "integrations",
        "shared_orchestrator",
        "observability",
        "evaluation",
        "custom_agents",
        "domains",
    }
)

LEGACY_IMPORT_PREFIXES: Final[tuple[str, ...]] = tuple(
    f"month-{month}-" for month in range(1, 7)
)
