# ADR 0002: Enterprise platform boundaries

- **Status:** Accepted
- **Date:** 2026-08-19
- **Scope:** Build 1 architecture foundation

## Context

FDE Mastery has accumulated domain agents, persistence, security, observability, deployment and evaluation capabilities in a working modular platform. The next evolution requires durable workflows, tenant-aware execution, policy enforcement, model/tool gateways, event-driven integration and independent workload scaling.

A direct microservice rewrite would increase operational complexity before the boundaries are stable. A better migration path is to establish explicit contracts and ports first, then extract runtime services only when independent scaling or isolation justifies it.

## Decision

1. Introduce `fde_platform` as the framework-neutral platform kernel.
2. Put stable cross-cutting contracts under `fde_platform/contracts`.
3. Put infrastructure/application boundaries under `fde_platform/ports`.
4. Keep concrete frameworks, databases, model providers and integrations outside the kernel.
5. Treat `domains/*` as domain plugins that depend on platform contracts, not the reverse.
6. Preserve Month 1–6 directories as legacy curriculum/compatibility material and prohibit direct production imports.
7. Enforce dependency direction with executable architecture tests.
8. Prefer a modular monolith during migration; extract services only where scale, security isolation, fault containment or deployment independence requires it.

## Consequences

### Positive

- Stable boundaries can survive provider and infrastructure changes.
- Future agent/workflow runtimes can be introduced without rewriting domain code.
- Architecture regressions become CI failures.
- Historical curriculum remains available without becoming a production dependency.
- The repository gains a credible path from modular monolith to distributed enterprise platform.

### Negative

- There are temporarily two layers: existing operational modules and the new kernel contracts.
- Some existing modules will require incremental migration in later builds.
- Architecture tests add maintenance overhead, which is intentional: the tests protect the platform's most important invariants.

## Alternatives rejected

### Immediate microservices

Rejected because service boundaries are not yet sufficiently mature and would create unnecessary deployment, networking and operational overhead.

### Keep the current structure unchanged

Rejected because the current structure does not provide a strong enough dependency boundary for the planned control/data/trust planes.

### Move everything into `src/` immediately

Rejected for Build 1 because it would create a broad packaging migration unrelated to the immediate architectural boundary problem. Packaging layout can be revisited when the application/service split is introduced.
