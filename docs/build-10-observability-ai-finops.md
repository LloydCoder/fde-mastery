# Build 10 — Observability & AI FinOps

## Objective

Make production execution observable end-to-end and make AI cost a governed, tenant-scoped platform concern.

## Delivered

- framework-neutral telemetry sink contract
- structured observation model with timezone and duration validation
- bounded metric dimensions to reduce cardinality risk
- framework-neutral metrics sink contract
- tenant-scoped AI cost records
- explicit model/run provenance for cost attribution
- fail-closed cost budgets
- thread-safe reference cost ledger
- regression/security tests
- ADR-0010

## Target telemetry model

```text
Agent Run
   │
   ├── Workflow spans/events
   │       ├── Tool operations
   │       └── Model operations
   │               ├── model/provider identity
   │               ├── token usage
   │               └── latency
   │
   └── Cost Record ──> Tenant Budget ──> ALLOW / REJECT
```

OpenTelemetry adapters should map platform observations to standard semantic conventions. GenAI message content is opt-in because it can contain sensitive or personal information.

## FinOps rules

1. Cost records must identify tenant, execution run and model.
2. Token counts and cost values must be non-negative.
3. Budgets are tenant-scoped and cannot be applied across tenants.
4. A budget breach is fail-closed.
5. Production cost persistence must be idempotent against execution/provider event identifiers.
6. Provider list prices are configuration, not hard-coded assumptions in the kernel.
7. Reconciliation is required before treating internal estimates as invoice truth.

## Observability rules

1. Prefer standard OpenTelemetry names and attributes over platform-specific duplicates.
2. Keep baseline attributes bounded and low-cardinality.
3. Do not record prompt/completion/tool content by default.
4. Correlate traces across agent, workflow, model, tool and messaging boundaries.
5. Record errors as structured telemetry without leaking secrets.
6. Treat telemetry as sensitive operational data with retention and access controls.

## Quality gate

Build 10 is complete only after the full Platform Quality workflow passes tests, security scans, migration validation, static analysis, SBOM validation, staging/load smoke, production Docker runtime smoke and Semgrep.

## Standards basis

The implementation follows OpenTelemetry Semantic Conventions and GenAI observability guidance, including model/token/latency attributes and explicit caution around sensitive message content. It also uses NIST AI RMF / GenAI Profile principles for trustworthy measurement and monitoring.
