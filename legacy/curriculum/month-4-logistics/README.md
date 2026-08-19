# Month 4: Supply Chain & Logistics Engine

An enterprise-grade autonomous freight and supply chain risk evaluator. This system ingests real-time IoT telemetry, carrier status feeds, and trade compliance data to evaluate shipment risk, generate mitigation plans, and maintain immutable chain-of-custody audit records.

---

## Architecture Overview

```
                  +-----------------------------+
                  |  Incoming Shipment Manifest |
                  |  (BOL, Carrier Webhook, IoT)|
                  +--------------+--------------+
                                 |
                                 v
                  +-----------------------------+
                  |   Telemetry & Compliance    |
                  |   Ingestion & Validation    |
                  +--------------+--------------+
                                 |
            +--------------------+--------------------+
            |                                         |
            v                                         v
+-------------------------+               +-------------------------+
| Sanctions / HS Code     |               | Cold-Chain / Port Delay |
| Compliance Check        |               | Telemetry Analysis      |
+-------------------------+               +-------------------------+
            |                                         |
            v                                         v
+-------------------------+               +-------------------------+
| Risk Scoring Engine     |               | Mitigation Plan Builder |
| (0-100, Tiered)         |               | (Autonomous + HITL)   |
+------------+------------+               +------------+------------+
             |                                         |
             v                                         v
+--------------------+----------------------------------+
|                                                     |
|              Execution Orchestrator                 |
|          - Route Optimization                     |
|          - Cold Storage Reroute                   |
|          - Customs Quarantine Hold                |
+--------------------+--------------------------------+
                     |
                     v
            +-----------------------------+
            |   Chain-of-Custody Ledger     |
            |   (Immutable Audit Record)    |
            +-----------------------------+
```

### Key Components

1. **Data Schemas (`schemas.py`)** — Pydantic models for shipment payloads, telemetry, risk evaluation results, mitigation steps, and chain-of-custody audit records.
2. **Logistics Agent (`agent.py`)** — Dual-engine risk evaluator combining trade compliance screening (sanctions, HS codes), cold-chain excursion detection, and port congestion analysis.
3. **Evaluation Harness (`eval_harness.py`)** — Automated benchmark runner testing risk tier classification, action selection, and exception flag detection against labeled ground truth.
4. **Pipeline Orchestrator (`main.py`)** — End-to-end demonstration of shipment ingestion → risk evaluation → mitigation planning → audit logging.
5. **Golden Dataset (`golden_dataset.json`)** — Pre-validated logistics cases covering routine freight, port delays, cold-chain breaches, and sanctioned trade compliance holds.

---

## Risk Scoring & Mitigation Policy

| Risk Score | Tier | Action | Triggers |
| :--- | :--- | :--- | :--- |
| **0 – 29** | `LOW` | `PROCEED_NORMAL` | Normal telemetry, no compliance flags, on-schedule transit |
| **30 – 69** | `MEDIUM` | `OPTIMIZE_ROUTE` | Port congestion, berth delays, SLA breach risk |
| **70 – 89** | `HIGH` | `ESCALATE_CUSTOMS_DESK` | Customs holds, documentation discrepancies |
| **90 – 100** | `CRITICAL` | `REROUTE_COLD_STORAGE` / `HOLD_AND_QUARANTINE` | Cold-chain excursion, sanctions embargo, invalid HS code |

### Hard Compliance Triggers

- **Sanctioned Destinations**: `IR`, `KP`, `SY`, `CU` → immediate `HOLD_AND_QUARANTINE`
- **Invalid HS Codes**: `9999.99`, `0000.00` → `INVALID_HS_TARIFF_CODE` flag
- **Cold-Chain Excursion**: Temperature outside declared range → `REROUTE_COLD_STORAGE`
- **Port Congestion**: Keywords "delay", "anchored", "berth", "congestion" in carrier notes → `OPTIMIZE_ROUTE`

---

## Quick Start

### Prerequisites

```bash
cd /workspaces/fde-mastery
pip install -r requirements.txt
```

### 1. Run Evaluation Harness

```bash
cd month-4-logistics
python eval_harness.py
```

Expected output:
```
============================================================
 EVALUATION SUMMARY [LOGISTICS & SUPPLY CHAIN]
============================================================
 Total Cases: 4
 Passed:      4
 Failed:      0
 Pass Rate:   100.0%
============================================================
```

### 2. Run Live Pipeline Demo

```bash
python main.py
```

Demonstrates end-to-end: shipment ingestion → telemetry analysis → risk scoring → mitigation → audit logging.

---

## Benchmark Results

| Case ID | Description | Risk Tier | Action | Flags | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `LOG-2026-L01` | Routine dry-goods air freight | LOW | `PROCEED_NORMAL` | — | ✅ |
| `LOG-2026-L02` | Port congestion SLA breach | MEDIUM | `OPTIMIZE_ROUTE` | PORT_CONGESTION_DELAY, SLA_BREACH_RISK | ✅ |
| `LOG-2026-L03` | Cold-chain pharma breach | CRITICAL | `REROUTE_COLD_STORAGE` | COLD_CHAIN_EXCURSION, SPOILAGE_IMMORTAL_RISK | ✅ |
| `LOG-2026-L04` | Sanctioned destination / invalid HS | CRITICAL | `HOLD_AND_QUARANTINE` | SANCTIONS_EMBARGO_FLAG, INVALID_HS_TARIFF_CODE | ✅ |

**Pass Rate**: `100.0%` (4/4)

---

## Project Structure

```
month-4-logistics/
├── __init__.py
├── README.md                 # Architecture & compliance documentation
├── schemas.py                # Pydantic models (Shipment, Telemetry, Risk, Audit)
├── agent.py                  # LogisticsAgent: compliance + telemetry evaluator
├── eval_harness.py           # Golden dataset benchmark runner
├── golden_dataset.json       # 4 labeled logistics test cases
└── main.py                   # Live pipeline demonstration
```

---

## Integration Notes

### Adding New Sanctioned Destinations

Edit `agent.py`:

```python
SANCTIONED_DESTINATIONS = {"IR", "KP", "SY", "CU", "NEW_COUNTRY"}
```

### Connecting to IoT Telemetry Streams

Map sensor webhooks to `TelemetryData`:

```python
from schemas import TelemetryData, ShipmentPayload

telemetry = TelemetryData(
    temperature_c=sensor_payload["temp"],
    humidity_percent=sensor_payload["humidity"],
    shock_g_force=sensor_payload["shock_max"],
    location_coords=f"{sensor_payload['lat']}, {sensor_payload['lon']}"
)
```

### Extending Exception Flags

Add new detection logic in `_evaluate_deterministic`:

```python
if payload.telemetry.shock_g_force > 5.0:
    flags.append("HIGH_IMPACT_DAMAGE")
```

---

## Compliance & Audit

- **Export Control**: Automated sanctions screening against OFAC / BIS restricted party lists
- **Customs Compliance**: HS tariff code validation with invalid-code detection
- **Chain-of-Custody**: SHA-256 hashed shipment identifiers with immutable ledger entries
- **FDA 21 CFR Part 11**: Timestamped, tamper-evident audit logs for regulated cold-chain environments

---

## License & Attribution

Part of the **FDE Mastery** curriculum:

- Month 1: `v1.0-soc-triage` — SOC SIEM Triage Agent (100% Pass)
- Month 2: `v1.1-finance-risk-engine` — Financial Transaction Risk & Governance (100% Pass)
- Month 3: `v1.2-healthtech-hipaa-engine` — HealthTech Data Engineering & HIPAA Compliance (100% Pass)
- Month 4: `v1.3-logistics-supply-chain` — Supply Chain Telemetry & Compliance Engine (100% Pass)
