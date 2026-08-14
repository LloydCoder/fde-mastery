# FDE Mastery

### Production-oriented AI systems across security, finance, healthcare, logistics, legal, and revenue operations.

FDE Mastery is a hands-on portfolio for **Forward Deployed Engineering, AI systems engineering, AI security, and enterprise automation**. It combines six domain AI systems with a Month 7 platform capstone that adds shared contracts, orchestration, tenant/domain controls, persistence, evaluation, observability, and CI security gates.

> **Portfolio objective:** demonstrate the engineering judgment required to move AI from a model/API experiment to a governed system that can operate inside a real business workflow.

## What this repository demonstrates

- Forward Deployed Engineering and customer-problem decomposition
- Typed AI-system contracts and domain adapters
- Agent orchestration and structured outputs
- Deterministic controls around probabilistic components
- Client and domain isolation
- API authentication and administrator authorization
- Request-size protection and rate limiting
- Durable PostgreSQL persistence architecture
- Optional Redis-backed distributed rate limiting
- Golden-dataset evaluation and integration tests
- Structured request observability
- AI threat modeling and prompt-injection abuse cases
- Ruff, MyPy, Bandit, pip-audit, and GitHub Actions quality gates
- Human-in-the-loop boundaries for high-impact workflows

---

# Architecture

```text
                         FDE MASTERY PLATFORM
                                  │
                         ┌────────▼────────┐
                         │   FastAPI API   │
                         └────────┬────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
       Authentication      Authorization        Request Controls
       API/Admin keys      Client + Domain       Size + Rate Limit
              │                   │                   │
              └───────────────────┼───────────────────┘
                                  │
                         ┌────────▼────────┐
                         │  Agent Router   │
                         │ Domain Contract │
                         └────────┬────────┘
                                  │
        ┌──────────┬──────────────┼──────────────┬──────────┬──────────┐
        ▼          ▼              ▼              ▼          ▼          ▼
    Security    Finance       HealthTech      Logistics   Legal      RevOps
     Adapter     Adapter       Adapter        Adapter    Adapter     Adapter
        │          │              │              │          │          │
        ▼          ▼              ▼              ▼          ▼          ▼
     Month 1    Month 2         Month 3        Month 4    Month 5    Month 6
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
              Platform State              Observability
              Repository                  Request IDs/Logs
               /       \
              ▼         ▼
          In-memory  PostgreSQL
             local     durable
                                  │
                         ┌────────▼────────┐
                         │ Evaluation/CI   │
                         │ pytest + quality│
                         └─────────────────┘
```

---

# Month 7 — Platform Capstone

`month-7-platform/`

Month 7 integrates the six domain systems behind a common `DomainAgent` contract and central router while adding cross-cutting platform controls.

### Implemented

- Common `DomainAgent` interface
- Six domain adapters
- Central `AgentRouter`
- Real API → router → adapter execution path
- API-key authentication
- Separate administrator authorization
- Client/domain authorization
- Request body-size protection
- Per-client rate limiting
- PostgreSQL repository implementation
- Configurable memory/PostgreSQL storage backend
- Repository contract tests
- Request IDs and structured JSON request logging
- Health and capability endpoints
- Platform integration tests
- GitHub Actions test/quality/security workflow
- Ruff + MyPy configuration
- Bandit and pip-audit checks
- AI threat model
- Architecture Decision Record
- Production-oriented environment configuration

### Storage

Local tests default to:

```text
FDE_STORAGE_BACKEND=memory
```

Durable deployments can use:

```text
FDE_STORAGE_BACKEND=postgres
FDE_DATABASE_URL=postgresql+psycopg://...
```

### Rate limiting

The default implementation is process-local for simple development. Horizontally scaled deployments can use the optional Redis implementation with:

```text
FDE_REDIS_URL=redis://...
```

Production should use a managed Redis service or an API gateway with shared rate-limit state.

### Security model

```text
Request
  ↓
Authentication
  ↓
Client authorization
  ↓
Domain authorization
  ↓
Body-size + rate controls
  ↓
AgentRouter
  ↓
Domain adapter
  ↓
Structured result + request/audit identifiers
```

The repository demonstrates production-oriented controls but is **not a production security certification or compliance claim**.

---

# Six-domain FDE portfolio

| Domain | System | Core problem |
|---|---|---|
| **01 — Cybersecurity** | SOC Triage Agent | SIEM alert analysis and triage |
| **02 — Finance** | Transaction Risk & Governance Engine | Transaction risk and mitigation |
| **03 — HealthTech** | HealthTech Compliance & Triage Engine | PHI handling and clinical triage |
| **04 — Logistics** | Supply Chain Risk Engine | Shipment and telemetry risk |
| **05 — Legal** | Contract Risk Analysis Engine | Contract clause risk |
| **06 — RevOps** | Enterprise Automation Engine | Pipeline and account operations |

Each domain remains independently testable while Month 7 provides the common integration layer.

See the individual month READMEs for domain-specific implementation and evaluation details.

---

# Evaluation philosophy

> **A demo is not enough. An AI system needs measurable behavior.**

The domain projects use golden datasets and evaluation harnesses. Month 7 adds platform integration and security tests.

```text
golden datasets
      ↓
evaluation harnesses
      ↓
platform integration tests
      ↓
quality checks
      ↓
security/dependency checks
      ↓
CI evidence
```

Reported benchmark numbers are repository test-suite results, not claims of production accuracy.

---

# Repository structure

```text
fde-mastery/
├── README.md
├── requirements.txt
├── .github/workflows/platform-tests.yml
│
├── month-1-cybersecurity/
├── month-2-finance/
├── month-3-healthtech/
├── month-4-logistics/
├── month-5-legal/
├── month-6-revops/
│
└── month-7-platform/
    ├── schemas.py
    ├── pyproject.toml
    ├── observability.py
    ├── shared_orchestrator/
    │   ├── domain_agent.py
    │   ├── router.py
    │   └── adapters/
    ├── persistence/
    │   ├── models.py
    │   ├── repository.py
    │   ├── factory.py
    │   ├── postgres.py
    │   └── migrations/001_initial.sql
    ├── deployment/api_gateway/
    │   ├── main.py
    │   ├── auth.py
    │   ├── rate_limit.py
    │   ├── redis_rate_limit.py
    │   └── .env.example
    ├── security/ai-threat-model.md
    ├── docs/adr/
    └── tests/
        ├── test_platform_integration.py
        ├── test_persistence.py
        └── test_rate_limit.py
```

---

# Quick start

```bash
cd month-7-platform
pip install -e ".[test,quality,security]"
```

For local tests:

```bash
export FDE_API_KEYS="test-api-key"
export FDE_ADMIN_API_KEYS="test-admin-key"
export FDE_STORAGE_BACKEND="memory"
python -m pytest -q
```

For durable PostgreSQL execution:

```bash
export FDE_STORAGE_BACKEND="postgres"
export FDE_DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/fde_mastery"
```

Do not commit real credentials. Use a secret manager for deployed environments.

---

# Engineering principles

### 1. Deterministic controls around probabilistic components

LLMs are used for reasoning and extraction, but high-impact decisions require schemas, validation, explicit policy, and human approval where appropriate.

### 2. Tenant and domain isolation

Client identity and enabled domains are checked before domain-agent execution.

### 3. Storage abstraction

Application logic depends on `PlatformRepository`, not a specific database. This keeps local evaluation deterministic while allowing durable deployment.

### 4. Evaluation before optimization

Golden datasets and repeatable tests establish behavior before prompts, models, or orchestration are changed.

### 5. Security by design

Authentication, authorization, request limits, dependency auditing, threat modeling, and structured error handling are first-class concerns.

### 6. Human-in-the-loop governance

High-impact workflows distinguish automated analysis from actions requiring an authorized human.

---

# Security

Do not commit API keys, credentials, patient data, financial records, private contracts, or other sensitive information.

The Month 7 platform includes API authentication, administrator authorization, tenant/domain isolation, request-size controls, rate limiting, structured request identifiers, dependency auditing, static security checks, and an AI threat model.

See:

- `month-7-platform/security/ai-threat-model.md`
- `month-7-platform/docs/adr/0001-month-7-platform-architecture.md`

Production deployment still requires managed identity, secret rotation, distributed state, centralized audit/event storage, monitoring, network controls, penetration testing, red teaming, incident response, and domain-specific compliance review.

---

# Responsible use

The domain projects use synthetic/example data and demonstrate engineering patterns.

They are not represented as:

- financial or investment advice;
- medical diagnosis or treatment advice;
- legal advice;
- regulatory certification;
- proof of production deployment;
- proof of performance in a real customer environment.

---

# Roadmap

The core Month 7 hardening sequence is now implemented. Remaining work is primarily productionization and evidence rather than basic architecture.

- [x] Common `DomainAgent` contract
- [x] Six domain adapters
- [x] Central domain router
- [x] Real API → router → adapter execution path
- [x] Integration tests
- [x] API authentication and admin authorization
- [x] Client/domain isolation
- [x] Request-size protection and rate limiting
- [x] PostgreSQL persistence boundary and backend
- [x] Configurable storage backend
- [x] Redis distributed-rate-limit implementation
- [x] Structured request observability
- [x] Ruff + MyPy configuration
- [x] Bandit + pip-audit CI gates
- [x] AI threat model
- [x] Architecture Decision Record
- [ ] Production OIDC/JWT identity provider integration
- [ ] Centralized audit/event store
- [ ] Formal migration runner with version tracking
- [ ] Full distributed tracing and metrics backend
- [ ] Container image signing and SBOM publication
- [ ] Formal prompt-injection/red-team benchmark suite
- [ ] Production deployment reference with managed PostgreSQL/Redis
- [ ] Interactive demonstrations and customer case studies

---

# About

**FDE Mastery** is built by **LloydCoder** as a hands-on portfolio for Forward Deployed Engineering, AI security, enterprise automation, and production AI systems engineering.

The emphasis is not simply on calling an LLM. It is on designing the surrounding system: **schemas, policies, evaluation, recovery, orchestration, security, governance, persistence, and evidence.**

---

## License

See [LICENSE](./LICENSE).
