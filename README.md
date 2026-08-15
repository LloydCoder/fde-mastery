# FDE Mastery

**Production-oriented Forward Deployed Engineering portfolio for AI systems, AI security, and enterprise automation.**

FDE Mastery contains six domain systems—Cybersecurity, Finance, HealthTech, Logistics, Legal, and RevOps—integrated by a Month 7 platform capstone. The platform demonstrates typed agent contracts, orchestration, tenant/domain authorization, OIDC/JWT identity, PostgreSQL persistence, centralized audit events, Redis-compatible rate limiting, resilience controls, OpenTelemetry integration, AI security regression tests, enterprise mutation safety, and signed/SBOM-attested container releases.

> **Portfolio objective:** demonstrate the engineering judgment required to move AI from a model/API experiment into a governed business workflow.

## Current platform capabilities

- Six real Month 1–6 domain adapters behind one `DomainAgent` contract
- Central `AgentRouter` with per-domain resilience, retries, jitter, circuit breaking, and concurrency limits
- FastAPI API with typed domain results and request correlation
- API-key authentication plus production-oriented OIDC discovery/JWKS validation
- JWT issuer, audience, expiry, signature, and required-claim validation
- Tenant and scope/RBAC authorization
- Short-lived service-to-service signed tokens and mTLS identity validation contract
- Request-size and distributed rate-limit controls
- PostgreSQL persistence boundary and formal checksum-verified migrations
- Centralized audit events with tamper-evident hash-chain utility
- Mutation idempotency contract with production PostgreSQL schema
- Sensitive-data redaction at the audit/output boundary
- Policy-as-code gate for high-impact actions and human-approval escalation
- OpenTelemetry tracing/metrics integration with OTLP Collector references
- Golden-dataset evaluation and statistical drift detection
- Executable prompt-injection/red-team regression cases
- Deterministic resilience/chaos tests and staging load-smoke harness
- Ruff, MyPy, Bandit, pip-audit, pytest, compilation, Terraform validation, and Docker CI gates
- CycloneDX SBOM generation
- Keyless Cosign container signing and SBOM attestation in the release workflow
- Managed PostgreSQL/Redis production infrastructure reference
- Interactive demo walkthrough and synthetic customer case-study template
- Scheduled continuous-evaluation workflow

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
                +-----------------+------------------+
                |                 |                  |
          OIDC / API keys       RBAC            Policy + idempotency
          service identity   tenant + scopes       redaction
                +-----------------+------------------+
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
                                  |
                +-----------------+------------------+
                |                                    |
          PostgreSQL                            OpenTelemetry
        state + audit +                         traces + metrics
         migrations
                |                                    |
                +-----------------+------------------+
                                  v
                         CI / security / release
                  tests + SBOM + signed image + attestations
```

## Enterprise hardening

The production hardening contract is documented in [`month-7-platform/docs/ENTERPRISE-HARDENING.md`](month-7-platform/docs/ENTERPRISE-HARDENING.md).

It covers identity, service authentication, secrets, policy gates, redaction, idempotency, audit integrity, reliability, observability, supply-chain verification, infrastructure controls, and recovery targets.

### Production identity

OIDC authentication supports issuer discovery, rotating JWKS validation/caching, JWT signature verification, required claims, issuer/audience checks, tenant extraction, and scopes.

```text
FDE_OIDC_ISSUER=https://<identity-provider>
FDE_OIDC_AUDIENCE=<audience>
FDE_OIDC_JWKS_URL=<optional-explicit-jwks-url>
```

Never commit tokens, signing keys, API keys, or provider secrets.

### Mutation safety and high-impact actions

Production mutation requests require `X-Idempotency-Key`. Reusing a key with a different request fingerprint returns `409 Conflict`. High-impact actions can be blocked pending authorized human approval according to action, severity, confidence, amount, and client tier.

### Data and audit integrity

PostgreSQL stores application and audit state. The migration runner provides version tracking, SHA-256 checksums, duplicate detection, drift detection, and transactional execution. Audit events are centrally persisted and a hash-chain utility provides tamper-evident event chaining for immutable archival pipelines.

### AI security and evaluation

The red-team corpus covers prompt injection, instruction override, secret extraction, tenant-boundary abuse, tool manipulation, malformed output, and resource abuse. Statistical evaluation drift detection and scheduled CI evaluation are included alongside deterministic chaos and load-smoke tests.

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

```text
Pull request / main push
        |
        +--> Platform Quality
        |      pytest / six-domain smoke
        |      security controls / chaos
        |      Ruff / MyPy / Bandit / pip-audit
        |      Terraform validate / SBOM / load smoke
        |      Docker build
        |
        +--> Static security
        |      Semgrep
        |
        +--> Scheduled Continuous Evaluation
        |      red-team + evaluation drift gate
        |
        +--> Release Attestation
               immutable GHCR image
               keyless Cosign signature
               CycloneDX SBOM
               SBOM attestation
```

Production admission should verify image signatures and provenance before deployment.

---

## Production reference

See [`month-7-platform/docs/PRODUCTION.md`](month-7-platform/docs/PRODUCTION.md) and [`month-7-platform/docs/ENTERPRISE-HARDENING.md`](month-7-platform/docs/ENTERPRISE-HARDENING.md) for managed PostgreSQL/Redis topology, deployment order, rollback model, telemetry, identity, secrets, mutation safety, and operational controls.

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

For production, inject a managed secrets provider and use managed PostgreSQL/Redis with TLS.

---

## Evidence and demonstrations

- [`docs/DEMO.md`](month-7-platform/docs/DEMO.md) — interactive walkthrough
- [`docs/CASE-STUDY.md`](month-7-platform/docs/CASE-STUDY.md) — synthetic customer-style case study template
- [`docs/PRODUCTION.md`](month-7-platform/docs/PRODUCTION.md) — production deployment reference
- [`docs/ENTERPRISE-HARDENING.md`](month-7-platform/docs/ENTERPRISE-HARDENING.md) — production security/operations contract
- [`security/ai-threat-model.md`](month-7-platform/security/ai-threat-model.md) — AI threat model

Customer outcome numbers must only be added after a real deployment and measurement.

---

## Repository structure

```text
fde-mastery/
├── README.md
├── .github/workflows/
│   ├── platform-tests.yml
│   ├── evaluation.yml
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
    ├── evaluation/
    ├── shared_orchestrator/
    ├── deployment/
    ├── scripts/
    ├── docs/
    └── tests/
```

---

## Roadmap status

### Implemented engineering controls

- [x] Common `DomainAgent` contract
- [x] Six real domain adapters
- [x] Central router and resilience layer
- [x] End-to-end adapter execution tests
- [x] API-key authentication
- [x] OIDC issuer discovery + JWKS JWT validation
- [x] Tenant/scope/RBAC authorization
- [x] Short-lived service authentication + mTLS identity contract
- [x] PostgreSQL persistence boundary
- [x] Centralized audit-event schema/store
- [x] Tamper-evident audit hash-chain utility
- [x] Checksum-verified migration runner
- [x] Idempotency contract and PostgreSQL schema
- [x] Sensitive-data redaction boundary
- [x] High-impact policy gate / human-approval contract
- [x] Redis-compatible distributed rate limiting
- [x] OpenTelemetry integration and production Collector reference
- [x] Executable AI red-team regression suite
- [x] Statistical evaluation drift detector
- [x] Deterministic chaos/resilience tests
- [x] Staging load-smoke harness
- [x] Terraform format/validation gate
- [x] CycloneDX SBOM generation
- [x] Keyless Cosign image signing and SBOM attestation workflow
- [x] Managed PostgreSQL/Redis production reference
- [x] Scheduled continuous-evaluation workflow
- [x] Interactive demo walkthrough
- [x] Customer-style case-study template
- [x] CI quality/security/release gates

### Evidence requiring real operational use

- [ ] Real customer deployment and measured outcomes
- [ ] External penetration test / independent security assessment
- [ ] Production telemetry with real workload data
- [ ] Customer-specific case study with verified metrics
- [ ] Organization-specific managed secrets provider binding

---

## Responsible use

The domain projects use synthetic/example data and demonstrate engineering patterns. They are not financial advice, medical diagnosis/treatment, legal advice, regulatory certification, or proof of production performance.

High-impact workflows should retain authorized human review and appropriate domain-specific controls.

## About

**FDE Mastery** is built by **LloydCoder** as a hands-on portfolio for Forward Deployed Engineering, AI security, enterprise automation, and production AI systems engineering.

The emphasis is on the surrounding system—not merely an LLM call: **schemas, policy, evaluation, recovery, orchestration, security, governance, persistence, observability, and release evidence.**

## License

See [`LICENSE`](./LICENSE).
