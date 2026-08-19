"""Persistence boundary used by application services."""

from typing import Any, Protocol


class RepositoryPort(Protocol):
    """Minimal persistence contract; storage technology stays outside the core."""

    def get(self, resource: str, resource_id: str) -> Any:
        """Return a resource or ``None`` when it does not exist."""

    def save(self, resource: str, value: Any) -> None:
        """Persist a resource."""
