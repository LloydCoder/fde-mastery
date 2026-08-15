"""Tamper-evident audit chaining for append-only event streams."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class ChainedEvent:
    event_id: str
    payload: dict
    previous_hash: str
    event_hash: str


def chain_event(event_id: str, payload: dict, previous_hash: str = "") -> ChainedEvent:
    canonical = json.dumps({"event_id": event_id, "payload": payload, "previous_hash": previous_hash}, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return ChainedEvent(event_id, payload, previous_hash, digest)


def verify_chain(events: list[ChainedEvent]) -> bool:
    previous = ""
    for event in events:
        expected = chain_event(event.event_id, event.payload, previous)
        if event.previous_hash != previous or event.event_hash != expected.event_hash:
            return False
        previous = event.event_hash
    return True
