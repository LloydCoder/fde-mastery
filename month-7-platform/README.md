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
| 10 | Observability & AI FinOps | IN PROGRESS |
| 11 | Enterprise Deployment & DR | NEXT |
| 12 | Platform Productization | PLANNED |

## Build 10 — Observability & AI FinOps

Build 10 establishes production telemetry and tenant-scoped AI cost governance.

- Framework-neutral telemetry and metrics contracts
- OpenTelemetry-compatible semantic mapping boundary
- Bounded, low-cardinality metric dimensions
- Agent/workflow/model/tool/messaging correlation model
- Tenant-scoped AI cost records with model and run provenance
- Explicit fail-closed cost budgets
- Reference cost ledger with production adapter boundary
- Privacy rule: GenAI content is opt-in, not baseline telemetry
- Regression/security coverage

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
```

The repository remains a modular monolith while these boundaries stabilize. Extraction into separate services is deferred until contracts, operational requirements and failure domains justify it.

## Observability Security Rules

1. Prefer established OpenTelemetry semantic conventions over custom duplicate attributes.
2. Baseline telemetry uses bounded, low-cardinality dimensions.
3. Prompt, completion and tool content are never required for baseline observability.
4. Sensitive GenAI content requires explicit opt-in and appropriate access/retention controls.
5. Execution identifiers correlate agent, workflow, model, tool and messaging operations.
6. Telemetry errors must not leak credentials, tokens or sensitive payloads.

## AI FinOps Rules

1. Cost records are tenant-scoped.
2. Every record identifies execution run and model.
3. Token counts and costs are non-negative and validated.
4. Budgets cannot be applied across tenants.
5. Budget breaches fail closed.
6. Production cost persistence must use idempotent correlation keys.
7. Provider pricing is configuration; internal estimates require reconciliation before invoice-level claims.

## Project Structure

```text
month-7-platform/
├── fde_platform/
│   ├── contracts/             # Stable cross-boundary contracts
│   ├── identity/              # Principal, tenant, request context
│   ├── authorization/         # Trust & policy boundary
│   ├── runtime/               # Agent execution runtime
│   ├── workflow/              # Durable workflows and queues
│   ├── tools/                 # Tool gateway
│   ├── models/                # Model gateway and provider boundary
│   ├── evaluation/            # Evaluation contracts, harness and scorers
│   └── observability/         # Telemetry, metrics and AI FinOps contracts
├── custom_agents/             # Compatibility/domain-facing agent tooling
├── persistence/               # PostgreSQL adapters and migrations
├── integrations/              # External system adapters
├── evaluation/                # Existing datasets/evaluation compatibility layer
├── observability/             # Existing telemetry compatibility layer
├── deployment/                # Container/Terraform deployment
└── tests/                     # Regression/security/architecture tests
```

## Quality Gate

A build is not complete until the repository quality workflow is green. The gate includes pytest, domain deployment smoke tests, enterprise security controls, migration validation, red-team regression, Ruff, MyPy, Bandit, dependency audit, compileall, Terraform validation, SBOM generation/validation, staging API/load smoke, production Docker runtime smoke, and Semgrep.

See [`docs/build-10-observability-ai-finops.md`](../docs/build-10-observability-ai-finops.md) and [`docs/adr/0010-observability-and-ai-finops.md`](../docs/adr/0010-observability-and-ai-finops.md).
