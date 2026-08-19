# Month 7: Platform Layer — Enterprise FDE Platform

The capstone layer that turns the domain agents into a governed enterprise AI platform. The migration is deliberately incremental: each build establishes a stable boundary, proves it with CI, and only then becomes the foundation for the next build.

## Enterprise Architecture Migration

| Build | Capability | Status |
|---:|---|---|
| 1 | Architecture Foundation | GREEN |
| 2 | Identity & Multi-Tenancy | GREEN |
| 3 | Agent Runtime | GREEN |
| 4 | Durable Workflow Engine | GREEN |
| 5 | Trust & Policy Plane | GREEN |
| 6 | Tool Gateway | GREEN |
| 7 | Model Gateway | GREEN |
| 8 | Event-Driven Platform | GREEN |
| 9 | AI Evaluation Plane | GREEN |
| 10 | Observability & AI FinOps | GREEN |
| 11 | Enterprise Deployment & DR | IN PROGRESS |
| 12 | Platform Productization | PLANNED |

## Build 11 — Enterprise Deployment & DR

Build 11 makes deployment topology, data residency, recovery, and software supply-chain controls first-class operational contracts.

- Regional and dedicated deployment profiles
- Explicit tenant data-residency policy
- Tiered RPO/RTO targets
- Encrypted backups and restore verification
- Writer fencing and controlled failover
- Recovery-region dependency validation
- Workflow/event idempotency checks during recovery
- SBOM, dependency audit and release-provenance requirements
- Machine-readable DR policy at `deployment/dr-policy.json`
- Contract tests for recovery invariants

**Status: IN PROGRESS — implementation complete; awaiting full CI verification.**

## Architecture

```text
Application / API / Workers
            ↓
Identity + RequestContext
            ↓
Trust & Policy Plane
       ↙            ↘
Model Gateway     Tool Gateway
      ↓                ↓
Model Providers     SaaS / DB / RPC / MCP
      ↓
Durable Workflow / Agent Runtime
            ↓
Domain Agents / Infrastructure
       ↙             ↘
Evaluation Plane   Observability
       ↓              ↓
Promotion Gate   Traces / Metrics / Events
                      ↓
                 AI FinOps Ledger
                      ↓
                Tenant Budget Gate
                      ↓
          Regional / Dedicated Deployment
                      ↓
            Backup / Recovery / DR
```

The repository remains a modular monolith while these boundaries stabilize. Extraction into separate services is deferred until contracts, operational requirements and failure domains justify it.

## Deployment and DR Rules

1. Deployment topology is explicit: regional, dedicated, and recovery profiles have declared boundaries.
2. Tenant residency is validated before provisioning or migration.
3. RPO/RTO targets are policy values, not implicit infrastructure assumptions.
4. Backups are encrypted and restore verification is mandatory.
5. Failed primaries are fenced before recovery writers are promoted.
6. Identity, RLS, policy, tool, model, workflow and event invariants must pass before traffic promotion.
7. External side effects remain idempotent and reconciliation is required after failover.
8. Secrets remain outside source control and recovery credentials are independently controlled.
9. Production artifacts require SBOM, dependency-audit and provenance evidence.

## Quality Gate

A build is not complete until the repository quality workflow is green. The gate includes pytest, domain deployment smoke tests, enterprise security controls, migration validation, red-team regression, Ruff, MyPy, Bandit, dependency audit, compileall, Terraform validation, SBOM generation/validation, staging API/load smoke, production Docker runtime smoke, and Semgrep.

See [`docs/build-11-enterprise-deployment-dr.md`](../docs/build-11-enterprise-deployment-dr.md) and [`docs/adr/0011-enterprise-deployment-and-dr.md`](../docs/adr/0011-enterprise-deployment-and-dr.md).
