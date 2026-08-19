"""Persistence models for clients and API usage."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class ClientRecord:
    client_id: str
    client_name: str
    domains: tuple[str, ...]
    registered_at: str

    @classmethod
    def create(cls, client_id: str, client_name: str, domains: list[str]) -> "ClientRecord":
        return cls(
            client_id=client_id,
            client_name=client_name,
            domains=tuple(domains),
            registered_at=datetime.now(timezone.utc).isoformat(),
        )


@dataclass
class UsageRecord:
    client_id: str
    total_calls: int = 0
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def increment(self) -> int:
        self.total_calls += 1
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return self.total_calls
