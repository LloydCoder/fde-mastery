# Month 7: Platform Layer — Unified Client Onboarding, Deployment & Delivery

The capstone infrastructure layer that transforms domain-specific agents into a governed enterprise AI platform. This platform provides client onboarding, schema auto-mapping, preference configuration, containerized deployment, unified API gateway, multi-system integrations, observability, billing, identity, multi-tenancy, and first-class agent execution.

---

## Enterprise Architecture Migration — Build 3 COMPLETE

The enterprise-grade architecture migration is active. The platform now has a framework-neutral kernel, canonical identity/multi-tenancy primitives, and a first-class agent execution runtime.

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

### Current migration rule

```text
Application / API / Workers
            ↓
     Identity + Context
            ↓
       Agent Runtime
            ↓
     Platform contracts
            ↓
       Domain plugins
            ↓
Infrastructure adapters
```

The repository remains a modular monolith during this phase. Future workflow, policy, tool, model, and event services will be introduced only when their boundaries are stable enough to justify extraction.

See [`docs/BUILD-3-AGENT-RUNTIME.md`](docs/BUILD-3-AGENT-RUNTIME.md), [`docs/adr/0004-agent-runtime.md`](docs/adr/0004-agent-runtime.md), and [`fde_platform/README.md`](fde_platform/README.md).

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

```
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
│   └── architecture.py                    # Executable boundary policy
├── schemas.py
├── main.py
├── eval_harness.py
├── client_onboarding/
├── deployment/
├── shared_orchestrator/
├── integrations/
├── observability/
├── evaluation/
└── tests/
    └── test_agent_runtime.py              # Build 3 runtime invariants
```

---

## Agent Runtime Contract

Every execution is represented by an `AgentRun` rather than being an anonymous function call:

```text
CREATED
   ↓
RUNNING
   ├───────────────┐
   ↓               ↓
COMPLETED       FAILED / CANCELLED / TIMED_OUT / LIMIT_EXCEEDED
```

Runtime safety controls include:

- bounded step count
- bounded elapsed time
- bounded serialized output
- cooperative cancellation
- monotonically sequenced checkpoints
- SHA-256 checkpoint fingerprints
- bounded error metadata
- tenant/request/agent execution context

The runtime is intentionally synchronous in Build 3. Durable workers, distributed cancellation, workflow recovery, queues, replay, and dead-letter handling are Build 4 concerns.

---

## Security and Governance

The platform security baseline is mapped to OWASP ASVS 5.0. AI governance and evaluation are informed by NIST AI RMF and its Generative AI Profile. Identity architecture follows zero-trust principles and treats software/AI agents as explicit execution identities. Observability follows OpenTelemetry semantic-convention guidance, with sensitive AI content excluded by default.

High-impact actions remain human-controlled. Examples include account disablement, endpoint isolation, clinical intervention, payment/purchase approval, supplier award, contract rejection, and customer notification.

---

## CI / Release Gates

Every architectural change is expected to pass the repository quality pipeline before it is considered complete:

- pytest
- seven-domain deployment smoke tests
- Custom Agent tests and secure tool-gateway tests
- enterprise security controls
- identity/multi-tenancy and runtime regression tests
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
| 4 | Durable Workflow Engine | NEXT |
