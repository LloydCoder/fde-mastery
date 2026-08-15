"""Minimal durable queue boundary for work that must outlive an HTTP request."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Task:
    task_id: str
    kind: str
    payload: dict[str, Any]


class RedisTaskQueue:
    def __init__(self, url: str | None = None, queue_name: str = "fde:tasks"):
        try:
            import redis
        except ImportError as exc:
            raise RuntimeError("Install the redis extra to use the task queue") from exc
        self.client = redis.Redis.from_url(url or os.environ["FDE_REDIS_URL"], decode_responses=True)
        self.queue_name = queue_name

    def enqueue(self, task: Task) -> None:
        self.client.lpush(self.queue_name, json.dumps({"task_id": task.task_id, "kind": task.kind, "payload": task.payload}, separators=(",", ":")))

    def dequeue(self, timeout_seconds: int = 5) -> Task | None:
        item = self.client.brpop(self.queue_name, timeout=timeout_seconds)
        if item is None:
            return None
        _, raw = item
        data = json.loads(raw)
        return Task(task_id=str(data["task_id"]), kind=str(data["kind"]), payload=dict(data["payload"]))
