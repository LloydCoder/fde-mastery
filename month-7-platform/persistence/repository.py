"""Storage interface with an in-memory implementation for the platform demo.

The API no longer owns raw dictionaries. The repository boundary makes the
storage backend replaceable with PostgreSQL without changing gateway logic.
"""

from abc import ABC, abstractmethod
from threading import Lock
from typing import Optional

from .models import ClientRecord, UsageRecord


class PlatformRepository(ABC):
    @abstractmethod
    def register_client(self, record: ClientRecord) -> None: ...

    @abstractmethod
    def get_client(self, client_id: str) -> Optional[ClientRecord]: ...

    @abstractmethod
    def increment_usage(self, client_id: str) -> int: ...

    @abstractmethod
    def get_usage(self, client_id: str) -> int: ...


class InMemoryPlatformRepository(PlatformRepository):
    """Thread-safe reference backend used for local demos and tests."""

    def __init__(self) -> None:
        self._clients: dict[str, ClientRecord] = {}
        self._usage: dict[str, UsageRecord] = {}
        self._lock = Lock()

    def register_client(self, record: ClientRecord) -> None:
        with self._lock:
            self._clients[record.client_id] = record
            self._usage.setdefault(record.client_id, UsageRecord(record.client_id))

    def get_client(self, client_id: str) -> Optional[ClientRecord]:
        with self._lock:
            return self._clients.get(client_id)

    def increment_usage(self, client_id: str) -> int:
        with self._lock:
            usage = self._usage.setdefault(client_id, UsageRecord(client_id))
            return usage.increment()

    def get_usage(self, client_id: str) -> int:
        with self._lock:
            usage = self._usage.get(client_id)
            return usage.total_calls if usage else 0
