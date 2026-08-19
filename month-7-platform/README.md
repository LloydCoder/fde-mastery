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
| 7 | Model Gateway | IN PROGRESS |
| 8 | Event-Driven Platform | PLANNED |
| 9 | AI Evaluation Plane | PLANNED |
| 10 | Observability & AI FinOps | PLANNED |
| 11 | Enterprise Deployment & DR | PLANNED |
| 12 | Platform Productization | PLANNED |

### Build 1 — Architecture Foundation

- Framework-neutral kernel and stable contracts/ports
- Hexagonal/ports-and-adapters dependency direction
- Legacy curriculum isolation
- Executable architecture-boundary tests

**Status: GREEN — complete.**

### Build 2 — Identity & Multi-Tenancy

- Provider-neutral principals for users, services and agents
- Canonical tenant/environment model
- Immutable `RequestContext`
- Fail-closed authorization and PostgreSQL `FORCE ROW LEVEL SECURITY`
- Cross-tenant regression coverage

**Status: GREEN — complete.**

### Build 3 — Agent Runtime

- First-class `AgentRun`
- Explicit lifecycle and terminal states
- Step/time/output budgets
- Cooperative cancellation
- Versioned checkpoints with integrity fingerprints
- `RunStore` port and deterministic reference adapter

**Status: GREEN — complete.**

### Build 4 — Durable Workflow Engine

- Version-pinned workflow definitions
- Durable workflow state and append-only event history
- Leased task queue using transactional locking / `SKIP LOCKED`
- Bounded retries, dead letters, waits/signals and crash recovery
- Stable workflow/step/attempt idempotency keys
- Tenant-scoped RLS

**Status: GREEN — complete.**

### Build 5 — Trust & Policy Plane

- Fail-closed policy decision point
- Versioned policy rules and risk tiers
- Human approval boundary
- Tamper-evident authorization audit events
- Least-privilege and cross-tenant authorization regression coverage

**Status: GREEN — complete.**

### Build 6 — Tool Gateway

- Immutable, versioned `ToolDefinition`
- Explicit capabilities: `read`, `write`, `delete`, `external_network`, `sensitive_data`
- Explicit registration and fail-closed lookup
- Tenant + request-context binding
- Approval boundary for high-impact tools
- Idempotency keyed by tenant/tool/idempotency key
- Explicit `ToolResult` envelope
- Framework-neutral `ToolGateway` boundary
- Deterministic reference implementation
- Security regression coverage

**Status: GREEN — complete.**

### Build 7 — Model Gateway

Build 7 establishes the mandatory platform boundary for model invocation and routing.

- Immutable, versioned `ModelDefinition`
- Explicit model capabilities and data-class allowlists
- Provider-neutral `ModelProvider` adapter boundary
- Central `ModelRegistry` with explicit model/version registration
- Deterministic named routing with ordered fallback candidates
- Fail-closed unknown-model behavior
- Policy decision hook before provider invocation
- Retry-aware fallback: only retryable provider failures may move to another candidate
- Request-level output-token and model capability enforcement
- Explicit `ModelResponse` error envelope
- Framework-neutral provider adapters; provider SDKs remain outside the kernel
- Regression coverage for authorization, data classification, capability, routing, fallback and policy enforcement

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
```

The repository remains a modular monolith while these boundaries stabilize. Extraction into separate services is deferred until contracts, operational requirements and failure domains justify it.

## Model Gateway Security Rules

1. Models must be explicitly registered and versioned.
2. Provider SDKs must remain behind provider adapters; agents cannot call providers directly.
3. A request cannot grant itself capabilities absent from the registered model definition.
4. Data classification is checked before a provider is invoked.
5. The policy boundary is evaluated before provider execution.
6. Routing aliases contain only registered model versions.
7. Fallback is allowed only for explicitly retryable failures; policy, authorization and invalid-request failures must not fail over.
8. Output-token limits are enforced by the gateway and model definition.
9. Model output must be treated as untrusted data and validated before downstream tool or workflow execution.
10. Production deployments should maintain a controlled model inventory, provenance, provider allowlist and telemetry for model usage and failures.

## Model Supply-Chain Boundary

Models and provider integrations are treated as production dependencies rather than implicit trust anchors. Production adapters should record model/provider identity, version and provenance and enforce the approved model inventory. This supports centralized model governance and reduces model-supply-chain risk.

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
│   └── models/                # Model gateway and provider boundary
├── custom_agents/             # Compatibility/domain-facing agent tooling
├── persistence/               # PostgreSQL adapters and migrations
├── integrations/              # External system adapters
├── evaluation/                # Evaluation and golden datasets
├── observability/             # Telemetry
├── deployment/                # Container/Terraform deployment
└── tests/                     # Regression/security/architecture tests
```

## Quality Gate

A build is not complete until the repository quality workflow is green. The gate includes pytest, domain deployment smoke tests, enterprise security controls, migration validation, red-team regression, Ruff, MyPy, Bandit, dependency audit, compileall, Terraform validation, SBOM generation/validation, staging API/load smoke, production Docker runtime smoke, and Semgrep.

See [`docs/build-7-model-gateway.md`](docs/build-7-model-gateway.md) and [`docs/ADR-0007-model-gateway.md`](docs/ADR-0007-model-gateway.md).
