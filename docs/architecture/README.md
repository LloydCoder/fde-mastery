# Enterprise architecture

FDE Mastery is a governed AI execution platform implemented as a modular monolith. The canonical production package is `packages/platform-core`. Historical Months 1–6 curriculum is isolated under `legacy/curriculum` and is not part of the production dependency graph.

## Logical planes

- **Control plane:** tenants, agent/tool/model/policy registries, evaluations, deployments, configuration and approvals.
- **Data plane:** API gateway, durable workflows, agent runtime, workers, integrations and domain adapters.
- **Trust plane:** identity, authorization, policy decisions, risk, approvals, audit and security controls.
- **Evaluation plane:** golden datasets, adversarial tests, regression, quality, safety, cost and promotion gates.
- **Observability plane:** traces, metrics, logs, execution correlation, SLOs and FinOps.
- **Domain adapters:** cybersecurity, finance, healthtech, logistics, legal, revops, procurement and custom workflows.

These are logical boundaries. They do not imply that every plane must be deployed as a separate service.

## Repository ownership map

| Path | Responsibility |
|---|---|
| `packages/platform-core/fde_platform` | Stable platform contracts and kernel boundaries |
| `packages/platform-core/deployment` | API gateway and deployment integration |
| `packages/platform-core/shared_orchestrator` | Agent routing and orchestration |
| `packages/platform-core/security` | Trust, policy and security controls |
| `packages/platform-core/persistence` | Persistence adapters and migrations |
| `packages/platform-core/domains` | First-class domain implementations |
| `packages/platform-core/evaluation` | Evaluation datasets, benchmarks and promotion signals |
| `apps/worker` | Worker application boundary |
| `sdks` | Python and TypeScript clients |
| `platformctl` | Platform inspection CLI |
| `legacy/curriculum` | Historical learning curriculum only |

## Dependency rules

Preferred direction:

```text
API / application / worker
          |
          v
platform contracts and ports
          ^
          |
adapters / persistence / integrations
          |
          v
domain implementations
```

The platform kernel should not depend on FastAPI, database vendors, model providers, infrastructure implementations or historical curriculum packages. Domain and infrastructure adapters should depend on stable contracts rather than reverse-importing application internals.

## Trust boundaries

- Authentication establishes identity; authorization evaluates permissions for a tenant and resource.
- Tenant identity must be propagated and checked server-side.
- Model output is untrusted data and must never grant permissions.
- Tool execution is constrained by explicit capabilities, policy and tenant context.
- High-impact actions require an explicit, auditable, scoped and time-bounded approval path.
- External inputs, including prompts, tool results, webhooks and provider responses, are untrusted.
- Decision lineage records evidence references and execution metadata, not hidden chain-of-thought.

## Runtime and deployment

The repository provides API, worker and deployment boundaries with PostgreSQL/Redis production Compose references. Production promotion remains conditional on customer-specific integration, evaluation, staging, shadow-mode, human-approval, recovery and rollback evidence.

See [Production Readiness](../PRODUCTION-READINESS.md), [Deployment](../../DEPLOYMENT.md), and [CI Verification Contract](../CI-VERIFICATION-CONTRACT.md).

## Architecture decision records

Accepted decisions are recorded under [docs/adr](../adr/). Update or add an ADR when a change materially alters a platform boundary, trust assumption, data lifecycle, deployment topology or public contract.
