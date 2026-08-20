"""Immutable, tenant-aware registries used by the enterprise control plane."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RegistryEntry(Generic[T]):
    resource_id: str
    version: int
    tenant_id: str | None
    state: str
    resource: T

    def __post_init__(self) -> None:
        if not self.resource_id.strip():
            raise ValueError("resource_id is required")
        if self.version < 1:
            raise ValueError("version must be positive")
        if self.state not in {"draft", "staged", "shadow", "active", "retired"}:
            raise ValueError("invalid registry state")


class _Registry(Generic[T]):
    def __init__(self) -> None:
        self._entries: dict[tuple[str, int, str | None], RegistryEntry[T]] = {}
        self._active: dict[tuple[str, str | None], tuple[str, int, str | None]] = {}

    def register(self, entry: RegistryEntry[T]) -> RegistryEntry[T]:
        key = (entry.resource_id, entry.version, entry.tenant_id)
        if key in self._entries:
            raise ValueError("resource version already registered")
        self._entries[key] = entry
        if entry.state == "active":
            self.promote(entry.resource_id, entry.version, entry.tenant_id)
        return entry

    def promote(self, resource_id: str, version: int, tenant_id: str | None) -> None:
        key = (resource_id, version, tenant_id)
        entry = self._entries.get(key)
        if entry is None:
            raise KeyError("resource version not found")
        for existing_key, existing in tuple(self._entries.items()):
            if existing.resource_id == resource_id and existing.tenant_id == tenant_id and existing.state == "active":
                self._entries[existing_key] = RegistryEntry(existing.resource_id, existing.version, existing.tenant_id, "retired", existing.resource)
        self._entries[key] = RegistryEntry(entry.resource_id, entry.version, entry.tenant_id, "active", entry.resource)
        self._active[(resource_id, tenant_id)] = key

    def get(self, resource_id: str, version: int, tenant_id: str | None) -> RegistryEntry[T]:
        return self._entries[(resource_id, version, tenant_id)]

    def active(self, resource_id: str, tenant_id: str | None) -> RegistryEntry[T]:
        key = self._active[(resource_id, tenant_id)]
        return self._entries[key]

    def list(self, tenant_id: str | None = None) -> tuple[RegistryEntry[T], ...]:
        return tuple(entry for entry in self._entries.values() if entry.tenant_id in {None, tenant_id})


class AgentRegistry(_Registry[object]):
    pass


class ToolRegistry(_Registry[object]):
    pass


class ModelRegistry(_Registry[object]):
    pass


class PolicyRegistry(_Registry[object]):
    pass
