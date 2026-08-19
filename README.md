# FDE Mastery

**Production-oriented Forward Deployed Engineering platform for AI systems, AI security, and enterprise automation.**

FDE Mastery is a reusable enterprise AI platform with seven domain services—Cybersecurity, Finance, HealthTech, Logistics, Legal, RevOps, and Procurement—plus a tenant-scoped Custom Agent framework. The platform provides identity, authorization, policy, resilience, persistence, auditability, evaluation, observability, integrations, and signed/provenance-backed releases.

> **Portfolio objective:** demonstrate the engineering judgment required to move AI from a model/API experiment into a governed enterprise workflow.

## Enterprise architecture

![FDE Mastery enterprise architecture](./docs/architecture-enterprise.svg)

The repository uses an enterprise monorepo structure. Production code is owned by `packages/platform-core`; historical Months 1–6 curriculum is isolated under `legacy/curriculum`. The platform package remains internally cohesive so packaging, imports, deployment and CI can migrate without a risky all-at-once extraction.

## Repository structure

```text
fde-mastery/
├── apps/                         # deployable application ownership
├── packages/
│   └── platform-core/           # canonical production platform distribution
├── domains/                     # future first-class domain package ownership
├── infrastructure/              # repository-level infrastructure ownership
├── tests/                       # repository-level architecture/contract tests
├── legacy/
│   └── curriculum/              # historical Months 1–6, isolated from production
├── docs/                         # architecture, ADRs, operations and evidence
└── .github/workflows/            # CI/CD and release attestations
```

`packages/platform-core` currently contains the cohesive runtime package, including its domain adapters, security, persistence, evaluation, observability and deployment surfaces. Future extractions must be contract-driven and green in CI.

## Enterprise verification status

Build 12 is considered complete only when the final canonical repository structure passes the complete Platform Quality workflow on the exact merge candidate. A prior workflow run failed during the structural migration because a legacy curriculum loader still referenced the pre-migration path; that defect was corrected before final verification. No failed or superseded workflow is counted as evidence of completion.

The repository's enterprise claims are evidence-based engineering claims, not claims of security certification, regulatory compliance, or a real customer deployment.

## What is in the platform

- Seven domain adapters behind one `DomainAgent` contract
- Procurement as a first-class domain with supplier risk, quote comparison, spend thresholds, and human approval boundaries
- Tenant-scoped Custom Agent framework for customer-specific workflows without modifying the core platform
- Explicit Custom Agent tool gateway with tenant allowlists and fail-closed approval checks
- Central `AgentRouter` with retries, jitter, circuit breaking, concurrency limits, and per-domain isolation
- FastAPI API with typed request/response contracts and request correlation
- Tenant and scope/RBAC authorization
- PostgreSQL persistence, checksum-verified migrations, idempotency, and centralized audit events
- Tamper-evident audit hash-chain utility and sensitive-data redaction
- Policy-as-code and human approval for high-impact actions
- Redis-compatible distributed rate limiting and durable task-queue contract
- OpenTelemetry tracing/metrics with Collector deployment references and semantic-convention guidance
- Versioned evaluation, statistical drift detection, shadow-mode recording, and red-team regression tests
- Chaos/resilience tests and load-smoke validation
- Tenant-scoped integration contracts and integration adapters
- Terraform validation, CycloneDX SBOM generation, keyless Cosign signing, SBOM attestation, and SLSA-oriented build provenance
- Production deployment, disaster-recovery, rollback, security, and operational documentation

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

The security baseline is mapped to OWASP ASVS 5.0.0. AI governance and evaluation are informed by NIST AI RMF and its Generative AI Profile. Observability follows OpenTelemetry semantic conventions. Release artifacts use signed images, SBOM attestations, and SLSA-oriented build provenance.

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

## Observability

The platform uses OpenTelemetry with a Collector-oriented deployment model. The observability contract covers request correlation, gateway/router/domain spans, metrics and latency, confidence/evaluation signals, rate-limit events, audit events, drift detection, and provider failure/recovery signals.

Sensitive payloads are not required for correlation and should remain out of telemetry. GenAI semantic conventions are treated as a compatibility boundary so telemetry schemas can evolve without coupling core authorization or business logic to unstable attributes.

## CI / release gates

Every architectural change is expected to pass the repository quality pipeline before it is considered complete:

- pytest
- seven-domain deployment smoke tests
- Custom Agent tests and secure tool-gateway tests
- enterprise security controls
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

## License

See [`LICENSE`](./LICENSE).
