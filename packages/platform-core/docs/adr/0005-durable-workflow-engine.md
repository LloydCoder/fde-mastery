# ADR-0005: Durable Workflow Engine

- **Status:** Accepted
- **Build:** 4
- **Date:** 2026-08-19

## Context

Build 3 introduced a first-class agent execution runtime, but synchronous execution alone cannot safely support long-running enterprise processes, worker restarts, external approvals, retries, or replay.

## Decision

Introduce a framework-neutral durable workflow boundary inside the modular monolith.

The workflow subsystem owns:

1. Version-pinned workflow definitions.
2. Durable workflow projections.
3. Append-only ordered workflow events.
4. Leased task delivery with acknowledgement.
5. Bounded retry and dead-letter semantics.
6. External wait/signal semantics.
7. Recovery/reconciliation.
8. Tenant-scoped PostgreSQL persistence.

Activities remain at-least-once and must be idempotent for external mutations.

## Alternatives considered

### Vendor-first workflow platform

Rejected for now. It would couple the platform kernel to a particular workflow runtime before the domain contracts are stable.

### Queue-only orchestration

Rejected. A queue does not provide durable workflow state, replay, version pinning or explicit lifecycle semantics.

### In-process workflow state

Rejected. Process memory cannot survive worker crashes or horizontal scaling.

### Microservices immediately

Rejected. The repository is intentionally evolving as a modular monolith until service boundaries are operationally justified.

## Consequences

### Positive

- Long-running workflows can survive process failure.
- Retry behavior is explicit and bounded.
- External waits do not consume worker memory.
- Workflow history can be replayed and audited.
- PostgreSQL provides durable state while retaining a portable port boundary.
- Queue workers can be scaled independently later.

### Negative

- At-least-once execution requires idempotent side-effect adapters.
- Durable history increases storage requirements.
- Workflow definition versioning becomes an operational responsibility.
- Distributed queue implementations must preserve lease/ack semantics.

## Security requirements

- Every workflow/run/event/task is tenant-scoped.
- PostgreSQL RLS is forced.
- No workflow may bypass Build 2 authorization context.
- Sensitive AI content is not required in workflow events.
- External actions remain subject to the Build 5 policy/approval plane.
