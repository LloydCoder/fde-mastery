# ADR-0004: First-Class Agent Runtime

- **Status:** Accepted
- **Build:** 3 — Agent Runtime
- **Date:** 2026-08-19

## Context

The platform previously exposed stable agent contracts but did not have a first-class execution lifecycle. Calling an agent directly made execution state, cancellation, limits, checkpoints, and failure semantics implicit in the caller.

Enterprise agent systems need an execution record that can cross process boundaries and later be resumed by durable workflow infrastructure. The runtime must also enforce limits independently of model/provider behavior and must not make the LLM the authority for execution safety.

## Decision

Introduce `fde_platform.runtime` as a framework-neutral execution boundary with:

1. An immutable-in-use `AgentRun` identity and explicit lifecycle.
2. Terminal-state semantics and validated state transitions.
3. Hard execution budgets for steps, elapsed time, and serialized output size.
4. Cooperative cancellation using a per-run cancellation signal.
5. Versioned checkpoints with canonicalized state hashing.
6. A `RunStore` port and thread-safe in-memory reference adapter.
7. A domain-agent compatibility adapter so existing domain implementations remain unchanged.
8. No dependency on FastAPI, database drivers, model-provider SDKs, or infrastructure adapters.

Build 3 intentionally keeps execution synchronous. Distributed scheduling, durable workflow recovery, queues, and replay are Build 4 concerns.

## Rationale

This preserves the modular-monolith migration strategy while establishing the exact boundary that future workers and workflow engines can implement. The runtime owns execution invariants; domain agents own domain behavior; infrastructure owns persistence and transport.

The design follows the current direction of agent identity and authorization work from NIST, where software/AI agents are treated as distinct executable identities and need explicit controls. It also follows OpenTelemetry's current GenAI observability model: agent invocation, model calls, and tool calls are distinct operations, and telemetry should use low-cardinality identifiers while treating content as sensitive/opt-in.

## Consequences

### Positive

- Every execution has a stable run identifier.
- Failure, cancellation, timeout, and limit states are explicit.
- Future workers can resume from a stable storage port without changing domain code.
- Runtime safety is independent of model/provider behavior.
- Tests can exercise lifecycle invariants without external infrastructure.

### Trade-offs

- The in-memory adapter is not a production durability mechanism.
- Cancellation and time limits are cooperative for synchronous Python callables.
- Build 4 must provide durable storage, queue semantics, retry/recovery policy, and workflow replay before claiming durable execution.

## Non-goals

- Workflow orchestration
- Distributed queues
- Human approval workflows
- Model routing
- Tool execution
- Agent sandboxing

Those are intentionally separated into later architecture builds.
