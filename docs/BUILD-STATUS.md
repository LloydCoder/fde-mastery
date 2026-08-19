# Enterprise Architecture Build Status

| Build | Status | Scope |
|---|---|---|
| **1 — Architecture Foundation** | **GREEN** | Kernel contracts, ports, dependency boundaries, legacy isolation, executable architecture tests |
| **2 — Identity & Multi-Tenancy** | **GREEN** | Tenant model, identity context, fail-closed authorization, RLS, environments |
| **3 — Agent Runtime** | **GREEN** | First-class AgentRun, lifecycle, state, checkpointing, budgets, cancellation |
| **4 — Durable Workflows** | **GREEN** | Durable workflow state/history, leased queue, retries, waits/signals, recovery, replay, dead letters |
| **5 — Trust & Policy Plane** | **GREEN** | Fail-closed PDP, versioned policy rules, risk tiers, human approval boundary, tamper-evident authorization audit |
| **6 — Tool Gateway** | **GREEN** | Tool registry, capability-scoped execution, tenant/request isolation, approval boundary, idempotency |
| 7 — Model Gateway | IN PROGRESS | Model registry, routing, fallback, budgets, provider abstraction |
| 8 — Event-Driven Platform | NOT STARTED | Events, outbox/inbox, event bus, replay, DLQ |
| 9 — AI Evaluation Plane | NOT STARTED | Golden, adversarial, safety, quality, cost and promotion gates |
| 10 — Observability & FinOps | NOT STARTED | OTel traces, SLOs, cost and quality telemetry |
| 11 — Enterprise Deployment & DR | NOT STARTED | Regional/dedicated deployment, residency, backup, failover, supply chain |
| 12 — Platform Productization | NOT STARTED | CLI/SDK, registries, developer experience and final hardening |

## Build 7 exit criteria

- [x] Immutable, versioned model definitions exist.
- [x] Explicit model capability allowlists exist.
- [x] Data-classification allowlists are enforced before provider invocation.
- [x] Provider-neutral adapter boundary exists.
- [x] Central model registry and explicit model/version routes exist.
- [x] Retry-aware deterministic fallback exists.
- [x] Non-retryable authorization/policy/validation failures do not fail over.
- [x] Model output-token budgets are enforced.
- [x] Policy evaluation occurs before provider invocation.
- [x] Explicit model response/error envelope exists.
- [x] Model gateway security regression tests exist.
- [x] Build 7 ADR and implementation documentation are recorded.
- [ ] GitHub Actions Platform Quality workflow passes all jobs and checks on the Build 7 PR.
- [ ] Build 7 PR is merged only after the complete CI gate is green.

## Verification policy

A build is only declared **GREEN** after the repository CI pipeline passes. Build 7 must pass the complete Platform Quality workflow, including tests, security scans, migration validation, static analysis, SBOM validation, staging/load smoke, and production Docker runtime smoke.
