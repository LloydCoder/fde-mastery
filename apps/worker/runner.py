"""Crash-safe worker loop over the platform's leased workflow queue.

The worker owns execution, while API processes only enqueue durable work.
Infrastructure adapters can replace the in-memory queue with Redis/RabbitMQ
or a cloud queue without changing the handler contract.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

from fde_platform.workflow.queue import WorkflowQueue, WorkflowTask


class Worker:
    def __init__(self, queue: WorkflowQueue, handler: Callable[[WorkflowTask], None], lease_seconds: float = 60.0) -> None:
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        self.queue = queue
        self.handler = handler
        self.lease_seconds = lease_seconds

    def run_once(self) -> bool:
        task = self.queue.claim(lease_seconds=self.lease_seconds)
        if task is None:
            return False
        try:
            self.handler(task)
        except Exception:
            self.queue.release(task.task_id, available_at=datetime.now(timezone.utc) + timedelta(seconds=min(self.lease_seconds, 30.0)))
            raise
        self.queue.ack(task.task_id)
        return True
