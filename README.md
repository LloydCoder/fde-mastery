# FDE Mastery

### Production-oriented AI systems across security, finance, healthcare, logistics, legal, and revenue operations.

FDE Mastery is a hands-on portfolio for **Forward Deployed Engineering, AI systems engineering, AI security, and enterprise automation**. It contains six domain-specific AI systems plus a Month 7 platform layer that integrates them behind a common agent contract, API gateway, evaluation layer, deployment tooling, and security controls.

> **Portfolio objective:** demonstrate the engineering judgment required to take AI from a model/API experiment to a governed system that can operate inside a real business workflow.

---

## What this repository demonstrates

- **Forward Deployed Engineering** — translating operational problems into working technical systems.
- **AI systems engineering** — typed contracts, orchestration, recovery paths, model-provider abstraction, and structured outputs.
- **AI security** — authentication, authorization, domain isolation, deterministic guardrails, human approval boundaries, and audit-oriented outputs.
- **Enterprise automation** — domain agents connected to a shared platform rather than isolated demos.
- **Evaluation engineering** — golden datasets, domain evaluation harnesses, and platform integration tests.
- **Regulated-domain engineering** — security, financial risk, healthcare, logistics compliance, legal operations, and RevOps governance.
- **Platform engineering** — API gateway, domain routing, Docker deployment, health/readiness endpoints, and CI test automation.

---

# Architecture

```text
                         FDE MASTERY PLATFORM
                                  │
                         ┌────────▼────────┐
                         │   API Gateway   │
                         │ FastAPI + Auth  │
                         └────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │ Authentication /           │
                    │ Authorization / Rate Limit │
                    └─────────────┬─────────────┘
                                  │
                         ┌────────▼────────┐
                         │  Agent Router   │
                         │ Domain Contract │
                         └────────┬────────┘
                                  │
          ┌───────────┬───────────┼───────────┬───────────┐
          ▼           ▼           ▼           ▼           ▼           ▼
     Security     Finance     HealthTech  Logistics     Legal       RevOps
      Adapter      Adapter      Adapter     Adapter     Adapter      Adapter
          │           │           │           │           │           │
          ▼           ▼           ▼           ▼           ▼           ▼
       Month 1      Month 2     Month 3     Month 4     Month 5     Month 6
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ Evaluation & Evidence   │
                    │ Golden data + pytest    │
                    └─────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
              Audit / Metrics              Human Review
```

The Month 7 layer is the integration capstone. The six domain projects remain independently understandable while adapters expose them through a common `DomainAgent` contract.

---

# Month 7 — Platform Capstone

`month-7-platform/`

Month 7 turns the six domain systems into a unified platform-oriented architecture.

### Current platform capabilities

- Common `DomainAgent` contract
- Six domain adapters
- Central `AgentRouter`
- FastAPI gateway
- Domain-aware client authorization
- API-key authentication
- Separate administrator authorization
- Per-client sliding-window rate limiting
- Request body-size protection
- Health and agent-readiness endpoints
- Capability discovery endpoint
- Platform integration tests
- GitHub Actions test workflow
- Docker-based deployment foundation
- Client onboarding and preferences infrastructure
- Synthetic evaluation datasets

### Security model

```text
Request
   │
   ▼
API authentication
   │
   ▼
Client authorization
   │
   ▼
Domain authorization
   │
   ▼
Request-size / rate controls
   │
   ▼
Domain agent
   │
   ▼
Structured result + audit identifier
```

The current authentication and rate-limiting implementations are **portfolio/demo controls**. Production deployments should use managed identity, secret management, distributed rate limiting, durable persistence, centralized audit logging, and additional network/application controls.

---

# Six-domain FDE portfolio

| Domain | System | Core problem | Engineering focus |
|---|---|---|---|
| **01 — Cybersecurity** | SOC Triage Agent | SIEM alert analysis and triage | Threat classification, recovery, provider fallback, evaluation |
| **02 — Finance** | Transaction Risk & Governance Engine | Transaction risk and mitigation | Risk scoring, policy hard-stops, execution orders, audit ledger |
| **03 — HealthTech** | HealthTech Compliance & Triage Engine | PHI handling and clinical triage | De-identification, clinical risk rules, auditability |
| **04 — Logistics** | Supply Chain Risk Engine | Shipment and telemetry risk | Compliance checks, cold-chain detection, mitigation workflows |
| **05 — Legal** | Contract Risk Analysis Engine | Contract clause risk | Deterministic clause analysis, redlines, counsel routing |
| **06 — RevOps** | Enterprise Automation Engine | Pipeline and account operations | Health scoring, deal governance, churn intervention, workflow routing |

---

## 01 — Cybersecurity

`month-1-cybersecurity/`

A SOC triage system that processes raw SIEM-style security logs and produces structured threat reports.

Key engineering patterns:

- OpenAI and Anthropic provider support
- Pydantic schema validation
- Stateful recovery/retry loops
- Offline mock mode
- Golden-dataset evaluation
- Structured threat severity, category, action, and mitigation outputs

[Open the Cybersecurity project →](./month-1-cybersecurity/README.md)

---

## 02 — Finance

`month-2-finance/`

A transaction risk and governance engine covering card purchases, wires, crypto swaps, cross-border risk, velocity signals, mitigation planning, and audit records.

Key engineering patterns:

- Deterministic policy fallback
- LLM-assisted evaluation
- Risk scoring from 0–100
- Sanctions hard-stop rules
- Human-approval boundaries
- Structured execution orders
- Audit-oriented ledger entries
- Golden-dataset benchmark suite

[Open the Finance project →](./month-2-finance/README.md)

---

## 03 — HealthTech

`month-3-healthtech/`

A healthcare processing pipeline covering PHI de-identification, clinical risk triage, and audit-oriented processing.

Key engineering patterns:

- Structured clinical payloads
- PHI detection and redaction
- Deterministic clinical risk triggers
- Risk scoring
- FHIR-oriented integration mapping
- HITECH/HIPAA-oriented audit design
- Golden-dataset evaluation

**Important:** this project is an engineering demonstration and is not represented as a certified medical device, clinical decision-support product, or compliance certification.

[Open the HealthTech project →](./month-3-healthtech/README.md)

---

## 04 — Logistics

`month-4-logistics/`

A supply-chain risk engine combining shipment data, IoT telemetry, trade compliance signals, and mitigation workflows.

Key engineering patterns:

- Shipment schema validation
- Cold-chain excursion detection
- Sanctions/compliance rules
- HS-code validation examples
- Route optimization and quarantine workflows
- Chain-of-custody audit records
- Golden-dataset evaluation

[Open the Logistics project →](./month-4-logistics/README.md)

---

## 05 — Legal

`month-5-legal/`

A contract risk analysis and redline engine for commercial agreements such as MSAs, SOWs, DPAs, and NDAs.

Key engineering patterns:

- Clause taxonomy
- Deterministic legal-risk rules
- Risk scoring
- Proposed redlines
- Counsel approval routing
- Contract audit records
- Golden-dataset evaluation

**Important:** this project is a software-engineering demonstration, not legal advice or a substitute for qualified counsel.

[Open the Legal project →](./month-5-legal/README.md)

---

## 06 — RevOps

`month-6-revops/`

A revenue-operations automation engine for opportunity health scoring, deal governance, churn-risk detection, and workflow routing.

Key engineering patterns:

- Telemetry-driven health scoring
- Discount governance
- ARR thresholds
- Executive-sponsorship checks
- Churn-risk detection
- CRM/communication workflow targets
- Explicit automation flags
- Golden-dataset evaluation

[Open the RevOps project →](./month-6-revops/README.md)

---

# Evaluation philosophy

> **A demo is not enough. An AI system needs measurable behavior.**

Each domain contains a `golden_dataset.json` and an `eval_harness.py` used to benchmark labeled scenarios. Month 7 adds integration tests that exercise the API → router → adapter path across all six domains.

```text
golden_dataset.json
        │
        ▼
 eval_harness.py
        │
        ├── deterministic evaluation
        ├── optional model evaluation
        └── expected-vs-actual comparison
        │
        ▼
 benchmark result
        │
        ▼
 platform integration tests
```

Reported benchmark figures in domain READMEs should be treated as repository test-suite results, not claims of production accuracy.

---

# Repository structure

```text
fde-mastery/
├── README.md
├── LICENSE
├── requirements.txt
├── .github/
│   └── workflows/
│       └── platform-tests.yml
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
    ├── shared_orchestrator/
    │   ├── domain_agent.py
    │   ├── router.py
    │   └── adapters/
    ├── deployment/
    │   ├── api_gateway/
    │   │   ├── main.py
    │   │   ├── auth.py
    │   │   ├── rate_limit.py
    │   │   └── .env.example
    │   └── docker/
    └── tests/
        └── test_platform_integration.py
```

---

# Quick start

## Requirements

- Python 3.10+
- `pip`
- API keys only for live LLM-provider execution

## Domain evaluation

```bash
cd month-2-finance
python eval_harness.py --mock
```

See each domain README for its exact evaluation and demo commands.

## Platform tests

```bash
cd month-7-platform
pip install fastapi uvicorn pydantic pytest httpx
python -m pytest tests/test_platform_integration.py -q
```

## Platform API authentication

Set environment variables before running the gateway:

```bash
export FDE_API_KEYS="your-application-key"
export FDE_ADMIN_API_KEYS="your-admin-key"
```

Never commit real credentials. A template is provided at:

`month-7-platform/deployment/api_gateway/.env.example`

Application endpoints accept either:

```text
Authorization: Bearer <application-key>
```

or:

```text
X-API-Key: <application-key>
```

Administrative endpoints require the dedicated administrator key.

---

# Engineering principles

### 1. Deterministic controls around probabilistic components

LLMs are useful for reasoning and extraction, but high-impact decisions should have explicit schemas, validation, deterministic policies, and human-review boundaries where appropriate.

### 2. Structured contracts

Pydantic models and the Month 7 `DomainAgent` interface define contracts between inputs, reasoning components, decisions, workflows, and platform orchestration.

### 3. Graceful degradation

Where implemented, systems can fall back to deterministic logic or mock execution so evaluation does not depend entirely on live model APIs.

### 4. Evaluation before optimization

Golden datasets provide repeatable baselines before changing prompts, rules, models, or orchestration.

### 5. Security by design

Authentication, authorization, input limits, client isolation, domain isolation, human approval, and audit-oriented outputs are treated as first-class engineering concerns.

### 6. Human-in-the-loop governance

The systems distinguish actions that can be automated from actions that should require an analyst, physician, counsel, compliance officer, or other authorized human depending on the domain.

---

# Roadmap

The repository is being hardened progressively from a domain-project portfolio into a reusable FDE platform.

- [x] Common `DomainAgent` contract
- [x] Six domain adapters
- [x] Central domain router
- [x] Real API → router → adapter execution path
- [x] Platform integration tests
- [x] GitHub Actions platform test workflow
- [x] API-key authentication
- [x] Administrator authorization
- [x] Per-client rate limiting and request-size controls
- [x] Updated platform architecture documentation
- [ ] Distributed rate limiting with Redis
- [ ] Durable PostgreSQL client/billing state
- [ ] Production-grade OIDC/JWT identity
- [ ] Centralized audit/event store
- [ ] Repository-wide `pyproject.toml`
- [ ] Ruff + MyPy + pre-commit
- [ ] Full CI quality/security gates
- [ ] Dependency and container scanning
- [ ] Standardized evaluation result artifacts
- [ ] AI threat-model and prompt-injection test suites
- [ ] Structured observability, tracing, cost, and latency metrics
- [ ] Production deployment reference architecture
- [ ] Architecture Decision Records
- [ ] Interactive demonstrations and case studies

---

# Security

Do not commit API keys, credentials, patient data, financial records, private contracts, or other sensitive information.

The Month 7 gateway currently demonstrates API-key authentication, administrator authorization, domain authorization, per-client rate limiting, request-size controls, and structured error handling.

These controls are **portfolio/demo implementations**, not a production security certification. Production deployment requires managed identity, secret rotation, distributed state, centralized logging, monitoring, network controls, formal threat modeling, penetration testing, and domain-specific compliance review.

---

# Responsible-use notes

The domain projects use synthetic/example data and demonstrate engineering patterns.

They should not be interpreted as:

- financial or investment advice;
- medical diagnosis or treatment advice;
- legal advice;
- regulatory certification;
- proof of production deployment;
- proof of performance in a real customer environment.

Production deployment requires domain-specific validation, security controls, integration testing, compliance review, monitoring, and operational ownership.

---

# About

**FDE Mastery** is built by **LloydCoder** as a hands-on portfolio for Forward Deployed Engineering, AI security, enterprise automation, and production AI systems engineering.

The emphasis is not simply on calling an LLM. It is on designing the surrounding system: **schemas, policies, evaluation, recovery, orchestration, security, governance, and evidence.**

---

## License

See [LICENSE](./LICENSE).
