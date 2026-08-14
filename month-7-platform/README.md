# Month 7: Platform Layer — Unified Client Onboarding, Deployment & Delivery

The capstone infrastructure layer that transforms 6 domain-specific agents into a **sellable, zero-delay managed service**. This platform provides client onboarding, schema auto-mapping, preference configuration, containerized deployment, unified API gateway, multi-system integrations, observability, and billing.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLIENT ONBOARDING (Day 1-2)                                                │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────────┐           │
│  │ Schema      │  │ Preference      │  │ Golden Dataset        │           │
│  │ Mapper      │→ │ Engine          │→ │ Generator            │           │
│  │ (auto-map)  │  │ (rubric overrides)│  │ (50 cases from sample)│          │
│  └─────────────┘  └─────────────────┘  └─────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  DEPLOYMENT (Day 2-3)                                                       │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────────┐           │
│  │ Docker      │  │ Terraform       │  │ API Gateway         │           │
│  │ (per-client)│  │ (VPC deploy)    │  │ FastAPI /{client}   │           │
│  └─────────────┘  └─────────────────┘  └─────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  SHARED ORCHESTRATOR                                                        │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────────┐           │
│  │ Agent       │  │ Context         │  │ Escalation          │           │
│  │ Router      │  │ Manager         │  │ Matrix              │           │
│  │ (6 domains) │  │ (cross-domain)  │  │ (human handoff)     │           │
│  └─────────────┘  └─────────────────┘  └─────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  INTEGRATIONS & OBSERVABILITY                                               │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────────┐           │
│  │ Slack Bot   │  │ ServiceNow      │  │ Drift Detector      │           │
│  │ Webhook     │  │ Custom API      │  │ Confidence Tracker  │           │
│  │             │  │                 │  │ Billing Meter       │           │
│  └─────────────┘  └─────────────────┘  └─────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The "Zero-Delay" Client Journey

| Phase | Timeline | Action | Output |
|-------|----------|--------|--------|
| **Discovery** | 30 min | Map pain to pre-built domain agent | SOW with template pricing |
| **Onboarding** | 2 hours | Upload sample data → auto-map → generate golden dataset | 50-case benchmark, >90% pass |
| **Deployment** | 4 hours | Docker container + API endpoint + integrations | Live `/api/{client}/{domain}/triage` |
| **Value Proof** | Week 2 | Drift detection + confidence tracking + billing | Business review with metrics |

---

## Quick Start

### 1. Onboard a New Client

```bash
cd month-7-platform
python main.py onboard   --client-id retailer-corp   --client-name "RetailCo Global"   --domains cybersecurity,finance   --sample-dir ./sample_data/retailer-corp   --tier growth
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

```
month-7-platform/
├── README.md                              # This file
├── schemas.py                             # Unified platform schemas
├── main.py                                # Platform CLI (onboard / eval / simulate)
├── eval_harness.py                        # Platform-level evaluation harness
│
├── client_onboarding/
│   ├── schema_mapper.py                   # Auto-map client data → domain schemas
│   ├── preference_engine.py               # Client rubric overrides
│   ├── golden_generator.py                # Generate 50-case golden dataset from samples
│   └── onboard_cli.py                   # Onboarding orchestrator
│
├── deployment/
│   ├── docker/
│   │   ├── Dockerfile                     # Per-client container image
│   │   └── docker-compose.yml             # Full stack (API + Redis + Prometheus)
│   ├── terraform/                         # AWS/GCP/Azure VPC IaC (scaffold)
│   └── api_gateway/
│       └── main.py                        # FastAPI: /{client_id}/{domain}/triage
│
├── shared_orchestrator/
│   ├── router.py                          # Multi-domain agent router
│   ├── context_manager.py                 # Cross-domain memory & aggregate scoring
│   └── escalation_matrix.py             # Human handoff protocol manager
│
├── integrations/
│   ├── slack_bot.py                       # Slack alerting & notifications
│   ├── servicenow.py                      # Incident/ticket creation
│   └── custom_webhook.py                  # Generic downstream webhook
│
├── observability/
│   ├── drift_detector.py                  # Weekly eval re-run & pass-rate delta
│   ├── confidence_tracker.py              # Per-client confidence degradation alerts
│   └── billing_meter.py                   # Per-API-call invoicing
│
└── demo/
    └── enterprise_sales_simulation.py     # Live prospect walkthrough script
```

---

## Key Components

### Client Onboarding

| Module | Purpose |
|--------|---------|
| `schema_mapper.py` | Infers field mappings from client sample JSON to domain schemas using candidate key matching |
| `preference_engine.py` | Applies client-specific rubric overrides (e.g., stricter discount thresholds for conservative firms) |
| `golden_generator.py` | Creates 50-case synthetic benchmark datasets seeded from real client data patterns |
| `onboard_cli.py` | One-command onboarding: config → mapping → preferences → golden dataset → deployment plan |

### Deployment

| Component | Purpose |
|-----------|---------|
| `Dockerfile` | Builds per-client container with domain agent + API gateway |
| `docker-compose.yml` | Orchestrates API gateway, Redis cache, and Prometheus metrics |
| `api_gateway/main.py` | FastAPI app exposing `POST /api/{client_id}/{domain}/triage` with auth, billing, and audit |

### Shared Orchestrator

| Component | Purpose |
|-----------|---------|
| `router.py` | Routes requests to the correct domain agent instance based on URL path |
| `context_manager.py` | Maintains cross-domain memory (e.g., finance fraud signal informs cybersecurity triage) |
| `escalation_matrix.py` | Creates, tracks, and resolves human escalation tickets with assignment and status |

### Integrations

| Integration | Trigger | Target |
|-------------|---------|--------|
| **Slack Bot** | Every triage result | `#fde-alerts` channel with severity-colored attachments |
| **ServiceNow** | Escalated cases | Auto-create incident with assignment group |
| **Custom Webhook** | Configurable per client | POST triage payload to client-defined endpoint |

### Observability

| Module | Function |
|--------|----------|
| `drift_detector.py` | Re-runs golden dataset weekly, flags >5% pass-rate degradation |
| `confidence_tracker.py` | Rolling window mean/min confidence; alerts if mean < 0.85 or min < 0.70 |
| `billing_meter.py` | Tracks calls per domain, applies tier pricing, generates `BillingRecord` invoices |

---

## Pricing Model

| Tier | Domains | Calls/Month | Price/Month | Includes |
|------|---------|-------------|-------------|----------|
| **Starter** | 1 | 10,000 | $5,000 | API access, Slack bot, email support |
| **Growth** | 2 | 50,000 | $15,000 | + Deal Desk integration, drift monitoring, Clearbit enrichment |
| **Enterprise** | All 6 | Unlimited | $50,000 | + VPC deploy, 24/7 support, custom schema mapping, dedicated CSM |

**Value proposition**: *Traditional consultants bill $300/hr and take 8 weeks to build. We deploy in 48 hours because the agent is already built — you pay for configuration, not creation.*

---

## Benchmark Evaluation Results

The platform evaluation harness validates all infrastructure components:

| Test | Component | Status |
|------|-----------|--------|
| Schema Mapper | Auto-infers 4/6 required cybersecurity fields from sample | ✅ PASS |
| Preference Engine | Loads default rubric + applies client override | ✅ PASS |
| Golden Generator | Creates 10-case dataset in <1s | ✅ PASS |
| Agent Router | Registers and lists domain agents | ✅ PASS |
| Escalation Matrix | Creates and resolves escalation records | ✅ PASS |
| Drift Detector | Simulates 96.5% pass rate, no drift | ✅ PASS |
| Confidence Tracker | Records 0.94 confidence, computes mean | ✅ PASS |
| Billing Meter | 2 calls @ $0.03 = $0.06 billed | ✅ PASS |

**Platform Pass Rate: 100% (8/8)**

---

## Sales Simulation

Run the enterprise sales walkthrough to demonstrate zero-delay value to prospects:

```bash
python demo/enterprise_sales_simulation.py
```

Output includes:
- **Discovery**: 5-minute pain mapping to pre-built agent
- **Onboarding**: Live schema mapping + golden dataset generation
- **Deployment**: API endpoint live within 10 minutes
- **Value Proof**: Week 2 metrics showing 95%+ containment, 340 hrs/week saved

---

## License & Attribution

Part of the **FDE Mastery** curriculum — a 6-month production engineering roadmap for deterministic, schema-guaranteed LLM agents.

| Month | Domain | Tag |
|-------|--------|-----|
| 1 | Cybersecurity | `v1.0-soc-triage` |
| 2 | Finance | `v1.1-finance-risk-engine` |
| 3 | HealthTech | `v1.2-healthtech-hipaa-engine` |
| 4 | Logistics | `v1.3-logistics-supply-chain` |
| 5 | Legal | `v1.4-legal-contract-risk` |
| 6 | RevOps | `v1.5-revops-enterprise-automation` |
| 7 | **Platform** | `v2.0-platform-layer` |
