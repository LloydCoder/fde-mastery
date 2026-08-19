# Build 4 — Durable Workflow Engine

**Status: GREEN — complete.**

## Objective

Turn the Build 3 agent execution boundary into a crash-recoverable workflow boundary for long-running enterprise automation.

## Delivered

- Version-pinned declarative `WorkflowDefinition` and immutable step contracts.
- First-class `WorkflowRun` projection with explicit terminal states.
- Append-only ordered `WorkflowEvent` history for replay and audit.
- Optimistic sequence checking to detect concurrent history writers.
- Database-enforced immutable workflow history.
- Leased task queue with explicit acknowledgement semantics.
- Deterministic in-memory queue/store for unit and regression testing.
- PostgreSQL durable workflow run/event persistence.
- PostgreSQL leased queue adapter using transactional row locking and `SKIP LOCKED`.
- Exponential retry policy with bounded attempts and delay caps.
- Dead-letter tracking after retry exhaustion.
- Durable waiting/signalling boundary for external events.
- Operator cancellation.
- Crash recovery re-enqueue/reconciliation for non-terminal runs.
- Tenant-scoped PostgreSQL RLS with `FORCE ROW LEVEL SECURITY`.
- Composite tenant-to-workflow foreign-key binding.
- Stable workflow/step/attempt idempotency keys.
- Migration security contracts and runtime regression tests.

## Execution semantics

```text
CREATE
  ↓
RUNNING
  ↓
STEP STARTED
  ├── success ────────────────→ STEP COMPLETED
  ├── retryable failure ──────→ RETRY SCHEDULED → RUNNING
  ├── external wait ──────────→ WAITING → SIGNAL → RUNNING
  └── terminal failure ───────→ DEAD LETTERED

last STEP COMPLETED → COMPLETED
operator request     → CANCELLED
```

## Durability model

The workflow engine uses **at-least-once activity execution**. It does not claim exactly-once external side effects, because a process can fail after an external mutation and before durable acknowledgement. External activities therefore receive stable workflow/step/attempt identity and must use idempotency at their side-effect boundary.

The queue uses leases. A worker crash before acknowledgement leaves the task eligible for reclamation after the lease expires. The workflow event history is the source of truth for reconstructing progress.

The `recover()` operation reconciles non-terminal workflow runs after process/worker recovery. Queue deduplication makes repeated recovery calls safe.

## Database isolation

Workflow runs, events and tasks are tenant-owned. PostgreSQL RLS is enabled and forced, with restrictive `USING` and `WITH CHECK` policies based on the trusted transaction-scoped `fde.tenant_id` setting established in Build 2. Workflow events are immutable at the database trigger boundary, and tasks/events use composite tenant-to-run foreign keys to prevent mismatched tenant ownership.

## Why this boundary

Build 4 deliberately does **not** introduce a distributed workflow vendor or microservice fleet. The platform remains a modular monolith with explicit ports. A future worker deployment can replace the queue/store adapters without changing domain workflows or the runtime contract.

## Standards and research basis

The design follows durable-execution principles used by modern workflow systems: durable state, explicit retries, signals, deterministic versioning, idempotent activities, and recoverability. PostgreSQL documents `SKIP LOCKED` as suitable for avoiding lock contention among multiple consumers accessing queue-like tables. urlPostgreSQL SELECT / SKIP LOCKED documentationhttps://www.postgresql.org/docs/current/sql-select.html

The workflow boundary is intentionally vendor-neutral while preserving the same core durability concepts demonstrated by mature durable-execution platforms. urlTemporal workflow documentationhttps://docs.temporal.io/workflow-execution

## Verification

Build 4 passed the complete GitHub Actions **Platform Quality** workflow on PR #8, including:

- full pytest suite
- seven-domain adapter verification
- enterprise deployment gates
- 700-case golden dataset validation
- AI security regression
- enterprise security controls
- migration sequence validation
- Ruff
- MyPy
- Bandit
- pip-audit
- compileall
- Terraform validation
- SBOM generation and validation
- staging API startup/readiness
- load smoke
- production Docker build/runtime smoke
- Semgrep static security scan

**Build 4 is complete and merged into `main`.**
