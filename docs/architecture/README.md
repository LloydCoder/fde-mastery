# Enterprise Architecture

## Canonical repository structure

```text
apps/                 deployable application entrypoints
packages/platform-core/ provider-neutral enterprise platform kernel
domains/              business/domain implementations
infrastructure/       deployment, IaC, migrations and runtime assets
tests/                unit, integration, contract, security and architecture tests
docs/                 architecture, ADRs, operations and standards
legacy/curriculum/    historical Months 1-6 curriculum; not production runtime
```

## Dependency rule

Production code must depend inward on stable platform contracts. Domain implementations may depend on platform contracts but must not reach into infrastructure adapters directly. Application entrypoints compose the platform and adapters. Legacy curriculum is isolated from production packages.

## Enterprise planes

1. Identity and tenancy
2. Agent runtime
3. Durable workflow
4. Trust and policy
5. Tool gateway
6. Model gateway
7. Eventing
8. Evaluation
9. Observability and FinOps
10. Deployment and disaster recovery
11. Developer/product surface

## Cross-cutting invariants

Tenant context is explicit. Authorization is fail-closed. Side effects are idempotent where delivery is at-least-once. Secrets and provider SDKs remain behind controlled boundaries. Security and architecture checks are release gates.
