# Build 3 — Agent Runtime

**Status: GREEN candidate — CI merge gate required**

## Objective

Make agent execution a first-class platform capability rather than an implicit function call.

## Delivered

- `fde_platform.runtime.AgentRun` as the canonical execution record.
- Explicit lifecycle: `created → running → terminal` with validated transitions.
- Terminal outcomes: completed, failed, cancelled, timed out, and limit exceeded.
- `ExecutionBudget` with hard bounds for steps, elapsed time, and serialized output.
- Cooperative cancellation with a per-run cancellation signal.
- `RunCheckpoint` with monotonically increasing sequence numbers and SHA-256 state fingerprints.
- `RunStore` persistence port.
- Thread-safe in-memory store for deterministic tests and local development.
- Compatibility adapter for existing `DomainAgent` implementations.
- Runtime-focused regression suite covering success, failures, cancellation, checkpoints, output limits, time limits, and domain compatibility.
- ADR-0004 describing the boundary and non-goals.
- Platform package version bumped to 1.4.0.

## Boundary

```text
API / Worker / Workflow
          ↓
     AgentRuntime
          ↓
   AgentRun + Context
          ↓
      Domain Agent
          ↓
     RunStore port
          ↓
   Durable adapter (Build 4+)
```

The runtime does not know about FastAPI, PostgreSQL, Redis, model providers, or domain implementation modules.

## Safety invariants

1. Terminal runs cannot be executed again.
2. State transitions are explicit and validated.
3. Step, time, and output limits are enforced by the runtime.
4. Cancellation is checked before and after the agent call.
5. Checkpoints are monotonic per run and have deterministic integrity hashes.
6. Runtime failures are represented by a bounded error envelope rather than exposing arbitrary exception payloads through an API contract.
7. Domain agents remain behind the existing platform contract.

## Observability contract

Build 3 deliberately does not emit raw prompts, completions, or checkpoint state to telemetry. Future instrumentation should use stable run/agent identifiers and low-cardinality attributes. OpenTelemetry's current GenAI guidance distinguishes agent invocation, model calls, and tool calls and treats content capture as an opt-in concern because it may contain sensitive information.

## Deferred to Build 4

- durable PostgreSQL run/checkpoint persistence
- queue-backed workers
- retry/recovery orchestration
- workflow state machines
- replay and dead-letter handling
- distributed cancellation

## Verification

The repository quality workflow is the authoritative merge gate. Build 3 is complete only when the full workflow is green, including unit/integration tests, architecture checks, security scans, typing, SBOM, deployment smoke, load smoke, and production runtime smoke.
