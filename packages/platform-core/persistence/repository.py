"""Storage interface with in-memory implementations for platform state."""

from abc import ABC, abstractmethod
from threading import Lock
from typing import Optional

from .audit import AuditEvent
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

    @abstractmethod
    def record_audit_event(self, event: AuditEvent) -> None: ...

    @abstractmethod
    def get_audit_event(self, event_id: str) -> Optional[AuditEvent]: ...


class InMemoryPlatformRepository(PlatformRepository):
    """Thread-safe reference backend used for local development and tests."""

    def __init__(self) -> None:
        self._clients: dict[str, ClientRecord] = {}
        self._usage: dict[str, UsageRecord] = {}
        self._audit_events: dict[str, AuditEvent] = {}
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

    def record_audit_event(self, event: AuditEvent) -> None:
        with self._lock:
            self._audit_events[event.event_id] = event

    def get_audit_event(self, event_id: str) -> Optional[AuditEvent]:
        with self._lock:
            return self._audit_events.get(event_id)
