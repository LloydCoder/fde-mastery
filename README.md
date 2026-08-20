# FDE Mastery

**Production-oriented Forward Deployed Engineering platform for AI systems, AI security, and enterprise automation.**

FDE Mastery is a reusable enterprise AI platform with seven domain services—Cybersecurity, Finance, HealthTech, Logistics, Legal, RevOps, and Procurement—plus a tenant-scoped Custom Agent framework. The platform provides identity, authorization, policy, resilience, durable workflows, control-plane registries, model/tool boundaries, persistence, auditability, evaluation, observability, interoperability contracts, FinOps, incident management, deployment isolation, and signed/provenance-backed releases.

> **Portfolio objective:** demonstrate the engineering judgment required to move AI from a model/API experiment into a governed enterprise workflow.

## Enterprise architecture

![FDE Mastery enterprise architecture](./docs/architecture-enterprise.svg)

The repository uses an enterprise monorepo structure. Production code is owned by `packages/platform-core`; historical Months 1–6 curriculum is isolated under `legacy/curriculum`. The platform remains a modular monolith by design: control-plane, data-plane and trust-plane boundaries are explicit so only components that require independent scaling or isolation need to become separate services.

```text
                    CONTROL PLANE
 identity · tenancy · agent/tool/model/policy registries
 evaluations · deployments · configuration · approvals
                              │
                              ▼
API / Gateway → AuthN/AuthZ → Policy → Durable Workflow
                                      │
                                      ▼
                                Agent Runtime
                                  /       \
                                 /         \
                         Model Gateway   Tool Gateway
                              │               │
                         Providers       Enterprise Systems
                                 \           /
                                  ▼         ▼
                              Event / Audit
                                   │
                    Evaluation · FinOps · Incidents
                                   │
                              Observability

                    TRUST PLANE
 identity · least privilege · risk · HITL · sandbox · audit
```

## Repository structure

```text
fde-mastery/
├── apps/                         # deployable application boundaries, including worker
├── packages/
│   └── platform-core/            # canonical production platform distribution
├── domains/                      # first-class domain ownership surface
├── infrastructure/               # repository-level infrastructure ownership
├── platformctl/                  # dependency-free platform inspection CLI
├── tests/                        # repository-level architecture/contract tests
├── legacy/
│   └── curriculum/               # historical Months 1–6, isolated from production
├── docs/                         # architecture, ADRs, operations and evidence
└── .github/workflows/             # CI/CD and release attestations
```

## Platform capabilities

### P0 — production control and isolation

- Versioned Agent, Tool, Model and Policy registries with explicit promotion states
- Durable workflow and leased worker boundary so API processes can enqueue work without owning execution
- Independent trust-plane security gateway; model output is never an authorization decision
- Risk tiers and explicit approval requirements for high-impact actions
- Quorum/expiry human approvals
- Tenant-aware identity context and PostgreSQL RLS foundations
- Sandbox policy contract for custom/untrusted workloads

### P1 — interoperability and operational evidence

- Authorization-aware MCP and A2A protocol contracts
- Transactional outbox/inbox event architecture
- AI decision lineage containing evidence references rather than hidden chain-of-thought
- Tenant-aware AI FinOps for token, tool and compute economics
- AI incident lifecycle with containment, investigation, remediation and closure
- Architecture/contract tests for the new trust and control boundaries

### P2 — platform productization

- Shared, isolated and dedicated deployment profiles
- Dependency-free `platformctl manifest` and `platformctl doctor` commands
- Machine-readable platform capability manifest
- Explicit service extraction boundaries without premature microservice proliferation

These capabilities are implemented as platform contracts and reference adapters. They do not by themselves constitute a security certification, regulatory approval, or proof of a live customer deployment.

## Domain portfolio

| Domain | Primary service | Example workflow |
|---|---|---|
| Cybersecurity | SOC Triage | SIEM alert enrichment and prioritization |
| Finance | Transaction Risk | Transaction risk and governance |
| HealthTech | Compliance & Triage | PHI-safe workflow support |
| Logistics | Supply Chain Risk | Shipment and telemetry analysis |
| Legal | Contract Risk | Clause and contract risk analysis |
| RevOps | Revenue Operations | Pipeline and account operations |
| Procurement | Procurement Intelligence | Supplier risk, quote comparison, spend approval routing |
| Custom | Customer-specific agents | Tenant-defined workflows and policies |

High-impact actions remain human-controlled. Examples include account disablement, endpoint isolation, clinical intervention, payment/purchase approval, supplier award, contract rejection, and customer notification.

## Procurement domain

Procurement is a first-class deployment domain rather than a demo-only module.

Current v1 capabilities:

- Supplier risk scoring
- Quote comparison signals
- Spend/approval thresholds
- Procurement prioritization
- Human approval routing
- Deterministic fallback behavior

The first workflow is intentionally recommendation-only:

```text
Supplier / RFQ
      ↓
Normalize + validate
      ↓
Supplier risk + quote signals
      ↓
Spend threshold / policy
      ↓
Recommendation
      ↓
Human procurement approval
```

The platform does **not** autonomously award suppliers, create purchase orders, modify vendor master data, or approve spend.

## Custom Agent framework

Customers should not need a new hard-coded platform domain for every bespoke workflow. The Custom Agent framework provides tenant-scoped agent registration, versioned specifications, explicit tool allowlists, secure tool execution, fail-closed high-impact policy boundaries, and tenant-isolated registries.

Target workflow model:

```text
Trigger → Context → Agent → Approved tools → Policy → HITL → Action → Audit
```

## Enterprise deployment gate

A domain is promoted to customer production only after evidence for all eight gates:

1. Golden dataset expansion
2. Approved external-tool integration
3. Enterprise ingestion
4. Evaluation thresholds
5. Staging deployment
6. Shadow mode
7. Human-in-the-loop production
8. Controlled, reversible actions

See [`docs/PRODUCTION-READINESS.md`](./docs/PRODUCTION-READINESS.md).

## Security, AI governance and supply chain

The security baseline is mapped to OWASP ASVS 5.x and OWASP's 2026 Agentic Applications guidance. AI governance and evaluation are informed by NIST AI RMF and its Generative AI Profile. Observability follows OpenTelemetry guidance. Release artifacts use signed images, SBOM attestations, and SLSA-oriented build provenance.

```text
Source
  ↓
Quality + security gates
  ↓
Docker image
  ↓
CycloneDX SBOM
  ↓
Keyless Cosign signature
  ↓
SBOM + provenance attestation
  ↓
Registry
  ↓
Deployment verification
```

## Observability and decision evidence

The platform uses OpenTelemetry with a Collector-oriented deployment model. Operational telemetry is designed around request, workflow, agent, model, tool, policy and evaluation boundaries. Sensitive prompts and raw customer content should not be emitted into ordinary telemetry. Decision lineage stores references to inputs, retrieval, policies, tools, model/version, approval and outputs without exposing hidden chain-of-thought.

## CI / release gates

Every architectural change is expected to pass the repository quality pipeline before it is considered complete:

- pytest and P0/P1/P2 platform-control tests
- seven-domain deployment smoke tests
- Custom Agent and secure tool-gateway tests
- enterprise security controls
- migration validation
- red-team regression
- Ruff
- MyPy
- Bandit
- pip-audit
- compileall, including platform CLI and worker boundary
- platform CLI doctor/manifest checks
- Terraform format/validation
- SBOM generation/validation
- staging API startup/readiness
- load smoke
- production Docker build/runtime smoke
- Semgrep static security scan
- release image signing, SBOM attestation, and build provenance

A green workflow is a merge gate, not a substitute for customer-specific production validation.

## Quick start

```bash
cd packages/platform-core
python -m pip install -e ".[test,quality,security,observability,sbom]"
export FDE_STORAGE_BACKEND=memory
export FDE_RATE_LIMIT_BACKEND=memory
export FDE_MONTH1_PROVIDER=mock
export MOCK_LLM=true
export FDE_ENVIRONMENT=test
python -m pytest -q
```

Platform inspection:

```bash
PYTHONPATH=packages/platform-core python -m platformctl manifest
PYTHONPATH=packages/platform-core python -m platformctl doctor
```

For PostgreSQL:

```bash
cd packages/platform-core
export FDE_STORAGE_BACKEND=postgres
export FDE_DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/fde_mastery"
python -m persistence.migrate
```

## Evidence

- [`docs/PRODUCTION-READINESS.md`](./docs/PRODUCTION-READINESS.md) — promotion model
- [`docs/BUILD-STATUS.md`](./docs/BUILD-STATUS.md) — enterprise build ledger
- [`docs/adr/0013-enterprise-repository-structure.md`](./docs/adr/0013-enterprise-repository-structure.md) — repository structure decision
- [`legacy/curriculum/`](./legacy/curriculum/) — historical learning material
- [`packages/platform-core/security/ai-threat-model.md`](./packages/platform-core/security/ai-threat-model.md) — AI threat model

Customer outcome numbers should only be added after a real deployment and measurement.

## Responsible use

The domain projects use synthetic/example data and demonstrate engineering patterns. They are not financial advice, medical diagnosis/treatment, legal advice, regulatory certification, or proof of production performance.

High-impact workflows should retain authorized human review and appropriate domain-specific controls.

## About

**FDE Mastery** is built by **LloydCoder** as a hands-on portfolio for Forward Deployed Engineering, AI security, enterprise automation, and production AI systems engineering.
