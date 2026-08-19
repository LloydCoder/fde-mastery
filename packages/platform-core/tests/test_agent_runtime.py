from __future__ import annotations

import threading
import time

import pytest

from fde_platform.runtime import (
    AgentRunStatus,
    AgentRuntime,
    AgentRuntimeError,
    ExecutionBudget,
    InMemoryRunStore,
)


def test_run_lifecycle_completes_with_bounded_output() -> None:
    runtime = AgentRuntime()
    run = runtime.create_run(
        request_id="req-1",
        tenant_id="tenant-a",
        environment="test",
        agent_id="demo-agent",
        agent_version="1.0.0",
    )

    result = runtime.execute(run.run_id, lambda payload, _ctx: {"ok": payload["value"]}, {"value": 7})

    assert result.status is AgentRunStatus.COMPLETED
    assert result.step_count == 1
    assert result.result == {"ok": 7}
    assert result.started_at is not None
    assert result.completed_at is not None


def test_runtime_records_agent_failures_without_leaking_full_exception_payload() -> None:
    runtime = AgentRuntime()
    run = runtime.create_run(
        request_id="req-2", tenant_id="tenant-a", environment="test", agent_id="demo-agent"
    )

    result = runtime.execute(run.run_id, lambda _payload, _ctx: (_ for _ in ()).throw(RuntimeError("boom")), {})

    assert result.status is AgentRunStatus.FAILED
    assert result.error_type == "RuntimeError"
    assert result.error_message == "boom"


def test_cancel_before_execution_is_terminal() -> None:
    runtime = AgentRuntime()
    run = runtime.create_run(
        request_id="req-3", tenant_id="tenant-a", environment="test", agent_id="demo-agent"
    )

    cancelled = runtime.cancel(run.run_id)
    assert cancelled.status is AgentRunStatus.CANCELLED
    assert runtime.get_run(run.run_id).status is AgentRunStatus.CANCELLED

    with pytest.raises(AgentRuntimeError):
        runtime.execute(run.run_id, lambda _payload, _ctx: None, {})


def test_checkpoint_sequences_are_monotonic_and_integrity_addressable() -> None:
    runtime = AgentRuntime()
    run = runtime.create_run(
        request_id="req-4", tenant_id="tenant-a", environment="test", agent_id="demo-agent"
    )

    first = runtime.checkpoint(run.run_id, {"step": 1})
    second = runtime.checkpoint(run.run_id, {"step": 2})

    assert first.sequence == 0
    assert second.sequence == 1
    assert len(second.state_hash) == 64
    assert runtime.store.latest_checkpoint(run.run_id) == second


def test_output_budget_fails_closed() -> None:
    runtime = AgentRuntime()
    run = runtime.create_run(
        request_id="req-5",
        tenant_id="tenant-a",
        environment="test",
        agent_id="demo-agent",
        budget=ExecutionBudget(max_output_bytes=8),
    )

    result = runtime.execute(run.run_id, lambda _payload, _ctx: {"large": "payload"}, {})

    assert result.status is AgentRunStatus.LIMIT_EXCEEDED
    assert result.result is None


def test_time_budget_is_enforced_cooperatively() -> None:
    runtime = AgentRuntime()
    run = runtime.create_run(
        request_id="req-6",
        tenant_id="tenant-a",
        environment="test",
        agent_id="demo-agent",
        budget=ExecutionBudget(max_seconds=0.01),
    )

    def slow_agent(_payload, _ctx):
        time.sleep(0.02)
        return {"ok": True}

    result = runtime.execute(run.run_id, slow_agent, {})

    assert result.status is AgentRunStatus.TIMED_OUT


def test_cancellation_signal_is_observed_after_agent_returns() -> None:
    runtime = AgentRuntime()
    run = runtime.create_run(
        request_id="req-7", tenant_id="tenant-a", environment="test", agent_id="demo-agent"
    )
    started = threading.Event()

    def cancellable_agent(_payload, _ctx):
        started.set()
        time.sleep(0.01)
        return {"ok": True}

    # The runtime is synchronous; cancellation is therefore tested by signalling from
    # another thread while the agent is executing.
    thread = threading.Thread(target=lambda: runtime.execute(run.run_id, cancellable_agent, {}))
    thread.start()
    assert started.wait(timeout=1)
    runtime.cancel(run.run_id)
    thread.join(timeout=1)

    assert runtime.get_run(run.run_id).status is AgentRunStatus.CANCELLED


def test_domain_agent_adapter_keeps_runtime_domain_neutral() -> None:
    class FakeDomainAgent:
        def evaluate(self, payload):
            return {"domain_result": payload["value"]}

    runtime = AgentRuntime(store=InMemoryRunStore())
    run = runtime.create_run(
        request_id="req-8", tenant_id="tenant-a", environment="test", agent_id="procurement"
    )

    result = runtime.execute_domain(run.run_id, FakeDomainAgent(), {"value": 42})

    assert result.status is AgentRunStatus.COMPLETED
    assert result.result == {"domain_result": 42}
