# Enterprise Architecture

FDE Mastery is migrating from a production-oriented modular platform into a governed enterprise AI platform. The migration is incremental: existing APIs and domain adapters remain operational while new platform boundaries are introduced behind stable contracts.

## Build 1 — Architecture Foundation

Build 1 establishes the dependency direction used by all subsequent builds:

```text
apps / API / workers
        |
        v
application services
        |
        v
fde_platform contracts + ports
        ^
        |
adapters / infrastructure / integrations
        |
        v
domain plugins
```

The platform kernel (`fde_platform`) is deliberately framework- and vendor-neutral. It owns stable contracts and ports; FastAPI, PostgreSQL, model providers, tool providers, observability exporters, and other infrastructure remain outside the kernel.

## Target bounded contexts

The migration will converge on these logical planes:

- **Control plane** — tenants, agents, versions, policies, tools, models, evaluations, deployments.
- **Data plane** — gateways, workflows, agent runtime, workers, integrations, sandboxed execution.
- **Trust plane** — identity, authorization, policy decisions, risk, approvals, audit and security controls.
- **Evaluation plane** — golden datasets, adversarial tests, regression, quality, safety, cost and promotion gates.
- **Observability plane** — traces, metrics, logs, AI telemetry, SLOs and FinOps.
- **Domain plugins** — cybersecurity, finance, healthtech, logistics, legal, revops, procurement and future custom domains.

These are logical boundaries first. They are not a mandate to create a microservice for every package.

## Dependency rules

### Allowed direction

```text
API/application -> contracts/ports -> adapters
Domain plugin  -> contracts/ports
Infrastructure -> contracts/ports
```

### Forbidden direction

```text
fde_platform -> FastAPI/PostgreSQL/provider/infrastructure
fde_platform -> domains
fde_platform -> legacy month-* curriculum
production -> month-* curriculum directly
```

### Why

This follows hexagonal architecture / ports-and-adapters principles and preserves the ability to introduce independent runtimes, workflow workers, model gateways and tool gateways later without forcing the domain layer to know their implementations.

## Compatibility policy

Existing `month-1-cybersecurity` through `month-6-revops` code remains available for historical and compatibility purposes. It is isolated as legacy material and is prohibited as a direct dependency of production architecture. See [`legacy/README.md`](../../legacy/README.md).

## Architecture enforcement

`tests/test_architecture_boundaries.py` makes these rules executable. A future refactor that introduces a forbidden kernel dependency or direct production import of a curriculum module should fail CI rather than silently erode the architecture.

## Standards basis

The architecture is informed by current platform-engineering guidance (platform as a product, golden paths and guardrails), OWASP ASVS 5.0, NIST AI RMF operationalization, and OpenTelemetry semantic-convention practices. These standards are treated as design inputs, not as substitutes for application-specific threat modeling and testing.
