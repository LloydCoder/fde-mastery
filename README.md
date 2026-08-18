# FDE Mastery

**Production-oriented Forward Deployed Engineering platform for AI systems, AI security, and enterprise automation.**

FDE Mastery is a reusable enterprise AI platform with seven domain services—Cybersecurity, Finance, HealthTech, Logistics, Legal, RevOps, and Procurement—plus a tenant-scoped Custom Agent framework. A common FastAPI/platform layer provides identity, authorization, policy, resilience, persistence, auditability, evaluation, observability, integrations, and signed releases.

> **Portfolio objective:** demonstrate the engineering judgment required to move AI from a model/API experiment into a governed enterprise workflow.

## What is in the platform

- Seven domain adapters behind one `DomainAgent` contract
- Canonical `domains/` facades while preserving the existing Month 1–6 implementations and API compatibility
- Procurement as a first-class domain with supplier risk, quote comparison, spend thresholds, and human approval boundaries
- Tenant-scoped Custom Agent framework for customer-specific workflows without modifying the core platform
- Central `AgentRouter` with retries, jitter, circuit breaking, concurrency limits, and per-domain isolation
- FastAPI API with typed request/response contracts and request correlation
- API-key authentication plus production-oriented OIDC/JWKS JWT validation
- Tenant and scope/RBAC authorization
- Short-lived service identity and mTLS validation contract
- PostgreSQL persistence, checksum-verified migrations, idempotency, and centralized audit events
- Tamper-evident audit hash-chain utility and sensitive-data redaction
- Policy-as-code and human approval for high-impact actions
- Redis-compatible distributed rate limiting and durable task-queue contract
- OpenTelemetry tracing/metrics with Collector deployment references
- Versioned evaluation, statistical drift detection, shadow-mode recording, and red-team regression tests
- Chaos/resilience tests and load-smoke validation
- Tenant-scoped integration contracts and integration adapters
- Terraform validation, CycloneDX SBOM generation, keyless Cosign signing, and SBOM attestation
- Production deployment, disaster-recovery, rollback, security, and operational documentation

The repository demonstrates **production-oriented engineering controls**. It is not a claim of security certification, regulatory compliance, or a real customer deployment.

---

## Enterprise architecture

```text
                         FDE MASTERY ENTERPRISE PLATFORM
                                      |
                         +------------v-------------+
                         |       FastAPI API         |
                         +------------+-------------+
                                      |
                    +-----------------+------------------+
                    |                 |                  |
             OIDC / service       Tenant/RBAC       Policy + HITL
              identity/JWT        + scopes          + idempotency
                    +-----------------+------------------+
                                      |
                             +--------v--------+
                             |   AgentRouter   |
                             | resilience      |
                             +--------+--------+
                                      |
      +-----------+---------+---------+---------+---------+---------+-------------+
      |           |         |         |         |         |             |
      v           v         v         v         v         v             v
    SOC        Finance    Health   Logistics   Legal     RevOps     Procurement
      |           |         |         |         |         |             |
      +-----------+---------+---------+---------+---------+-------------+
                                      |
                         +------------+-------------+
                         |                          |
                  Custom Agents              Integration Hub
                  tenant-scoped              REST/Webhook/MCP
                         |                          |
                         +------------+-------------+
                                      |
                         Audit + Evaluation + OTel
                                      |
                         PostgreSQL / Redis / Models
                                      |
                    CI + SBOM + Cosign + Provenance
```

The platform uses a compatibility-first migration strategy: the new `domains/` namespace is the client-facing architectural vocabulary, while the original Month 1–6 paths remain intact until all references can be migrated safely. This avoids breaking existing FastAPI connections or integration contracts.

---

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

---

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

---

## Custom Agent framework

Customers should not need a new hard-coded platform domain for every bespoke workflow. The Custom Agent framework provides:

- Tenant-scoped agent registration
- Versioned agent specifications
- Tool allowlists
- Explicit human-approval actions
- Fail-closed high-impact policy boundaries
- A registry isolated by tenant

Target workflow model:

```text
Trigger → Context → Agent → Approved tools → Policy → HITL → Action → Audit
```

This is the foundation for customer-specific FDE implementations while keeping the core platform stable.

---

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

See [`docs/PRODUCTION-READINESS.md`](./docs/PRODUCTION-READINESS.md). Repository tests establish engineering readiness; customer-specific credentials, data, compliance evidence, and operational validation remain deployment responsibilities.

---

## Security and supply chain

The security baseline is aligned with current OWASP Top 10:2025 categories, including broken access control, security misconfiguration, software supply-chain failures, injection, authentication failures, data integrity, logging/alerting, and exceptional-condition handling. citeturn0search3

The AI governance/evaluation approach is informed by NIST AI RMF and its Generative AI Profile, which provide a cross-sector framework for governing, mapping, measuring, and managing AI risks. citeturn0search0turn0search9

The release pipeline includes:

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
SBOM / provenance attestation
  ↓
Registry
  ↓
Deployment verification
```

SLSA provenance is the appropriate next-level supply-chain evidence because it records how an artifact was produced and its build inputs; signed provenance provides stronger tamper resistance than an unsigned artifact alone. citeturn0search2turn0search10

---

## Observability

The platform uses OpenTelemetry with a Collector-oriented deployment model. OpenTelemetry recommends Collector deployment patterns for receiving, processing, and exporting telemetry to one or more backends. citeturn0search1turn0search6

The observability contract covers:

- Request correlation
- Gateway/router/domain spans
- Metrics and latency
- Confidence/evaluation signals
- Rate-limit events
- Audit events
- Drift detection
- Provider failure/recovery signals

Production backends remain configurable per customer environment.

---

## CI / release gates

Every architectural change is expected to pass the repository quality pipeline before it is considered complete:

- pytest
- seven-domain deployment smoke tests
- Custom Agent tests
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
- production Docker build
- Semgrep static security scan
- release image signing and SBOM attestation

A green workflow is a merge gate, not a substitute for customer-specific production validation.

---

## Production reference

See:

- [`DEPLOYMENT.md`](./DEPLOYMENT.md)
- [`docs/PRODUCTION-READINESS.md`](./docs/PRODUCTION-READINESS.md)
- [`docs/ENTERPRISE-HARDENING.md`](./docs/ENTERPRISE-HARDENING.md)
- [`docs/DR-RUNBOOK.md`](./docs/DR-RUNBOOK.md)
- [`docs/API.md`](./docs/API.md)

Minimum production configuration:

```text
FDE_ENVIRONMENT=production
FDE_STORAGE_BACKEND=postgres
FDE_RATE_LIMIT_BACKEND=redis
FDE_DATABASE_URL=<managed-postgresql-tls-url>
FDE_REDIS_URL=<managed-redis-tls-url>
FDE_OIDC_ISSUER=https://<identity-provider>
FDE_OIDC_AUDIENCE=<audience>
FDE_SECRETS_BACKEND=managed
OTEL_ENABLED=true
```

Production defaults fail closed if a managed secrets provider is not injected.

---

## Quick start

```bash
cd month-7-platform
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
export FDE_STORAGE_BACKEND=postgres
export FDE_DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/fde_mastery"
python -m persistence.migrate
```

---

## Evidence

- [`month-1-cybersecurity/AUDIT.md`](./month-1-cybersecurity/AUDIT.md) — SOC operating map
- [`docs/PRODUCTION-READINESS.md`](./docs/PRODUCTION-READINESS.md) — eight-gate promotion model
- [`docs/DEMO.md`](./docs/DEMO.md) — interactive walkthrough
- [`docs/CASE-STUDY.md`](./docs/CASE-STUDY.md) — synthetic customer case-study template
- [`docs/ENTERPRISE-HARDENING.md`](./docs/ENTERPRISE-HARDENING.md) — security/operations contract
- [`month-7-platform/security/ai-threat-model.md`](./month-7-platform/security/ai-threat-model.md) — AI threat model

Customer outcome numbers should only be added after a real deployment and measurement.

---

## Repository structure

```text
fde-mastery/
├── README.md
├── .github/workflows/
├── month-1-cybersecurity/     # compatibility-preserved source
├── month-2-finance/            # compatibility-preserved source
├── month-3-healthtech/         # compatibility-preserved source
├── month-4-logistics/          # compatibility-preserved source
├── month-5-legal/              # compatibility-preserved source
├── month-6-revops/             # compatibility-preserved source
└── month-7-platform/
    ├── domains/                # canonical domain namespace
    │   ├── cybersecurity/
    │   ├── finance/
    │   ├── healthtech/
    │   ├── logistics/
    │   ├── legal/
    │   └── procurement/
    ├── custom_agents/           # tenant-specific agent framework
    ├── shared_orchestrator/
    ├── integrations/
    ├── security/
    ├── persistence/
    ├── observability/
    ├── evaluation/
    ├── deployment/
    └── tests/
```

---

## Responsible use

The domain projects use synthetic/example data and demonstrate engineering patterns. They are not financial advice, medical diagnosis/treatment, legal advice, regulatory certification, or proof of production performance.

High-impact workflows should retain authorized human review and appropriate domain-specific controls.

## About

**FDE Mastery** is built by **LloydCoder** as a hands-on portfolio for Forward Deployed Engineering, AI security, enterprise automation, and production AI systems engineering.

The emphasis is on the surrounding system—not merely an LLM call: **schemas, policy, evaluation, recovery, orchestration, security, governance, persistence, observability, integration, and release evidence.**

## License

See [`LICENSE`](./LICENSE).
