# Month 7: Platform Layer — Unified Client Onboarding, Deployment & Delivery

The capstone infrastructure layer that transforms domain-specific agents into a governed enterprise AI platform. This platform provides client onboarding, schema auto-mapping, preference configuration, containerized deployment, unified API gateway, multi-system integrations, observability, billing, identity, multi-tenancy, first-class agent execution, and durable workflows.

---

## Enterprise Architecture Migration — Build 4 COMPLETE

The enterprise-grade architecture migration is active. The platform now has a framework-neutral kernel, canonical identity/multi-tenancy primitives, a first-class agent execution runtime, and a durable workflow boundary for long-running work.

### Build 1 — Architecture Foundation

- Stable agent, domain, execution, model, tool, repository, and event-bus contracts
- Hexagonal/ports-and-adapters dependency direction
- Kernel isolation from FastAPI, database drivers, model-provider SDKs, and infrastructure adapters
- Executable architecture-boundary tests
- No direct production imports of Month 1–6 curriculum modules
- Legacy curriculum explicitly isolated as compatibility/history material
- Packaging configured so `fde_platform` ships with the platform distribution

**Build 1 status: GREEN — complete.**

### Build 2 — Identity & Multi-Tenancy

- Provider-neutral principal model for users, services, and agents
- Canonical tenant/environment primitives
- Immutable request context binding identity to tenant and environment
- Fail-closed tenant, role, and scope authorization
- PostgreSQL tenant/environment/membership schema
- PostgreSQL `FORCE ROW LEVEL SECURITY` with restrictive `USING` and `WITH CHECK` isolation
- Cross-tenant authorization and migration security regression tests

**Build 2 status: GREEN — complete.**

### Build 3 — Agent Runtime

- First-class `AgentRun` execution record
- Explicit lifecycle and terminal-state semantics
- Execution budgets for steps, elapsed time, and serialized output
- Cooperative cancellation
- Versioned checkpoints with SHA-256 state fingerprints
- `RunStore` persistence port with thread-safe in-memory reference adapter
- Compatibility adapter for existing `DomainAgent` implementations
- Runtime regression coverage for success, failure, cancellation, limits, checkpoints, and domain compatibility

**Build 3 status: GREEN — complete.**

### Build 4 — Durable Workflow Engine

- Version-pinned declarative workflow definitions and steps
- Durable `WorkflowRun` projection and explicit lifecycle
- Append-only ordered workflow event history with optimistic sequence protection
- Leased task queue with explicit acknowledgement semantics
- PostgreSQL durable workflow/run/event persistence
- PostgreSQL queue claims using transactional row locking and `SKIP LOCKED`
- Bounded exponential retries and dead-letter handling
- Durable external wait/signal semantics
- Operator cancellation
- Crash recovery/re-enqueue reconciliation
- Stable workflow/step/attempt idempotency keys
- Tenant-scoped `FORCE ROW LEVEL SECURITY` for workflow state, history, and tasks
- Regression tests for success, replay, retries, dead letters, waits/signals, cancellation, leases, and migration security

**Build 4 status: GREEN — complete.**

### Current migration rule

```text
Application / API / Workers
            ↓
     Identity + Context
            ↓
       Agent Runtime
            ↓
    Durable Workflows
            ↓
     Platform contracts
            ↓
       Domain plugins
            ↓
Infrastructure adapters
```

The repository remains a modular monolith during this phase. Future policy, tool, model, and event services will be introduced only when their boundaries are stable enough to justify extraction.

See [`docs/BUILD-4-DURABLE-WORKFLOWS.md`](docs/BUILD-4-DURABLE-WORKFLOWS.md), [`docs/adr/0005-durable-workflow-engine.md`](docs/adr/0005-durable-workflow-engine.md), and [`fde_platform/README.md`](fde_platform/README.md).

---

## Tinlance Gateway Integration

The production Tinlance gateway calls this service through the stable contract:

```text
POST /v1/{domain}/execute
Authorization: Bearer <OIDC access token>
x-request-id: <correlation id>
```

Request body:

```json
{
  "tenant_id": "tinlance",
  "payload": {
    "task": "triage this alert",
    "organization_id": "org_123",
    "metadata": {"source": "tinlance"}
  }
}
```

Supported domains are exactly:

`cybersecurity`, `finance`, `healthtech`, `logistics`, `legal`, `revops`.

### Required production configuration

The Mastery API validates OIDC bearer tokens using these environment variables:

```text
FDE_OIDC_ISSUER=https://<issuer>
FDE_OIDC_AUDIENCE=<mastery-api-audience>
FDE_OIDC_JWKS_URL=<optional-explicit-jwks-url>
FDE_OIDC_ALGORITHMS=RS256
```

The token issued to the Tinlance gateway must contain:

- `iss` matching `FDE_OIDC_ISSUER`
- `aud` containing `FDE_OIDC_AUDIENCE`
- `sub`
- `exp` and `iat`
- `tenant_id: tinlance`
- `scope` containing `agents:execute`

The token issuer/client-credentials endpoint is external to this repository. The Tinlance gateway obtains the token and presents it to this API; this service is responsible for cryptographic JWT validation and authorization.

### Health and readiness

- `GET /health` is a liveness endpoint and is public.
- `GET /ready` returns `503` until OIDC issuer/audience configuration and all six domain routes are present.
- Execution responses preserve `x-request-id` for end-to-end correlation.
- Agent failures are returned as a generic `502 Agent execution failed`; internal exceptions are not exposed over the API.

The contract is covered by API tests and the domain enum/allowlist is intentionally duplicated at the integration boundary so a future domain expansion cannot silently change the Tinlance contract.

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLIENT ONBOARDING                                                          │
│  Schema Mapper → Preferences → Golden Dataset → Deployment Plan             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  IDENTITY & MULTI-TENANCY                                                    │
│  Principal → RequestContext → Tenant/Environment → Authorization → RLS      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  AGENT RUNTIME                                                               │
│  AgentRun → Budget → Cancellation → Checkpoint → Domain Agent → Result      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  DURABLE WORKFLOW ENGINE                                                     │
│  WorkflowRun → Event History → Leased Queue → Retry/Wait → Recovery/Replay  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  DOMAIN PLUGINS                                                              │
│  Cybersecurity │ Finance │ HealthTech │ Logistics │ Legal │ RevOps │ ...    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  INFRASTRUCTURE & OBSERVABILITY                                              │
│  PostgreSQL │ Redis │ Integrations │ OpenTelemetry │ Evaluation │ Releases   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The "Zero-Delay" Client Journey

| Phase | Timeline | Action | Output |
|-------|----------|--------|--------|
| **Discovery** | 30 min | Map pain to pre-built domain agent | SOW with template pricing |
| **Onboarding** | 2 hours | Upload sample data → auto-map → generate golden dataset | 50-case benchmark |
| **Deployment** | 4 hours | Docker container + API endpoint + integrations | Live client endpoint |
| **Value Proof** | Week 2 | Drift detection + confidence tracking + billing | Business review with metrics |

---

## Quick Start

### 1. Onboard a New Client

```bash
cd month-7-platform
python main.py onboard --client-id retailer-corp --client-name "RetailCo Global" --domains cybersecurity,finance --sample-dir ./sample_data/retailer-corp --tier growth
```

### 2. Run Platform Evaluation

```bash
python main.py eval
```

### 3. Run Sales Simulation

```bash
python main.py simulate --scenario all
```

### 4. Start API Gateway (Docker)

```bash
cd deployment/docker
docker-compose up --build
```

---

## Project Structure

```text
month-7-platform/
├── README.md
├── fde_platform/
│   ├── contracts/                         # Stable cross-boundary contracts
│   ├── identity/                          # Principal, tenant and request context
│   ├── authorization/                     # Fail-closed authorization boundary
│   ├── ports/                             # Hexagonal architecture ports
│   ├── runtime/                           # First-class agent execution runtime
│   ├── workflow/                          # Durable workflow engine + queue contracts
│   └── architecture.py                    # Executable boundary policy
├── schemas.py
├── main.py
├── eval_harness.py
├── client_onboarding/
├── deployment/
├── persistence/
│   ├── migrations/                        # Versioned tenant/workflow persistence
│   ├── workflow_store.py                  # PostgreSQL workflow adapter
│   └── workflow_queue.py                  # PostgreSQL leased queue adapter
├── shared_orchestrator/
├── integrations/
├── observability/
├── evaluation/
└── tests/
    ├── test_agent_runtime.py
    ├── test_durable_workflows.py
    └── test_workflow_migration_contract.py
```

---

## Agent Runtime Contract

Every execution is represented by an `AgentRun` rather than being an anonymous function call. Build 4 adds a durable workflow above the runtime for multi-step work:

```text
CREATED
   ↓
RUNNING
   ├───────────────┐
   ↓               ↓
COMPLETED       FAILED / CANCELLED / TIMED_OUT / LIMIT_EXCEEDED
```

Workflow execution adds:

```text
WorkflowRun
   ↓
StepStarted
   ↓
Activity
   ├── success → StepCompleted → next step
   ├── retry   → scheduled retry
   ├── wait    → WAITING → external signal
   └── failure → DEAD_LETTERED
```

The durable boundary is intentionally **at-least-once** for activities. External side-effect adapters must use stable idempotency keys. Worker leases, acknowledgements, event history, and `recover()` provide crash recovery without claiming impossible exactly-once external mutation semantics.

---

## Security and Governance

The platform security baseline is mapped to OWASP ASVS 5.0. AI governance and evaluation are informed by NIST AI RMF and its Generative AI Profile. Identity architecture follows zero-trust principles and treats software/AI agents as explicit execution identities. Observability follows OpenTelemetry semantic-convention guidance, with sensitive AI content excluded by default.

Workflow state, events, and tasks are tenant-scoped and protected by PostgreSQL `FORCE ROW LEVEL SECURITY`. High-impact actions remain human-controlled. Build 5 will introduce the dedicated policy, risk, and approval plane above this durable execution layer.

---

## CI / Release Gates

Every architectural change is expected to pass the repository quality pipeline before it is considered complete:

- pytest
- seven-domain deployment smoke tests
- Custom Agent tests and secure tool-gateway tests
- enterprise security controls
- identity/multi-tenancy and runtime regression tests
- durable workflow and migration security regression tests
- migration validation
- red-team regression
- Ruff
- MyPy
- Bandit
- pip-audit
- compileall
- Terraform format/validation
- SBOM generation/validation
- staging API startup/readiness
- load smoke
- production Docker build/runtime smoke
- Semgrep static security scan
- release image signing, SBOM attestation, and build provenance

A green workflow is a merge gate, not a substitute for customer-specific production validation.

---

## License & Attribution

Part of the **FDE Mastery** curriculum — a production-oriented Forward Deployed Engineering platform for AI systems, AI security, and enterprise automation.

| Build | Capability | Status |
|------:|------------|--------|
| 1 | Architecture Foundation | GREEN |
| 2 | Identity & Multi-Tenancy | GREEN |
| 3 | Agent Runtime | GREEN |
| 4 | Durable Workflow Engine | GREEN |
