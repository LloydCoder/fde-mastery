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
| 6 | Tool Gateway | IN PROGRESS |
| 7 | Model Gateway | NEXT |
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

Build 6 establishes the mandatory platform boundary for agent-to-tool execution.

- Immutable, versioned `ToolDefinition`
- Explicit capabilities: `read`, `write`, `delete`, `external_network`, `sensitive_data`
- Explicit tool registration and fail-closed lookup
- Tenant + request-context binding
- Approval boundary for high-impact tools
- Idempotency keyed by tenant/tool/idempotency key
- Explicit `ToolResult` envelope
- Framework-neutral `ToolGateway` port
- Deterministic in-memory reference implementation
- Security regression coverage for unknown tools, excessive capabilities, cross-tenant execution, approval bypass, and duplicate delivery
- ADR-0006 and Build 6 implementation guide

**Status: IN PROGRESS — implementation complete; awaiting full CI verification.**

## Architecture

```text
Application / API / Workers
            ↓
Identity + RequestContext
            ↓
Trust & Policy Plane
            ↓
Agent Runtime
            ↓
Durable Workflow Engine
            ↓
Tool Gateway
     ↙      ↓       ↘
 SaaS     DB/RPC    MCP adapters
            ↓
Domain Agents / Infrastructure
```

The repository remains a modular monolith while these boundaries stabilize. Extraction into separate services is deferred until contracts, operational requirements and failure domains justify it.

## Tool Gateway Security Rules

1. Tools must be explicitly registered.
2. Tool definitions are immutable and versioned.
3. A caller cannot grant itself capabilities that the registered tool does not have.
4. Every invocation is bound to the authenticated tenant and request context.
5. High-impact tools can require human approval.
6. Repeated delivery with the same idempotency key is safe in the reference gateway.
7. Unknown tools and policy violations fail closed.
8. Downstream systems must enforce their own authorization; the gateway is not a substitute for complete mediation downstream.
9. Open-ended primitives such as arbitrary shell execution or unrestricted URL fetching should not be exposed when a narrower capability can satisfy the task.
10. MCP is an integration protocol, not an authorization bypass.

## MCP Integration Boundary

When MCP adapters are introduced, they must preserve the platform principal, tenant, environment, policy decision, capability and audit context. HTTP-based MCP deployments must also implement the applicable OAuth authorization requirements, validate token audience/resource binding, use short-lived credentials, and avoid token passthrough.

## Project Structure

```text
month-7-platform/
├── fde_platform/
│   ├── contracts/             # Stable cross-boundary contracts
│   ├── identity/              # Principal, tenant, request context
│   ├── authorization/         # Trust & policy boundary
│   ├── runtime/               # Agent execution runtime
│   ├── workflow/              # Durable workflows and queues
│   └── tools/                 # Build 6 tool gateway contracts/adapters
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

See [`docs/BUILD-6-TOOL-GATEWAY.md`](docs/build-6-tool-gateway.md) and [`docs/ADR-0006-tool-gateway.md`](docs/ADR-0006-tool-gateway.md).
