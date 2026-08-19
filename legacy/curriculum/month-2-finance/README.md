# Month 2: Financial Transaction Agent & Risk Governance Engine

An enterprise-grade, deterministic-backed financial transaction risk evaluator and mitigation orchestrator. This system ingests incoming transactional payloads, evaluates cross-border and velocity risk vectors using multi-tier LLM inference with deterministic fallbacks, generates structured execution orders, and writes immutable audit logs.

---

## Architecture Overview

```
                  +-----------------------------+
                  | Incoming Financial Request  |
                  |  (Card, Wire, Crypto Swap)  |
                  +--------------+--------------+
                                 |
                                 v
                  +-----------------------------+
                  |   Inference Engine Router   |
                  | (Claude Sonnet / Rule Base) |
                  +--------------+--------------+
                                 |
            +--------------------+--------------------+
            |                                         |
            v                                         v
+-------------------------+               +-------------------------+
| Structured Evaluation   |               | High-Risk Threshold?    |
| Risk Score (0-100)      |               | Route Check (US -> RU)  |
| Action: APPROVE/REJECT  |               +------------+------------+
+------------+------------+                            |
             |                                         v
             |                            +-------------------------+
             |                            | Mitigation Plan         |
             |                            | - Immediate Settlement  |
             |                            | - Account Lock Trigger|
             |                            | - Auto-Drafted SAR Log|
             |                            +------------+------------+
             |                                         |
             v                                         v
+--------------------+----------------------------------+
|                                                     |
|              Execution Orchestrator                 |
|          - Generates Execution Order                |
|          - Dispatches Action Steps                  |
+--------------------+--------------------------------+
                     |
                     v
            +-----------------------------+
            |   Immutable Audit Ledger    |
            |   (JSON Hash Ledger Entry)  |
            +-----------------------------+
```

### Key Components

1. **Transaction Models & Schemas (`schemas.py`)** — Pydantic models enforcing strict schema validation on incoming transactions, risk outputs, execution orders, and audit ledger entries.
2. **Evaluation Harness (`eval_harness.py`)** — Automated test runner executing golden dataset benchmarks against live Anthropic APIs or deterministic rule fallback engines.
3. **Execution Engine (`main.py`)** — End-to-end driver processing transactions, evaluating mitigations, creating execution steps, and maintaining immutable audit trail states.
4. **Golden Dataset (`golden_dataset.json`)** — Pre-validated benchmark edge cases testing domestic card purchases, international wire transfers, and sanctioned cross-border crypto swaps.

---

## Risk Scoring & Mitigation Policy

Transactions are assigned a continuous risk score between **0.0** and **100.0** along with a discrete classification:

| Risk Score Range | Classification | Action | Handling / Mitigation Plan |
| :--- | :--- | :--- | :--- |
| **0.0 – 29.9** | `LOW` | `APPROVE` | **Autonomous**: Immediate clearing and automated ledger settlement. |
| **30.0 – 59.9** | `MEDIUM` | `MONITOR` | **Hybrid**: Execute under active monitoring flag + enqueue 24h velocity audit. |
| **60.0 – 89.9** | `HIGH` | `FLAG_FOR_REVIEW` | **Hybrid**: Hold funds in escrow + trigger secondary human analyst review queue. |
| **90.0 – 100.0** | `CRITICAL` | `AUTO_REJECT` | **Autonomous Block / Human Review**: Immediate settlement cancellation + temporary account lock + automated SAR drafting. |

### Rule Overrides & Sanctions Hard-Stop

- **Sanctioned Destinations**: Any transaction directed toward sanctioned or high-risk geographic jurisdictions (e.g., `RU`, `IR`, `KP`) triggers an immediate minimum risk score of **95.0+** and forces an `AUTO_REJECT` order regardless of transaction type.
- **Large Amount Crypto Swaps**: Non-custodial cross-border crypto swaps exceeding **$100,000 USD** automatically escalate to `CRITICAL` risk due to velocity and regulatory anti-money laundering (AML) controls.

---

## Quick Start

### Prerequisites

Ensure you have installed the dependencies from the root `requirements.txt`:

```bash
cd /workspaces/fde-mastery
pip install -r requirements.txt
```

### 1. Run Benchmark Evaluation Harness

Execute the golden dataset suite using the deterministic fallback engine (no API key required):

```bash
cd month-2-finance
python eval_harness.py --mock
```

Or evaluate against the live Anthropic API:

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
python eval_harness.py --model claude-sonnet-4-6
```

### 2. Run Live Transaction Processing Demo

Simulate execution orders, mitigation plans, and immutable ledger creation:

```bash
python main.py
```

---

## Benchmark Evaluation Results

The evaluation harness evaluates system accuracy against the `golden_dataset.json` test suite using `claude-sonnet-4-6` or the deterministic rule engine.

### Evaluation Summary

- **Model Evaluated**: `claude-sonnet-4-6` *(Fallback: Deterministic Rule Engine)*
- **Total Test Cases**: `4`
- **Pass Rate**: `100.0%`
- **Total Execution Time**: `0.02s` (Mock / Fallback)

### Test Suite Execution Detail

| Case ID | Transaction Type | Route | Amount (USD) | Expected Action | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TXN-2026-F01` | `CARD_PURCHASE` | `US ➔ US` | $142.50 | `APPROVE` | ✅ **PASSED** |
| `TXN-2026-F02` | `WIRE_TRANSFER` | `US ➔ US` | $9,500.00 | `FLAG_FOR_REVIEW` | ✅ **PASSED** |
| `TXN-2026-F03` | `WIRE_TRANSFER` | `US ➔ KY` | $490,000.00 | `FLAG_FOR_REVIEW` | ✅ **PASSED** |
| `TXN-2026-F04` | `CRYPTO_SWAP` | `US ➔ RU` | $250,000.00 | `AUTO_REJECT` | ✅ **PASSED** |

### Fuzzy Evaluation Mode

For policy threshold testing where near-match actions are acceptable (e.g., `AUTO_REJECT` vs `FREEZE_ACCOUNT` for CRITICAL risk), run:

```bash
python eval_harness.py --mock --fuzzy
```

---

## Project Structure

```
month-2-finance/
├── README.md                 # Systems design & risk model architecture
├── schemas.py                # Transaction, Ledger & Order Pydantic models
├── agent.py                  # Financial decision & risk scoring agent
├── eval_harness.py           # Benchmark runner for transaction/risk tests
├── golden_dataset.json       # Synthetic transaction & trade execution dataset
└── main.py                   # Live execution & order routing demo
```

### Schema Highlights

- **Strict Financial Constraints**: Enforces positive floating amounts (`gt=0`), risk scoring bounded between `0.0` and `100.0`, and explicit 3-letter currency / 2-letter country codes.
- **Deterministic Action Mapping**: Clear `FinancialAction` enums (`APPROVE`, `MONITOR`, `FLAG_FOR_REVIEW`, `AUTO_REJECT`, `FREEZE_ACCOUNT`) mirror production compliance setups.
- **Autonomous vs. Human Governance**: `MitigationStep` explicitly tags whether an operational step requires human approval (`requires_human_approval=True` for account freezes or SAR filings) or can run autonomously (`SYSTEM`).
- **Audit Readiness**: `AuditLedgerEntry` provides structured payloads for immutable record-keeping.

---

## Agent Design Highlights

- **Claude Sonnet 4.6 Native**: Directly leverages `claude-sonnet-4-6` with zero temperature for deterministic, audit-compliant compliance outputs.
- **Deterministic Schema Validation**: Automatically parses JSON outputs into strongly typed `RiskAssessmentReport` and `RiskRuleTrigger` Pydantic models.
- **Resilient Fallback Engine**: Built-in `_heuristic_fallback` guarantees system execution and testing continuity even when running offline or without API keys.

---

## CLI Reference

### `eval_harness.py`

| Flag | Description | Default |
|------|-------------|---------|
| `--dataset` | Path to golden dataset JSON | `golden_dataset.json` |
| `--model` | Model ID to evaluate | `claude-sonnet-4-6` |
| `--mock` | Run in mock/fallback mode without live API calls | `False` |
| `--fuzzy` | Enable fuzzy evaluation mode for policy thresholds | `False` |

### `main.py`

Run without arguments to process the full golden dataset through the live execution pipeline:

```bash
python main.py
```

---

## Integration Notes

### Adding New Risk Rules

To extend the deterministic fallback engine with new compliance rules, edit `_heuristic_fallback` in `agent.py`:

```python
# Example: Add a new merchant category block
if transaction.metadata.get("merchant_category") == "MIXER_SERVICE":
    rules.append(RiskRuleTrigger(
        rule_id="CRYPTO_MIXER_DETECTED",
        rule_name="Cryptocurrency Mixer Service",
        severity=RiskLevel.CRITICAL,
        description="Destination merchant is a known cryptocurrency mixer."
    ))
    score = max(score, 95.0)
```

### Connecting to Live Payment Processors

The `FinancialTransaction` schema accepts arbitrary metadata via the `metadata: Dict[str, str]` field. Map your processor webhooks:

```python
from schemas import FinancialTransaction

txn = FinancialTransaction(
    transaction_id="TXN-12345",
    account_id="ACC-001",
    counterparty_id="CP-MERCHANT-XYZ",
    transaction_type=TransactionType.CARD_PURCHASE,
    amount=250.00,
    source_country="US",
    destination_country="US",
    metadata={
        "ip_address": "203.0.113.45",
        "device_hash": "abc123",
        "merchant_category": "5411_GROCERY_STORES",
        "transactions_in_last_hour": "3"
    }
)
```

---

## License & Attribution

Part of the **FDE Mastery** curriculum — a 6-month production engineering roadmap for deterministic, schema-guaranteed LLM agents across Cybersecurity, Finance, HealthTech, Logistics, Legal, and RevOps.

- Month 1: `v1.0-soc-triage` — SOC SIEM Triage Agent (100% Pass)
- Month 2: `v1.1-finance-risk-engine` — Financial Transaction Risk & Governance
