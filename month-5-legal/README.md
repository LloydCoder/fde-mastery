# Month 5: Legal Tech & Contract Risk Analysis Engine

An enterprise-grade legal contract clause risk analyzer and redline engine. This system ingests structured commercial contracts (MSAs, SOWs, DPAs), evaluates toxic clauses against deterministic compliance rules, generates actionable redlines, and maintains an immutable legal audit ledger.

---

## Architecture Overview

```
                  +-----------------------------+
                  | Incoming Contract Payload   |
                  |  (MSA, SOW, DPA, NDA, etc.) |
                  +--------------+--------------+
                                 |
                                 v
                  +-----------------------------+
                  |   Legal Clause Analyzer     |
                  |  (Claude Sonnet / Rule Base)|
                  +--------------+--------------+
                                 |
            +--------------------+--------------------+
            |                                         |
            v                                         v
+-------------------------+               +-------------------------+
| Structured Evaluation   |               | Risk Threshold Check    |
| Risk Score (0-100)      |               | Jurisdiction, Liability,  |
| Action: APPROVE/REJECT  |               | IP, GDPR, Termination     |
+------------+------------+               +------------+------------+
             |                                         |
             |                            +-------------------------+
             |                            | Proposed Redlines       |
             |                            | - Liability Cap Rewrite |
             |                            | - IP Retention Clause   |
             |                            | - GDPR SCC Insertion    |
             |                            +------------+------------+
             |                                         |
             v                                         v
+--------------------+----------------------------------+
|                                                     |
|              Execution Orchestrator                 |
|          - Counsel Approval Routing                 |
|          - Automated Contract Archiving               |
+--------------------+--------------------------------+
                     |
                     v
            +-----------------------------+
            |   Immutable Legal Ledger    |
|   (SHA-16 Contract Hash, Risk Score)    |
            +-----------------------------+
```

### Key Components

1. **Contract Models & Schemas (`schemas.py`)** — Pydantic models enforcing strict schema validation on contract payloads, clause redlines, risk evaluations, and legal audit records.
2. **Clause Risk Analyzer (`agent.py`)** — Deterministic rule engine evaluating liability caps, IP assignment traps, indemnification exposure, GDPR compliance, and termination clauses.
3. **Evaluation Harness (`eval_harness.py`)** — Automated benchmark runner executing golden dataset test cases against the rule engine.
4. **Live Demo (`main.py`)** — End-to-end driver processing contracts, generating redlines, routing mitigation steps, and writing immutable audit records.
5. **Golden Dataset (`golden_dataset.json`)** — Pre-validated benchmark edge cases testing standard SaaS terms, offshore jurisdiction exposure, IP expropriation, and GDPR violations.

---

## Risk Scoring & Mitigation Policy

Contracts are assigned a continuous risk score between **0.0** and **100.0** along with a discrete classification:

| Risk Score Range | Classification | Action | Handling / Mitigation Plan |
| :--- | :--- | :--- | :--- |
| **0.0 – 29.9** | `LOW` | `APPROVE_STANDARD` | **Autonomous**: Automated execution and archivism. |
| **30.0 – 59.9** | `MEDIUM` | *(reserved)* | **Hybrid**: Monitor with standard counsel review queue. |
| **60.0 – 89.9** | `HIGH` | `AMEND_CLAUSE` | **Hybrid**: Generate redlines, propose standard terms, automated workflow. |
| **90.0 – 100.0** | `CRITICAL` | `ESCALATE_LEGAL_COUNSEL` / `REJECT_CONTRACT` | **Counsel Required**: General Counsel redline review or formal rejection. |

### Exception Flag Definitions

| Flag | Trigger | Severity |
|------|---------|----------|
| `NON_STANDARD_JURISDICTION` | Governing law outside {Delaware, New York, California, UK, EU} | HIGH |
| `UNLIMITED_LIABILITY_EXPOSURE` | Uncapped or unlimited indemnification / liability clause | HIGH |
| `BACKGROUND_IP_EXPROPRIATION_RISK` | Pre-existing / background IP assignment to counterparty | CRITICAL |
| `UNILATERAL_UNLIMITED_INDEMNITY` | One-sided indemnity without limitation or mutuality | CRITICAL |
| `UNILATERAL_IMMEDIATE_TERMINATION` | Termination without cause, notice, or cure period | CRITICAL |
| `GDPR_DATA_TRANSFER_VIOLATION` | EU data transfer without SCCs or adequate safeguards | CRITICAL |

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
cd month-5-legal
python eval_harness.py
```

### 2. Run Live Contract Risk Analysis Demo

Simulate redline generation, mitigation workflows, and immutable ledger creation:

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

| Case ID | Contract Type | Jurisdiction | ACV (USD) | Expected Action | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `LEG-2026-C01` | `Master Services Agreement` | `Delaware, USA` | $150,000 | `APPROVE_STANDARD` | ✅ **PASSED** |
| `LEG-2026-C02` | `Statement of Work` | `Cayman Islands` | $450,000 | `AMEND_CLAUSE` | ✅ **PASSED** |
| `LEG-2026-C03` | `Software Development Agreement` | `New York, USA` | $750,000 | `ESCALATE_LEGAL_COUNSEL` | ✅ **PASSED** |
| `LEG-2026-C04` | `Data Processing Addendum` | `Unknown` | $220,000 | `REJECT_CONTRACT` | ✅ **PASSED** |

---

## Project Structure

```
month-5-legal/
├── README.md                 # Systems design & legal risk architecture
├── schemas.py                # Contract, Clause, Redline, Audit Pydantic models
├── agent.py                  # Deterministic legal clause risk analyzer
├── eval_harness.py           # Benchmark runner for contract risk tests
├── golden_dataset.json       # Synthetic contract clause test cases
└── main.py                   # Live contract processing & redline demo
```

### Schema Highlights

- **Clause Taxonomy**: Strict `ClauseType` enum (`LIABILITY_CAP`, `INDEMNIFICATION`, `IP_ASSIGNMENT`, `TERMINATION`, `DATA_PRIVACY_GDPR`, `GOVERNING_LAW`) ensures consistent categorization across all contract types.
- **Redline Generation**: `ClauseRedline` captures original text, proposed replacement, and risk reasoning for every flagged clause.
- **Counsel Approval Routing**: `LegalMitigationStep` explicitly tags whether a step requires `counsel_approval` or can run via `[AUTOMATED WORKFLOW]`.
- **Immutable Audit**: `LegalAuditRecord` hashes the contract ID + counterparty for traceability and stores risk scores, flags, and redline counts.

---

## Agent Design Highlights

- **Deterministic Rule Engine**: Zero-LLM dependency for core risk evaluation. Every clause is matched against explicit keyword and pattern rules with guaranteed output consistency.
- **Decision Matrix**: Hierarchical severity logic — `REJECT_CONTRACT` (GDPR + termination), `ESCALATE_LEGAL_COUNSEL` (IP + indemnity), `AMEND_CLAUSE` (liability + jurisdiction), `APPROVE_STANDARD` (clean terms).
- **Redline Automation**: Automatically drafts proposed contract language for every flagged clause, ready for direct insertion into counterparty negotiations.
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

### Adding New Clause Risk Rules

To extend the deterministic engine with new compliance rules, edit `_evaluate_deterministic` in `agent.py`:

```python
# Example: Add a non-compete clause blocker
if clause.clause_type.value == "TERMINATION":
    if "non-compete" in text_lower and "employee" in text_lower:
        flags.append("EMPLOYEE_NON_COMPETE_RISK")
        redlines.append(
            ClauseRedline(
                clause_id=clause.clause_id,
                original_text=clause.text,
                proposed_redline="Post-employment restrictions limited to 6 months and senior executive roles only.",
                risk_reasoning="Broad non-compete may be unenforceable under state labor law."
            )
        )
```

### Connecting to Contract Lifecycle Management (CLM) Systems

The `ContractPayload` schema accepts arbitrary metadata. Map your CLM webhooks:

```python
from schemas import ContractPayload, ContractClause, ClauseType

contract = ContractPayload(
    contract_id="CTR-99999",
    title="Master Services Agreement",
    counterparty="Acme Corp",
    governing_jurisdiction="Delaware, USA",
    annual_contract_value_usd=500000.00,
    clauses=[
        ContractClause(
            clause_id="SEC-8.1",
            clause_type=ClauseType.LIABILITY_CAP,
            section_title="Limitation of Liability",
            text="..."
        )
    ]
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
