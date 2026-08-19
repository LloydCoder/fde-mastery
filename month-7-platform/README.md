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
| 9 | AI Evaluation Plane | IN PROGRESS |
| 10 | Observability & AI FinOps | NEXT |
| 11 | Enterprise Deployment & DR | PLANNED |
| 12 | Platform Productization | PLANNED |

## Build 9 — AI Evaluation Plane

Build 9 establishes evaluation as a first-class platform capability and release gate.

- Immutable evaluation cases and versioned datasets
- SHA-256 case and dataset fingerprints
- Golden and adversarial evaluation categories
- Safety regression scorer with fail-closed prohibited-output checks
- Deterministic quality scoring contracts
- Cost and latency measurement per result
- Model and dataset provenance on every evaluation run
- Explicit threshold-based `PROMOTE` / `REJECT` decisions
- Evaluation inputs remain data and are never executed as code
- Framework-neutral evaluation harness and scorers
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
            ↓
      Evaluation Plane
   ↙      ↓       ↘
Golden  Safety  Adversarial
   \      |       /
    Quality + Cost
          ↓
    Promotion Gate
      ↙        ↘
  PROMOTE     REJECT
```

The repository remains a modular monolith while these boundaries stabilize. Extraction into separate services is deferred until contracts, operational requirements and failure domains justify it.

## Evaluation Security Rules

1. Dataset versions and fingerprints must make silent test-set mutation detectable.
2. Evaluation cases are untrusted data and must never be interpreted as executable code.
3. Safety failures are independent of aggregate quality and cannot be hidden by a high mean score.
4. Every evaluation run records the tested model reference and dataset fingerprint.
5. Promotion thresholds are explicit and version-controlled.
6. Agentic evaluations must record relevant tools, budgets and harness configuration before being used as capability evidence.
7. Evaluation reports must consider validity hazards such as reward hacking, contamination, shortcutting and evaluation awareness.

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
│   └── evaluation/            # Evaluation contracts, harness and scorers
├── custom_agents/             # Compatibility/domain-facing agent tooling
├── persistence/               # PostgreSQL adapters and migrations
├── integrations/              # External system adapters
├── evaluation/                # Existing datasets/evaluation compatibility layer
├── observability/             # Telemetry
├── deployment/                # Container/Terraform deployment
└── tests/                     # Regression/security/architecture tests
```

## Quality Gate

A build is not complete until the repository quality workflow is green. The gate includes pytest, domain deployment smoke tests, enterprise security controls, migration validation, red-team regression, Ruff, MyPy, Bandit, dependency audit, compileall, Terraform validation, SBOM generation/validation, staging API/load smoke, production Docker runtime smoke, and Semgrep.

See [`docs/build-9-ai-evaluation-plane.md`](../docs/build-9-ai-evaluation-plane.md) and [`docs/adr/0009-ai-evaluation-plane.md`](../docs/adr/0009-ai-evaluation-plane.md).
