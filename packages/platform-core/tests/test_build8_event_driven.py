from datetime import datetime, timedelta, timezone

import pytest

from fde_platform.events import EventEnvelope, InMemoryInbox, InMemoryOutbox, OutboxPublisher, OutboxStatus
from fde_platform.events.outbox import OutboxConflict


def make_event(event_type: str = "agent.run.completed") -> EventEnvelope:
    return EventEnvelope.create(
        event_type=event_type,
        schema_version=1,
        source="fde.test",
        tenant_id="tenant-a",
        environment_id="production",
        subject="run-1",
        payload={"ok": True},
        partition_key="run-1",
    )


def test_event_envelope_is_immutable_and_tenant_bound() -> None:
    event = make_event()
    assert event.tenant_id == "tenant-a"
    with pytest.raises(TypeError):
        event.payload["ok"] = False  # type: ignore[index]


def test_outbox_is_ordered_and_duplicate_event_ids_are_rejected() -> None:
    outbox = InMemoryOutbox()
    first = outbox.append(make_event())
    with pytest.raises(OutboxConflict):
        outbox.append(first.event)
    second = outbox.append(make_event("agent.run.failed"))
    assert second.sequence == first.sequence + 1


def test_outbox_publish_is_at_least_once_and_marks_success() -> None:
    outbox = InMemoryOutbox()
    event = make_event()
    outbox.append(event)
    published: list[str] = []
    publisher = OutboxPublisher(outbox, lambda item: published.append(item.event_type))
    now = datetime.now(timezone.utc)
    assert publisher.drain(worker_id="worker-1", now=now) == 1
    assert published == ["agent.run.completed"]
    assert outbox.get(event.event_id).status == OutboxStatus.PUBLISHED


def test_failed_publish_is_retryable_then_dead_letters() -> None:
    outbox = InMemoryOutbox()
    event = make_event()
    outbox.append(event)
    publisher = OutboxPublisher(outbox, lambda _item: (_ for _ in ()).throw(RuntimeError("broker unavailable")))
    now = datetime.now(timezone.utc)
    publisher.drain(worker_id="worker-1", now=now, max_attempts=1)
    record = outbox.get(event.event_id)
    assert record.status == OutboxStatus.DEAD_LETTERED
    assert record.attempts == 1
    assert "broker unavailable" in (record.last_error or "")
    assert record.available_at >= now


def test_expired_lease_can_be_reclaimed_by_another_worker() -> None:
    outbox = InMemoryOutbox()
    event = make_event()
    outbox.append(event)
    now = datetime.now(timezone.utc)
    first = outbox.claim(worker_id="worker-1", now=now, lease_seconds=1)[0]
    assert first.locked_by == "worker-1"
    reclaimed = outbox.claim(worker_id="worker-2", now=now + timedelta(seconds=2), lease_seconds=1)
    assert reclaimed[0].locked_by == "worker-2"
    with pytest.raises(OutboxConflict):
        outbox.mark_published(event.event_id, worker_id="worker-1")


def test_inbox_deduplicates_per_consumer_and_retries_failed_handlers() -> None:
    inbox = InMemoryInbox()
    event = make_event()
    seen: list[str] = []
    assert inbox.consume(event, consumer="billing", handler=lambda item: seen.append(item.subject)) == "accepted"
    assert inbox.consume(event, consumer="billing", handler=lambda item: seen.append(item.subject)) == "duplicate"
    assert inbox.consume(event, consumer="analytics", handler=lambda item: seen.append(item.subject)) == "accepted"
    assert seen == ["run-1", "run-1"]

    attempts = 0
    def flaky(_item: EventEnvelope) -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("temporary")

    with pytest.raises(RuntimeError):
        inbox.consume(event, consumer="retrying", handler=flaky)
    assert inbox.consume(event, consumer="retrying", handler=flaky) == "accepted"
    assert attempts == 2
