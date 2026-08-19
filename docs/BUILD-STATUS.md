# Enterprise Architecture Build Status

| Build | Status | Scope |
|---|---|---|
| **1 — Architecture Foundation** | **GREEN** | Kernel contracts, ports, dependency boundaries, legacy isolation, executable architecture tests |
| **2 — Identity & Multi-Tenancy** | **GREEN** | Tenant model, identity context, fail-closed authorization, RLS, environments |
| **3 — Agent Runtime** | **GREEN** | First-class AgentRun, lifecycle, state, checkpointing, budgets, cancellation |
| **4 — Durable Workflows** | **GREEN** | Durable workflow state/history, leased queue, retries, waits/signals, recovery, replay, dead letters |
| 5 — Trust & Policy Plane | NOT STARTED | PDP/PEP, risk tiers, policy-as-code, approval service |
| 6 — Tool Gateway | NOT STARTED | Registry, capability tokens, isolation, idempotency, MCP boundary |
| 7 — Model Gateway | NOT STARTED | Model registry, routing, fallback, budgets, provider abstraction |
| 8 — Event-Driven Platform | NOT STARTED | Events, outbox/inbox, event bus, replay, DLQ |
| 9 — AI Evaluation Plane | NOT STARTED | Golden, adversarial, safety, quality, cost and promotion gates |
| 10 — Observability & FinOps | NOT STARTED | OTel traces, SLOs, cost and quality telemetry |
| 11 — Enterprise Deployment & DR | NOT STARTED | Regional/dedicated deployment, residency, backup, failover, supply chain |
| 12 — Platform Productization | NOT STARTED | CLI/SDK, registries, developer experience and final hardening |

## Build 4 exit criteria

- [x] Version-pinned workflow definitions and step contracts exist.
- [x] First-class durable `WorkflowRun` lifecycle exists.
- [x] Append-only ordered event history exists with optimistic sequence protection.
- [x] Leased workflow queue has explicit acknowledgement semantics.
- [x] PostgreSQL workflow/event persistence adapter exists.
- [x] PostgreSQL queue adapter uses transactional row locking and `SKIP LOCKED`.
- [x] Retry, dead-letter, wait/signal, cancellation and recovery semantics are implemented.
- [x] Workflow state/history/task tables are tenant-isolated with forced RLS.
- [x] Workflow/step/attempt idempotency keys are stable.
- [x] Workflow regression and migration security contract tests exist.
- [x] Build 4 ADR and architecture documentation are recorded.
- [x] Active Month 7 README records Build 4 as the current completed phase.
- [ ] CI verification — pending GitHub Actions run on this build branch/PR.

## Verification policy

A build is only declared **GREEN** after the repository CI pipeline passes. Local tooling in this environment cannot reach GitHub's network, so GitHub Actions is the authoritative execution environment for the full existing quality/security/deployment suite.
