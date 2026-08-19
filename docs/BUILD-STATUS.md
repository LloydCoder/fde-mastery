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
| **8 — Event-Driven Platform** | **GREEN** | Versioned events, transactional outbox, idempotent inbox, leased publishing, retry/dead-letter semantics, tenant-isolated persistence |
| **9 — AI Evaluation Plane** | **IN PROGRESS** | Golden, adversarial, safety, quality, cost and promotion gates |
| 10 — Observability & FinOps | NOT STARTED | OTel traces, SLOs, cost and quality telemetry |
| 11 — Enterprise Deployment & DR | NOT STARTED | Regional/dedicated deployment, residency, backup, failover, supply chain |
| 12 — Platform Productization | NOT STARTED | CLI/SDK, registries, developer experience and final hardening |

## Build 9 exit criteria

- [x] Immutable evaluation cases and versioned datasets exist.
- [x] SHA-256 case and dataset fingerprints exist.
- [x] Golden and adversarial evaluation categories exist.
- [x] Safety regression scorer fails closed on configured prohibited terms.
- [x] Quality scorer contracts are explicit and bounded.
- [x] Cost and latency are captured per evaluation result.
- [x] Evaluation runs record model and dataset provenance.
- [x] Explicit promotion thresholds produce PROMOTE/REJECT decisions.
- [x] Evaluation content is treated as data, not executable code.
- [x] Build 9 ADR and implementation documentation are recorded.
- [x] Evaluation regression tests exist.
- [ ] GitHub Actions Platform Quality workflow passes all jobs and checks on the Build 9 PR.
- [ ] Build 9 PR is merged only after the complete CI gate is green.

## Verification policy

A build is only declared **GREEN** after the repository CI pipeline passes tests, security scans, migration validation, static analysis, SBOM validation, staging/load smoke, and production Docker runtime smoke.
