# ADR-0013 — Enterprise repository structure

- **Status:** Accepted
- **Date:** 2026-08-19
- **Decision:** Adopt a monorepo structure that separates deployable applications, reusable packages, historical curriculum, documentation and repository-level tests while keeping the production platform distribution cohesive during the first structural migration.

## Context

Builds 1–12 established the enterprise platform boundaries, but the repository still exposed the historical `month-*` layout at its root. That made the production platform and learning curriculum appear to be peers even though they have different lifecycle, dependency and governance requirements.

## Decision

Move the complete Month 7 production distribution to `packages/platform-core`. Move Months 1–6 into `legacy/curriculum`. Establish top-level `apps`, `packages`, `domains`, `infrastructure`, and `tests` ownership boundaries.

The platform package remains internally cohesive for this migration. This avoids a risky simultaneous extraction of runtime, deployment and domain packages. Future extractions require explicit package contracts, import updates, deployment updates and green CI.

## Rationale

PyPA documents `pyproject.toml`-based source trees and recommends explicit packaging boundaries; the repository therefore treats `packages/platform-core` as a real distribution boundary rather than merely a cosmetic folder. The structure also preserves a clear separation between production code and historical curriculum.

## Consequences

- Production code has an unambiguous package home.
- Historical curriculum cannot be mistaken for production dependencies.
- CI and deployment paths are explicit and deterministic.
- Future package extraction can happen incrementally behind contract tests.
- Git tree moves preserve existing blob identity where possible, minimizing unnecessary content churn.
