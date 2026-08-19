# Month 6: RevOps & Enterprise Automation Engine

An enterprise-grade revenue operations automation system that evaluates sales pipeline opportunities using telemetry-driven health scoring, enforces deal desk governance guardrails, automates churn risk intervention, and routes low-value leads to enrichment nurture sequences. Built on the same deterministic, schema-guaranteed architecture as Months 1–5.

---

## Architecture Overview

```
                  +-----------------------------+
                  | Incoming Opportunity        |
                  |  (CRM: Salesforce/HubSpot)  |
                  +--------------+--------------+
                                 |
                                 v
                  +-----------------------------+
                  |   RevOps Evaluation Engine  |
                  | (Claude Sonnet / Rule Base) |
                  +--------------+--------------+
                                 |
            +--------------------+--------------------+
            |                                         |
            v                                         v
+-------------------------+               +-------------------------+
| Health Score (0-100)    |               | Exception Flag Analysis |
| Telemetry-Driven        |               | - Discount Governance     |
| Churn Risk Detection    |               | - Exec Sponsor Check      |
+------------+------------+               | - ARR Threshold           |
             |                              +------------+------------+
             |                                           |
             |                              +-------------------------+
             |                              | Automation Workflow     |
             |                              | - Salesforce Routing    |
             |                              | - Slack Notifications   |
             |                              | - Calendly/HubSpot      |
             |                              +------------+------------+
             |                                           |
             v                                           v
+--------------------+----------------------------------+
|                                                     |
|              Execution Orchestrator                 |
|          - Auto-Assign Enterprise AE                  |
|          - Deal Desk Escalation                     |
|          - Churn Risk Alerting                      |
|          - Nurture Sequence Trigger                 |
+--------------------+--------------------------------+
                     |
                     v
            +-----------------------------+
            |   Immutable RevOps Ledger   |
|   (SHA-16 Opp Hash, Health Score)       |
            +-----------------------------+
```

### Key Components

1. **Opportunity Models & Schemas (`schemas.py`)** — Pydantic models enforcing strict validation on CRM opportunity payloads, telemetry metrics, automation workflows, and audit records.
2. **RevOps Evaluation Engine (`agent.py`)** — Deterministic rule engine scoring opportunities across four risk tiers using telemetry thresholds, discount governance, executive sponsorship, and ARR minimums.
3. **Evaluation Harness (`eval_harness.py`)** — Automated benchmark runner executing golden dataset test cases against the rule engine.
4. **Live Demo (`main.py`)** — End-to-end driver processing opportunities, generating health scores, triggering automation workflows, and writing immutable audit records.
5. **Golden Dataset (`golden_dataset.json`)** — Pre-validated benchmark edge cases testing PQL auto-assignment, deal desk escalation, churn risk flagging, and nurture routing.

---

## Health Score & Risk Policy

Opportunities are assigned a continuous health score between **0.0** and **100.0** along with a discrete risk classification:

| Health Score | Classification | Action | Handling / Automation Workflow |
| :--- | :--- | :--- | :--- |
| **70.0 – 100.0** | `LOW` | `AUTO_ASSIGN_ENTERPRISE_AE` | **Autonomous**: Salesforce auto-assignment, Calendly scheduling, Slack AE notification. |
| **45.0 – 69.9** | `MEDIUM` | `TRIGGER_ENRICHMENT_NURTURE` | **Autonomous**: HubSpot nurture sequence, Clearbit enrichment, 90-day re-evaluation queue. |
| **60.0 – 89.9** | `HIGH` | `ESCALATE_DEAL_DESK` | **Autonomous**: Salesforce Deal Desk queue, DocuSign CLM lock, AE/Manager email alert. |
| **90.0 – 100.0** | `CRITICAL` | `FLAG_CHURN_RISK` | **Autonomous**: Salesforce churn alert, auto-schedule EBR, Slack VP Sales + CSM notification. |

### Governance Thresholds

| Parameter | Value | Description |
|-----------|-------|-------------|
| `DISCOUNT_GOVERNANCE_THRESHOLD` | **30.0%** | Discount requests exceeding this trigger Deal Desk escalation. |
| `MINIMUM_ARR_THRESHOLD` | **$50,000** | Opportunities below this ARR route to nurture enrichment. |
| `CHURN_GROWTH_THRESHOLD` | **-30.0%** | Week-over-week usage decline below this flags churn risk. |
| `CHURN_LICENSE_THRESHOLD` | **25.0%** | License utilization below this flags critical underutilization. |

### Exception Flag Definitions

| Flag | Trigger | Severity |
|------|---------|----------|
| `SEVERE_TELEMETRY_USAGE_DROP` | `weekly_usage_growth_pct < -30%` on high-value account | CRITICAL |
| `CRITICAL_LICENSE_UNDERUTILIZATION` | `license_utilization_pct < 25%` on high-value account | CRITICAL |
| `EXCESSIVE_DISCOUNT_THRESHOLD_BREACH` | `discount_requested_pct > 30%` | HIGH |
| `MISSING_EXEC_SPONSORSHIP` | No exec sponsor at `PROPOSAL_NEGOTIATION` or `CLOSED_WON` | HIGH |
| `BELOW_MINIMUM_ARR_THRESHOLD` | `annual_recurring_revenue_usd < $50,000` | MEDIUM |

---

## Quick Start

### Prerequisites

Ensure you have installed the dependencies from the root `requirements.txt`:

```bash
cd /workspaces/fde-mastery
pip install -r requirements.txt
```

### 1. Run Benchmark Evaluation Harness

Execute the golden dataset suite using the deterministic rule engine (no API key required):

```bash
cd month-6-revops
python eval_harness.py
```

### 2. Run Live RevOps Automation Demo

Simulate health scoring, automation workflows, and immutable ledger creation:

```bash
python main.py
```

---

## Benchmark Evaluation Results

The evaluation harness evaluates system accuracy against the `golden_dataset.json` test suite using the deterministic rule engine.

### Evaluation Summary

- **Engine Evaluated**: `deterministic-fallback`
- **Total Test Cases**: `4`
- **Pass Rate**: `100.0%`
- **Total Execution Time**: `<0.01s`

### Test Suite Execution Detail

| Case ID | Account | ARR (USD) | Lead Source | Expected Action | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `REV-2026-R01` | `Acme Fintech Global` | $120,000 | `PRODUCT_QUALIFIED_PQL` | `AUTO_ASSIGN_ENTERPRISE_AE` | ✅ **PASSED** |
| `REV-2026-R02` | `Omni Health Systems` | $280,000 | `INBOUND_DEMO` | `ESCALATE_DEAL_DESK` | ✅ **PASSED** |
| `REV-2026-R03` | `Titan Logistics Software` | $450,000 | `OUTBOUND_EXEC_OUTREACH` | `FLAG_CHURN_RISK` | ✅ **PASSED** |
| `REV-2026-R04` | `Startup Tech Labs` | $15,000 | `ORGANIC_SEARCH` | `TRIGGER_ENRICHMENT_NURTURE` | ✅ **PASSED** |

---

## Project Structure

```
month-6-revops/
├── README.md                 # Systems design & RevOps architecture
├── schemas.py                # Opportunity, Telemetry, Workflow, Audit Pydantic models
├── agent.py                  # Deterministic RevOps evaluation engine
├── eval_harness.py           # Benchmark runner for opportunity risk tests
├── golden_dataset.json       # Synthetic CRM opportunity test cases
└── main.py                   # Live opportunity processing & automation demo
```

### Schema Highlights

- **Telemetry-Driven Scoring**: `TelemetryMetrics` captures MAU, week-over-week growth, and license utilization for data-driven health scoring.
- **Pipeline Stage Awareness**: `DealStage` enum ensures governance rules apply correctly at each funnel stage (e.g., exec sponsor required at `PROPOSAL_NEGOTIATION`).
- **Multi-System Automation**: `AutomationStep` targets specific systems (`SALESFORCE_CRM`, `SLACK`, `CALENDLY`, `HUBSPOT_MARKETING`, `CLEARBIT`, `DOCUSIGN_CLM`, `CUSTOMER_SUCCESS`) with explicit `is_automated` flags.
- **Immutable Audit**: `RevOpsAuditRecord` hashes the opportunity ID + account name for traceability and stores health scores, flags, and workflow step counts.

---

## Agent Design Highlights

- **Deterministic Rule Engine**: Zero-LLM dependency for core RevOps evaluation. Every opportunity is scored against explicit telemetry, discount, sponsorship, and ARR thresholds with guaranteed output consistency.
- **Hierarchical Risk Logic**: CRITICAL (churn on high-value accounts) → HIGH (deal governance violations) → MEDIUM (below ARR minimum) → LOW (healthy enterprise PQL).
- **System-Aware Automation**: Each action maps to a concrete multi-step workflow targeting real enterprise systems (Salesforce, Slack, Calendly, HubSpot, Clearbit, DocuSign CLM).
- **Resilient Fallback**: Built-in deterministic engine guarantees execution and testing continuity even when running offline or without API keys.

---

## CLI Reference

### `eval_harness.py`

| Flag | Description | Default |
|------|-------------|---------|
| *(none)* | Runs benchmark against `golden_dataset.json` | — |

### `main.py`

Run without arguments to process the full golden dataset through the live execution pipeline:

```bash
python main.py
```

---

## Integration Notes

### Adding New Governance Rules

To extend the deterministic engine with new RevOps rules, edit `_evaluate_deterministic` in `agent.py`:

```python
# Example: Add a competitive displacement flag
if payload.metadata.get("competitive_deal") == "true" and payload.discount_requested_pct > 20.0:
    flags.append("COMPETITIVE_DISCOUNT_ESCALATION")
    return RevOpsEvaluationResult(
        opportunity_id=payload.opportunity_id,
        health_score=75.0,
        risk_tier=RiskTier.HIGH,
        recommended_action=RevOpsAction.ESCALATE_DEAL_DESK,
        exception_flags=flags,
        reasoning_trace="Competitive deal with elevated discount requires Deal Desk approval.",
        automation_workflow=[
            AutomationStep(
                step_number=1,
                system_target="SALESFORCE_CRM",
                action_description="Route to competitive deal desk queue.",
                is_automated=True,
            ),
        ],
    )
```

### Connecting to Live CRM Systems

The `OpportunityPayload` schema accepts arbitrary metadata via the `metadata: Dict[str, str]` field. Map your CRM webhooks:

```python
from schemas import OpportunityPayload, TelemetryMetrics, LeadSource, DealStage

opp = OpportunityPayload(
    opportunity_id="OPP-99999",
    account_name="Acme Corp",
    annual_recurring_revenue_usd=250000.00,
    lead_source=LeadSource.INBOUND_DEMO,
    deal_stage=DealStage.PROPOSAL_NEGOTIATION,
    discount_requested_pct=15.0,
    has_exec_sponsor=True,
    telemetry=TelemetryMetrics(
        monthly_active_users=320,
        weekly_usage_growth_pct=12.5,
        license_utilization_pct=78.0,
    ),
)
```

---

## License & Attribution

Part of the **FDE Mastery** curriculum — a 6-month production engineering roadmap for deterministic, schema-guaranteed LLM agents across Cybersecurity, Finance, HealthTech, Logistics, Legal, and RevOps.

- Month 1: `v1.0-soc-triage` — SOC SIEM Triage Agent (100% Pass)
- Month 2: `v1.1-finance-risk-engine` — Financial Transaction Risk & Governance (100% Pass)
- Month 3: `v1.2-healthtech-hipaa-engine` — HIPAA-Compliant Clinical Triage (100% Pass)
- Month 4: `v1.3-logistics-supply-chain` — Autonomous Freight & Supply Chain Risk (100% Pass)
- Month 5: `v1.4-legal-contract-risk` — Legal Tech & Contract Risk Analysis (100% Pass)
- Month 6: `v1.5-revops-enterprise-automation` — RevOps & Enterprise Automation Engine (100% Pass)
