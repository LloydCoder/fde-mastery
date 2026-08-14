"""Contract tests shared by persistence backends."""

from persistence.models import ClientRecord
from persistence.repository import InMemoryPlatformRepository


def exercise_repository(repository):
    record = ClientRecord.create("client-1", "Example", ["finance", "legal"])
    repository.register_client(record)
    loaded = repository.get_client("client-1")
    assert loaded is not None
    assert loaded.client_name == "Example"
    assert loaded.domains == ("finance", "legal")
    assert repository.get_usage("client-1") == 0
    assert repository.increment_usage("client-1") == 1
    assert repository.increment_usage("client-1") == 2
    assert repository.get_usage("client-1") == 2


def test_in_memory_repository_contract():
    exercise_repository(InMemoryPlatformRepository())
