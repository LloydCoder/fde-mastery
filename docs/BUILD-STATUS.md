# Enterprise Architecture Build Status

| Build | Status | Scope |
|---|---|---|
| **1 — Architecture Foundation** | **GREEN** | Kernel contracts, ports, dependency boundaries, legacy isolation, executable architecture tests |
| 2 — Identity & Multi-Tenancy | NOT STARTED | Tenant model, RBAC/ABAC, resource authorization, RLS, environments |
| 3 — Agent Runtime | NOT STARTED | First-class AgentRun, lifecycle, state, checkpointing, budgets, cancellation |
| 4 — Durable Workflows | NOT STARTED | Durable execution, replay, retries, HITL pauses, compensation |
| 5 — Trust & Policy Plane | NOT STARTED | PDP/PEP, risk tiers, policy-as-code, approval service |
| 6 — Tool Gateway | NOT STARTED | Registry, capability tokens, isolation, idempotency, MCP boundary |
| 7 — Model Gateway | NOT STARTED | Model registry, routing, fallback, budgets, provider abstraction |
| 8 — Event-Driven Platform | NOT STARTED | Events, outbox/inbox, event bus, replay, DLQ |
| 9 — AI Evaluation Plane | NOT STARTED | Golden, adversarial, safety, quality, cost and promotion gates |
| 10 — Observability & FinOps | NOT STARTED | OTel traces, SLOs, cost and quality telemetry |
| 11 — Enterprise Deployment & DR | NOT STARTED | Regional/dedicated deployment, residency, backup, failover, supply chain |
| 12 — Platform Productization | NOT STARTED | CLI/SDK, registries, developer experience and final hardening |

## Build 1 exit criteria

- [x] Framework-neutral `fde_platform` kernel exists in the active Month 7 package.
- [x] Agent/domain/execution contracts are defined.
- [x] Agent/model/tool/repository/event-bus ports are defined.
- [x] Kernel dependency restrictions are encoded as executable tests.
- [x] Production code is prohibited from directly importing Month 1–6 curriculum modules.
- [x] Legacy curriculum boundary is documented.
- [x] Packaging includes the new kernel.
- [x] Architecture ADR is recorded.
- [x] Active Month 7 README records the current phase.
- [ ] CI verification — pending GitHub Actions run on this build branch/PR.

## Verification policy

A build is only declared **GREEN** after the repository CI pipeline passes. Local tooling in this environment cannot reach GitHub's network, so GitHub Actions is the authoritative execution environment for the full existing quality/security/deployment suite.
