# Enterprise Architecture Build Status

| Build | Status | Scope |
|---|---|---|
| **1 — Architecture Foundation** | **GREEN** | Kernel contracts, ports, dependency boundaries, legacy isolation, executable architecture tests |
| **2 — Identity & Multi-Tenancy** | **GREEN** | Tenant model, identity context, fail-closed authorization, RLS, environments |
| **3 — Agent Runtime** | **GREEN** | First-class AgentRun, lifecycle, state, checkpointing, budgets, cancellation |
| **4 — Durable Workflows** | **GREEN** | Durable workflow state/history, leased queue, retries, waits/signals, recovery, replay, dead letters |
| **5 — Trust & Policy Plane** | **GREEN** | Fail-closed PDP, versioned policy rules, risk tiers, human approval boundary, tamper-evident authorization audit |
| **6 — Tool Gateway** | **GREEN** | Tool registry, capability-scoped execution, tenant/request isolation, approval boundary, idempotency |
| **7 — Model Gateway** | **GREEN** | Model registry, capability/data-class controls, policy gate, deterministic routing, retry-aware fallback, provider abstraction |
| **8 — Event-Driven Platform** | **IN PROGRESS** | Versioned events, transactional outbox, idempotent inbox, leased publishing, retry/dead-letter semantics, tenant-isolated persistence |
| 9 — AI Evaluation Plane | NOT STARTED | Golden, adversarial, safety, quality, cost and promotion gates |
| 10 — Observability & FinOps | NOT STARTED | OTel traces, SLOs, cost and quality telemetry |
| 11 — Enterprise Deployment & DR | NOT STARTED | Regional/dedicated deployment, residency, backup, failover, supply chain |
| 12 — Platform Productization | NOT STARTED | CLI/SDK, registries, developer experience and final hardening |

## Build 8 exit criteria

- [x] Immutable, versioned event envelope exists.
- [x] Explicit tenant/environment context is required for events.
- [x] Transactional outbox persistence migration exists.
- [x] Idempotent consumer inbox persistence migration exists.
- [x] Outbox leasing and bounded retry semantics exist.
- [x] Dead-letter terminal state exists.
- [x] Consumer deduplication is scoped by consumer and event ID.
- [x] Database RLS is FORCE-enabled for event persistence.
- [x] Event-driven regression/security tests exist.
- [x] Build 8 ADR is recorded.
- [ ] GitHub Actions Platform Quality workflow passes all jobs and checks on the Build 8 PR.
- [ ] Build 8 PR is merged only after the complete CI gate is green.

## Verification policy

A build is only declared **GREEN** after the repository CI pipeline passes. Build 8 is not complete until the complete Platform Quality workflow passes tests, security scans, migration validation, static analysis, SBOM validation, staging/load smoke, and production Docker runtime smoke.
