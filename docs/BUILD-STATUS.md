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
| **13 — Domain Intelligence Foundation** | **GREEN** | Canonical domain promotion contract, domain registry, representative evaluation fixtures, first-class Custom domain |
| **14 — FDE Engagement & Workflow Engine** | **GREEN** | Tenant-scoped engagement lifecycle, value metrics, evidence gates, promotion workflow and durable-workflow compilation |
| **15 — Enterprise Integration Plane** | **GREEN** | Tenant/environment integration registry, managed credential references, OAuth PKCE, authenticated webhooks, SSRF-safe outbound policy, retry/rate limits, integration persistence and Tool Gateway bridge |
| **16 — MCP / A2A Interoperability** | **GREEN** | MCP 2026 protocol contracts, tenant/scoped tool discovery, A2A Agent Cards, skill authorization, tenant-scoped task bridge, endpoint allowlisting and protocol conformance boundaries |
| **17 — Advanced AI / Agent Security Plane** | **IN PROGRESS** | Risk-tiered action gate, agent security context, capability/autonomy controls, prompt-injection screening, output redaction, memory provenance and secure Tool Gateway adapter |

## Build 13 verification

- [x] DomainDescriptor carries lifecycle, risk, approval, evaluation and representative-data metadata.
- [x] Canonical domain registry exists outside the framework-neutral kernel.
- [x] Eight first-class domains are registered: Cybersecurity, Finance, HealthTech, Logistics, Legal, RevOps, Procurement and Custom.
- [x] Custom domain is configuration-driven and recommendation-only with no autonomous side effects.
- [x] Synthetic representative promotion fixtures cover every first-class domain.
- [x] Domain promotion contract tests cover catalog completeness, fixture coverage, factory loading, health, HITL requirements and fail-closed unknown-domain behavior.
- [x] Custom domain is registered through the existing resilient platform router.
- [x] Build 13 ADR and implementation documentation are recorded.
- [x] Platform Quality run #431 passed all jobs and checks, including production Docker build/runtime smoke and Semgrep.
- [x] Build 13 PR was merged only after the complete CI gate was green.

## Build 14 verification

- [x] Tenant-scoped FDE engagement contract exists.
- [x] Measurable baseline and target metrics are first-class.
- [x] Acceptance criteria are explicitly bound to lifecycle stages.
- [x] Evidence references are explicit and can be tied to individual criteria.
- [x] Lifecycle transitions fail closed.
- [x] Promotion gates define evidence and human-approval requirements.
- [x] Production requires deployment and approval evidence.
- [x] Lifecycle compiles to the existing durable WorkflowDefinition contract without introducing a second runtime.
- [x] Contract tests cover transition safety, promotion gates, compilation, evidence and tenant scoping.
- [x] Build 14 ADR and implementation documentation are recorded.
- [x] Platform Quality run #436 passed every job and check, including tests, security, static analysis, SBOM, staging/load smoke, production Docker runtime smoke and Semgrep.
- [x] Build 14 PR was merged only after the complete CI gate was green.

## Build 15 verification

- [x] Tenant/environment integration registry and fail-closed lifecycle are verified.
- [x] Credential material is excluded from integration contracts; only managed secret references are accepted.
- [x] OAuth authorization-code + PKCE/S256 and state primitives are verified.
- [x] Webhook HMAC verification, timestamp tolerance and replay/idempotency controls are verified.
- [x] Outbound integration HTTPS, host allowlisting, private/reserved-network rejection and redirect blocking are verified.
- [x] Bounded retry and Retry-After handling are verified.
- [x] Connector-level rate limiting is verified, including zero-based timestamp refill behavior.
- [x] Integration actions are bridged through the existing Tool Gateway rather than a second executor.
- [x] Tenant-isolated integration and webhook-delivery persistence migration is validated.
- [x] Build 15 ADR and implementation documentation are recorded.
- [x] Platform Quality run #451 passed all jobs and checks, including tests, security, static analysis, SBOM, staging/load smoke, production Docker runtime smoke and Semgrep.
- [x] The initial Build 15 CI failures were fixed rather than bypassed: token-bucket refill semantics and Bandit's non-cryptographic jitter finding were corrected, followed by a complete green rerun.
- [x] Final documentation verification passed in Platform Quality run #453.
- [x] Build 15 PR #25 was merged after the complete CI gate was green.

## Build 16 verification

- [x] MCP protocol versions are explicit and validated.
- [x] MCP request tenant and authorization contexts are bound and fail closed on mismatch.
- [x] MCP routing headers are validated against request bodies.
- [x] Tenant-scoped MCP tool catalog and scope gates are verified.
- [x] MCP tool risk annotations are represented without treating annotations as authorization.
- [x] A2A Agent Cards, interfaces, skills and security schemes are represented as typed contracts.
- [x] A2A discovery is tenant-scoped and skill-aware.
- [x] A2A endpoint host allowlisting is verified.
- [x] A2A requests require explicit authorization and skill checks.
- [x] A2A tasks map to the existing durable workflow runtime rather than a second executor.
- [x] Integration registry naming collision discovered during Build 16 review is resolved.
- [x] Build 16 ADR and implementation documentation are recorded.
- [x] Platform Quality run #471 passed all jobs and checks, including tests, security, static analysis, SBOM, staging/load smoke, production Docker runtime smoke and Semgrep.
- [x] Final documentation verification passed in Platform Quality run #473.
- [x] Build 16 PR #26 was merged after the complete CI gate was green.

## Build 17 verification

- [ ] Risk-tiered agent action gate is verified.
- [ ] Agent security context is tenant/agent/request bound.
- [ ] Capability allowlisting and autonomy budget controls are verified.
- [ ] High/critical actions require explicit approval evidence.
- [ ] Untrusted/external context cannot perform irreversible actions.
- [ ] Prompt-injection screening is deterministic and defense-in-depth.
- [ ] Credential-shaped output is redacted before leaving the trust boundary.
- [ ] Memory records carry provenance/trust and can be tenant/trust filtered.
- [ ] Secure Tool Gateway adapter blocks unsafe actions before execution.
- [ ] Build 17 ADR and implementation documentation are recorded.
- [ ] Platform Quality and Semgrep workflows are green.
- [ ] Build 17 PR is merged only after the complete CI gate is green.

## Verification policy

A build is only declared **GREEN** after the repository CI pipeline passes tests, security scans, migration validation, static analysis, SBOM validation, staging/load smoke, and production Docker runtime smoke.
