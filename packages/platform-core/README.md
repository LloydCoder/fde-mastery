# Month 7: Platform Layer — Enterprise FDE Platform

The capstone layer turns the domain agents into a governed enterprise AI platform. Each build establishes a stable boundary, proves it with CI, and becomes the foundation for the next build.

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
| 11 | Enterprise Deployment & DR | GREEN |
| 12 | Platform Productization | GREEN |
| 13 | Domain Intelligence Foundation | GREEN |
| 14 | FDE Engagement & Workflow Engine | IN PROGRESS |

## Build 14 — FDE Engagement & Workflow Engine

Build 14 adds the customer-facing delivery lifecycle contract above the existing durable workflow engine.

- Tenant-scoped FDE engagements
- Explicit customer objectives and workflow identity
- Baseline and target value metrics
- Acceptance criteria and evidence references
- Fail-closed lifecycle transitions
- Discovery → mapping → value case → architecture → build → evaluation → pilot → shadow → production → operate → transfer → retired
- Human approval gates for high-impact promotion stages
- Production deployment evidence requirement
- Deterministic promotion readiness reports
- Compilation into the existing `WorkflowDefinition` contract

The lifecycle layer does **not** execute tools, models or external side effects. Existing identity, policy, approval, tool, model, evaluation, audit and durable workflow boundaries remain authoritative.

## Architecture

```text
Application / API / Workers
            ↓
Identity + RequestContext
            ↓
FDE Engagement Lifecycle
  objective · metrics · evidence
            ↓
     Promotion Gates
            ↓
   Durable Workflow Definition
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
```

The repository remains a modular monolith while these boundaries stabilize. Extraction into separate services is deferred until contracts, operational requirements and failure domains justify it.

## Quality Gate

A build is not complete until the repository quality workflow is green. The gate includes pytest, domain deployment smoke tests, enterprise security controls, migration validation, red-team regression, Ruff, MyPy, Bandit, dependency audit, compileall, Terraform validation, SBOM generation/validation, staging API/load smoke, production Docker runtime smoke, and Semgrep.

See [`docs/build-14-fde-engagement-workflow.md`](../../docs/build-14-fde-engagement-workflow.md) and [`docs/adr/0015-fde-engagement-workflow-engine.md`](../../docs/adr/0015-fde-engagement-workflow-engine.md).
