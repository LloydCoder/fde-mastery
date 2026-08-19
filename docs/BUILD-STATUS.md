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
| **9 — AI Evaluation Plane** | **GREEN** | Golden, adversarial, safety, quality, cost and promotion gates |
| **10 — Observability & AI FinOps** | **GREEN** | OTel-compatible telemetry, bounded dimensions, execution correlation, tenant cost ledger, fail-closed AI budgets |
| **11 — Enterprise Deployment & DR** | **GREEN** | Regional/dedicated deployment, residency, backup, failover, recovery evidence, supply-chain controls |
| **12 — Platform Productization** | **GREEN** | Stable provider-neutral developer surface, machine-readable capability manifest, enterprise repository structure, contract coverage and final CI hardening |

## Build 11 verification

- [x] Enterprise deployment profiles are explicitly documented.
- [x] Regional and dedicated residency boundaries are defined.
- [x] RPO/RTO tiers are machine-readable.
- [x] Recovery ordering requires writer fencing before state restoration.
- [x] Backup encryption, retention and restore verification requirements are defined.
- [x] Recovery validates identity, tenant isolation, RLS and policy gates before promotion.
- [x] Workflow/event/tool/model side effects remain idempotent during recovery.
- [x] SBOM, dependency audit and release provenance are production promotion requirements.
- [x] Build 11 ADR and implementation documentation are recorded.
- [x] DR policy contract tests exist.
- [x] Platform Quality run #368 passed all jobs and checks.
- [x] Build 11 PR was merged only after the complete CI gate was green.

## Build 12 verification

- [x] Provider-neutral `platformctl` developer entry point exists.
- [x] Machine-readable platform capability manifest exists.
- [x] Manifest completeness is covered by contract tests.
- [x] Productization boundary cannot bypass identity, policy, tool or model gates.
- [x] Production platform distribution is owned by `packages/platform-core`.
- [x] Historical Months 1–6 curriculum is separated under `legacy/curriculum`.
- [x] Repository ownership boundaries for apps, packages, domains, infrastructure and tests are documented.
- [x] CI, evaluation and release-attestation workflows target the new platform package location.
- [x] ADR-0013 records the repository structure decision.
- [x] Build 12 architecture and security documentation are recorded.
- [x] Platform Quality run #379 passed all jobs and checks, including tests, security scans, migration validation, static analysis, SBOM validation, staging/load smoke and production Docker runtime smoke.
- [x] Build 12 PR was merged only after the complete CI gate was green.

## Verification policy

A build is only declared **GREEN** after the repository CI pipeline passes tests, security scans, migration validation, static analysis, SBOM validation, staging/load smoke, and production Docker runtime smoke.

Build 12 verification also confirmed the repository-structure migration does not leave production adapters dependent on pre-migration Month 1–6 paths; the legacy loader resolves curriculum agents from `legacy/curriculum` while retaining isolated schema loading.
