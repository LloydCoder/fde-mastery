# FDE Mastery

**Production-oriented Forward Deployed Engineering portfolio for AI systems, AI security, and enterprise automation.**

FDE Mastery contains six domain systems (Cybersecurity, Finance, HealthTech, Logistics, Legal, and RevOps) integrated by a Month 7 platform capstone. The capstone demonstrates typed agent contracts, orchestration, tenant/domain authorization, OIDC/JWT identity, PostgreSQL persistence, centralized audit events, Redis-compatible rate limiting, resilience controls, OpenTelemetry observability, AI security regression tests, and signed/SBOM-attested container releases.

> **Portfolio objective:** demonstrate the engineering judgment required to move AI from a model/API experiment into a governed business workflow.

## Current platform capabilities

- Six real Month 1–6 domain adapters behind one `DomainAgent` contract
- Central `AgentRouter` with per-domain resilience and circuit breaking
- FastAPI application and structured domain results
- API-key authentication plus production-oriented OIDC discovery/JWKS validation
- JWT issuer, audience, expiry, signature, and required-claim validation
- Tenant and scope/RBAC authorization
- Request-size and rate-limit controls; Redis backend for horizontal deployments
- PostgreSQL persistence boundary
- Append-only centralized audit-event store
- Checksum-verified, versioned transactional migration runner
- Request correlation and OpenTelemetry tracing/metrics integration
- Golden-dataset and integration-test architecture
- Executable prompt-injection/red-team regression cases
- Ruff, MyPy, Bandit, pip-audit, pytest, compilation, and Docker CI gates
- CycloneDX SBOM generation
- Keyless Cosign container signing and SBOM attestation in the release workflow
- Managed PostgreSQL/Redis production deployment reference
- Interactive demo walkthrough and customer-style case-study template

The repository demonstrates **production-oriented engineering controls**. It is not a claim of security certification, regulatory compliance, or a real customer deployment.

---

## Architecture

```text
                         FDE MASTERY PLATFORM
                                  |
                         +--------v--------+
                         |   FastAPI API   |
                         +--------+--------+
                                  |
                +-----------------+-----------------+
                |                 |                 |
          OIDC / API keys       RBAC          Request controls
                |          tenant + scopes     size + rate limit
                +-----------------+-----------------+
                                  |
                         +--------v--------+
                         |   AgentRouter   |
                         | resilience      |
                         +--------+--------+
                                  |
       +------------+-------------+-------------+------------+------------+
       |            |             |             |            |            |
       v            v             v             v            v            v
   Security      Finance      HealthTech    Logistics      Legal        RevOps
   Month 1      Month 2        Month 3       Month 4      Month 5      Month 6
       |            |             |             |            |            |
       +------------+-------------+-------------+------------+------------+
                                  |
                +-----------------+------------------+
                |                                    |
          PostgreSQL                            Observability
        state + audit events                  traces + metrics
                |                                    |
                +-----------------+------------------+
                                  v
                         CI / security / release
                  tests + SBOM + signed image + attestations
```

## Month 7 platform

Location: `month-7-platform/`

### Identity and authorization

OIDC authentication supports issuer discovery, JWKS key rotation/caching, signature verification, required JWT claims, issuer/audience checks, tenant extraction, and scopes. API-key authentication remains useful for controlled service/demo environments.

Production configuration uses:

```text
FDE_OIDC_ISSUER=https://<identity-provider>
FDE_OIDC_AUDIENCE=<audience>
FDE_OIDC_JWKS_URL=<optional-explicit-jwks-url>
```

Never commit tokens, signing keys, API keys, or provider secrets.

### Persistence and audit

Production deployments use PostgreSQL. The platform includes a centralized audit-event schema and repository with request ID, tenant/client, domain, action, outcome, status, duration, timestamp, and metadata.

### Migrations

The canonical runner is `persistence/migrations/runner.py`. It provides:

- numeric migration versions
- durable version tracking
- SHA-256 checksums
- duplicate-version detection
- checksum drift detection
- transactional application
- migration status inspection

Run:

```bash
python -m persistence.migrate
```

### Observability

OpenTelemetry support lives under `month-7-platform/observability/` and supports API instrumentation plus OTLP export when enabled. Production deployments should send telemetry to an OpenTelemetry Collector and then to the organization's managed tracing/metrics backend.

```text
OTEL_ENABLED=true
OTEL_SERVICE_NAME=fde-mastery-platform
OTEL_EXPORTER_OTLP_ENDPOINT=https://<collector>
```

### AI security

`security/redteam_cases.json` and `security/redteam.py` provide deterministic regression coverage for prompt injection, instruction override, secret extraction, tenant-boundary abuse, tool manipulation, malformed output, and resource-abuse scenarios.

---

## Six-domain FDE portfolio

| Domain | System | Core problem |
|---|---|---|
| 01 — Cybersecurity | SOC Triage Agent | SIEM alert analysis and triage |
| 02 — Finance | Transaction Risk & Governance Engine | Transaction risk and mitigation |
| 03 — HealthTech | HealthTech Compliance & Triage Engine | PHI handling and clinical triage |
| 04 — Logistics | Supply Chain Risk Engine | Shipment and telemetry risk |
| 05 — Legal | Contract Risk Analysis Engine | Contract clause risk |
| 06 — RevOps | Enterprise Automation Engine | Pipeline and account operations |

Each domain remains independently testable while Month 7 provides the common integration layer.

---

## Security and release pipeline

The repository separates quality validation from release attestation:

```text
Pull request / main push
        |
        v
Platform Quality
  pytest
  six-domain smoke test
  compileall
  security/dependency checks
  Docker build
        |
        v
main success
        |
        v
Release Attestation
  immutable GHCR image
  keyless Cosign signature
  CycloneDX SBOM
  SBOM attestation
```

The release workflow signs the immutable commit-tagged image rather than a mutable `latest` tag.

---

## Production reference

See [`month-7-platform/docs/PRODUCTION.md`](month-7-platform/docs/PRODUCTION.md) for the managed PostgreSQL/Redis topology, deployment order, rollback model, telemetry requirements, and operational controls.

Minimum production configuration:

```text
FDE_ENVIRONMENT=production
FDE_STORAGE_BACKEND=postgres
FDE_RATE_LIMIT_BACKEND=redis
FDE_DATABASE_URL=<managed-postgresql-tls-url>
FDE_REDIS_URL=<managed-redis-tls-url>
FDE_OIDC_ISSUER=https://<identity-provider>
FDE_OIDC_AUDIENCE=<audience>
OTEL_ENABLED=true
```

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

For production, use a secret manager and managed PostgreSQL/Redis rather than local development credentials.

---

## Evidence and demonstrations

- [`docs/DEMO.md`](month-7-platform/docs/DEMO.md) — five-minute interactive walkthrough
- [`docs/CASE-STUDY.md`](month-7-platform/docs/CASE-STUDY.md) — synthetic customer-style case study template
- [`docs/PRODUCTION.md`](month-7-platform/docs/PRODUCTION.md) — production deployment reference
- [`security/ai-threat-model.md`](month-7-platform/security/ai-threat-model.md) — AI threat model

Customer outcome numbers must only be added after a real deployment and measurement.

---

## Repository structure

```text
fde-mastery/
├── README.md
├── .github/workflows/
│   ├── platform-tests.yml
│   └── release-attestation.yml
├── month-1-cybersecurity/
├── month-2-finance/
├── month-3-healthtech/
├── month-4-logistics/
├── month-5-legal/
├── month-6-revops/
└── month-7-platform/
    ├── schemas.py
    ├── pyproject.toml
    ├── security/
    ├── persistence/
    ├── observability/
    ├── shared_orchestrator/
    ├── deployment/
    ├── scripts/
    ├── docs/
    └── tests/
```

---

## Roadmap status

### Implemented

- [x] Common `DomainAgent` contract
- [x] Six real domain adapters
- [x] Central router and resilience layer
- [x] End-to-end adapter execution tests
- [x] API-key authentication
- [x] OIDC issuer discovery + JWKS JWT validation
- [x] Tenant/scope/RBAC authorization
- [x] PostgreSQL persistence boundary
- [x] Centralized audit-event schema and PostgreSQL store
- [x] Checksum-verified migration runner
- [x] Redis-compatible distributed rate limiting
- [x] OpenTelemetry tracing/metrics integration
- [x] Executable AI red-team regression suite
- [x] CycloneDX SBOM generation
- [x] Keyless Cosign image signing and SBOM attestation workflow
- [x] Managed PostgreSQL/Redis production reference
- [x] Interactive demo walkthrough
- [x] Customer-style case-study template
- [x] CI quality/security/release gates

### Evidence still requiring a real deployment

These are intentionally **not** marked as production claims:

- [ ] Real customer deployment and measured outcomes
- [ ] External penetration test / independent security assessment
- [ ] Production telemetry backend with real workload data
- [ ] Customer-specific case study with verified metrics

---

## Responsible use

The domain projects use synthetic/example data and demonstrate engineering patterns. They are not financial advice, medical diagnosis/treatment, legal advice, regulatory certification, or proof of production performance.

High-impact workflows should retain authorized human review and appropriate domain-specific controls.

## About

**FDE Mastery** is built by **LloydCoder** as a hands-on portfolio for Forward Deployed Engineering, AI security, enterprise automation, and production AI systems engineering.

The emphasis is on the surrounding system—not merely an LLM call: **schemas, policy, evaluation, recovery, orchestration, security, governance, persistence, observability, and release evidence.**

## License

See [`LICENSE`](./LICENSE).
