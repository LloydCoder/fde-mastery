# FDE Mastery

### Production-oriented AI systems across security, finance, healthcare, logistics, legal, and revenue operations.

FDE Mastery is a six-domain engineering portfolio focused on building **deployable, governed AI systems for real operational workflows**.

The repository explores a consistent architecture for domain-specific agents: strict Pydantic schemas, deterministic policy controls, LLM-assisted reasoning where appropriate, resilient fallback paths, golden-dataset evaluation, explicit human-approval boundaries, and audit-oriented outputs.

> **Portfolio objective:** demonstrate the engineering judgment required to take AI from a model/API experiment to a system that can operate inside a real business workflow.

---

## What this repository demonstrates

- **Forward Deployed Engineering (FDE)** — translating operational problems into working technical systems.
- **AI systems engineering** — structured inputs/outputs, orchestration, recovery paths, and model-provider abstraction.
- **AI security** — security operations workflows, validation, deterministic guardrails, and auditability.
- **Enterprise automation** — explicit workflow actions and human-in-the-loop boundaries.
- **Evaluation engineering** — golden datasets and repeatable benchmark harnesses rather than relying only on qualitative demos.
- **Regulated-domain engineering** — security, financial risk, healthcare, logistics compliance, legal operations, and RevOps governance.

---

## Architecture pattern

```text
                    ┌──────────────────────────┐
                    │   Operational Input      │
                    │ logs / transactions /    │
                    │ clinical / shipment /    │
                    │ contract / CRM data      │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Schema Validation        │
                    │ Pydantic / typed models  │
                    └────────────┬─────────────┘
                                 │
                                 ▼
              ┌────────────────────────────────────┐
              │     Domain Evaluation Engine      │
              │                                    │
              │ LLM reasoning + deterministic     │
              │ policy / rules / fallback logic   │
              └───────────────┬────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
      ┌──────────────────┐        ┌──────────────────┐
      │ Structured       │        │ Risk / Policy    │
      │ Decision         │        │ & Exception      │
      │                  │        │ Evaluation       │
      └────────┬─────────┘        └────────┬─────────┘
               │                           │
               └─────────────┬─────────────┘
                             ▼
                    ┌───────────────────┐
                    │ Action / Workflow │
                    │ Orchestration      │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
             Autonomous action     Human approval
                    │                   │
                    └─────────┬─────────┘
                              ▼
                    ┌───────────────────┐
                    │ Audit / Evidence  │
                    │ & Evaluation      │
                    └───────────────────┘
```

The exact implementation differs by domain; the goal is to keep the **engineering principles** consistent while adapting the system to the operational context.

---

# Six-domain FDE portfolio

| Domain | System | Core problem | Engineering focus |
|---|---|---|---|
| **01 — Cybersecurity** | SOC Triage Agent | SIEM alert analysis and triage | Threat classification, schema recovery, provider fallback, evaluation |
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
- Immutable audit-oriented ledger entries
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

A central principle of FDE Mastery is:

> **A demo is not enough. An AI system needs measurable behavior.**

Each domain contains a `golden_dataset.json` and an `eval_harness.py` used to benchmark the implementation against labeled scenarios.

The evaluation layer is intended to make regressions visible as the systems evolve.

Typical flow:

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
```

The current domain READMEs document the benchmark cases and reported results. These figures should be treated as **repository test-suite results**, not claims of production accuracy.

---

# Engineering principles

### 1. Deterministic controls around probabilistic components

LLMs are useful for reasoning and extraction, but high-impact decisions should have explicit schemas, validation, deterministic policies, and human-review boundaries where appropriate.

### 2. Structured outputs

Pydantic models define the contract between inputs, reasoning components, decisions, workflows, and audit records.

### 3. Graceful degradation

Where implemented, systems can fall back to deterministic logic or mock execution so core evaluation and demonstrations do not depend entirely on live model APIs.

### 4. Evaluation before optimization

Golden datasets provide a repeatable baseline before changing prompts, rules, models, or orchestration.

### 5. Auditability

High-impact workflows expose structured decisions, exception flags, mitigation steps, and audit-oriented records rather than returning an opaque natural-language answer.

### 6. Human-in-the-loop governance

The systems distinguish actions that can be automated from actions that should require an analyst, physician, counsel, compliance officer, or other authorized human depending on the domain.

---

# Repository structure

```text
fde-mastery/
├── README.md
├── LICENSE
├── requirements.txt
│
├── month-1-cybersecurity/
│   ├── README.md
│   ├── agent.py
│   ├── schemas.py
│   ├── eval_harness.py
│   ├── golden_dataset.json
│   └── main.py
│
├── month-2-finance/
│   ├── README.md
│   ├── agent.py
│   ├── schemas.py
│   ├── eval_harness.py
│   ├── golden_dataset.json
│   └── main.py
│
├── month-3-healthtech/
│   └── ...
│
├── month-4-logistics/
│   └── ...
│
├── month-5-legal/
│   └── ...
│
└── month-6-revops/
    └── ...
```

---

# Quick start

## Requirements

- Python 3.10+
- `pip`
- API key only for domains/configurations that use a live LLM provider

## Install

```bash
git clone https://github.com/LloydCoder/fde-mastery.git
cd fde-mastery
pip install -r requirements.txt
```

## Run an offline evaluation

For example:

```bash
cd month-2-finance
python eval_harness.py --mock
```

Other domain READMEs contain their domain-specific commands and options.

## Run a domain demo

```bash
cd month-2-finance
python main.py
```

See each domain README before enabling live API execution.

---

# Technology

- Python
- Pydantic v2
- OpenAI API
- Anthropic API
- pytest
- python-dotenv
- Loguru
- JSON-based evaluation datasets

The current dependency baseline is intentionally small; repository-wide tooling, CI, packaging, observability, and deployment infrastructure are part of the engineering hardening roadmap.

---

# Roadmap

FDE Mastery is being hardened progressively from a domain-project portfolio into a reusable engineering platform.

- [ ] Repository-wide packaging with `pyproject.toml`
- [ ] Standardized test suite and coverage reporting
- [ ] Ruff + type checking + pre-commit
- [ ] GitHub Actions CI
- [ ] Dependency and secret scanning
- [ ] Standardized evaluation result format
- [ ] AI security and threat-model test suites
- [ ] Structured observability and cost/latency metrics
- [ ] Dockerized reproducible demos
- [ ] Architecture Decision Records (ADRs)
- [ ] Production deployment reference architectures
- [ ] Interactive demonstrations and screenshots
- [ ] Domain-specific case studies

---

# Security

Do not commit API keys, credentials, patient data, financial records, private contracts, or other sensitive information to this repository.

Security hardening, threat modeling, and automated security checks are part of the roadmap for the repository.

See [SECURITY.md](./SECURITY.md) once the repository security policy is established.

---

# Responsible-use notes

The domain projects use synthetic/example data and are intended to demonstrate engineering patterns.

They should not be interpreted as:

- financial or investment advice;
- medical diagnosis or treatment advice;
- legal advice;
- regulatory certification;
- proof of production deployment;
- proof of performance in a real customer environment.

Production deployment would require domain-specific validation, security controls, integration testing, compliance review, monitoring, and operational ownership.

---

# About

**FDE Mastery** is built by **LloydCoder** as a hands-on portfolio for Forward Deployed Engineering, AI security, enterprise automation, and production AI systems engineering.

The emphasis is not simply on calling an LLM. It is on designing the surrounding system: **schemas, policies, evaluation, recovery, orchestration, governance, and evidence.**

---

## License

See [LICENSE](./LICENSE).
