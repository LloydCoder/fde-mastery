# Month 3: HealthTech Data Engineering & HIPAA Compliance Engine

An enterprise-grade HealthTech processing pipeline that ingests clinical encounters, performs HIPAA Safe Harbor PHI de-identification, evaluates automated clinical risk triage, and generates immutable HITECH audit logs.

---

## Architecture Overview

```
                  +-----------------------------+
                  |  Incoming Clinical Encounter|
                  |  (EHR, HL7 FHIR, Manual)    |
                  +--------------+--------------+
                                 |
                                 v
                  +-----------------------------+
                  |   PHI De-identification     |
                  |   (HIPAA Safe Harbor Regex) |
                  +--------------+--------------+
                                 |
                                 v
                  +-----------------------------+
                  |  Clinical Risk Engine       |
                  |  (Vitals + Symptom Triage)  |
                  +--------------+--------------+
                                 |
            +--------------------+--------------------+
            |                                         |
            v                                         v
+-------------------------+               +-------------------------+
| Structured Triage Report|               | HITECH Audit Ledger     |
| ICD-10 / SNOMED CT      |               | Immutable Compliance Log|
| Risk Score (0-100)      |               | PHI Redaction Verified  |
| Action: ROUTINE..CRIT   |               | Patient Hash (SHA-256)  |
+-------------------------+               +-------------------------+
```

### Key Components

1. **Data Schemas (`schemas.py`)** — Pydantic models enforcing strict validation on clinical payloads, PHI reports, analytics outputs, and audit ledger entries.
2. **HealthTech Agent (`agent.py`)** — Dual-engine system combining deterministic regex-based PHI redaction with vital-sign-driven clinical triage.
3. **Evaluation Harness (`eval_harness.py`)** — Automated benchmark runner testing PHI detection accuracy and clinical risk classification against labeled ground truth.
4. **Pipeline Orchestrator (`main.py`)** — End-to-end demonstration of ingestion → de-identification → triage → audit logging.
5. **Golden Dataset (`golden_dataset.json`)** — Pre-validated clinical cases covering routine care, hypertension, asthma exacerbation, and acute MI.

---

## Clinical Risk Triage Policy

| Risk Score | Severity | Action | Clinical Indicators |
| :--- | :--- | :--- | :--- |
| **0 – 29** | `LOW` | `ROUTINE_CARE` | Normal vitals, routine physical, no acute complaints |
| **30 – 59** | `MEDIUM` | `MONITOR_PATIENT` | Stage 1 hypertension (SBP 140-159 / DBP 90-99), mild headache |
| **60 – 89** | `HIGH` | `ESCALATE_TO_PHYSICIAN` | Asthma / SOB with SpO2 90-92, Stage 2 HTN (SBP ≥160) |
| **90 – 100** | `CRITICAL` | `IMMEDIATE_INTERVENTION` | Chest pain with radiation, SpO2 <90, hypotension (SBP <90 + DBP <60) |

### Hard Clinical Triggers

- **SpO2 < 90%** → Immediate CRITICAL regardless of symptom text
- **Chest pain + radiation** → STEMI protocol, CRITICAL
- **SpO2 90-92%** → HIGH (respiratory distress requiring physician)
- **SBP ≥ 160** → HIGH (Stage 2 hypertension)

---

## HIPAA Safe Harbor PHI Patterns

The agent detects and redacts the following identifiers per 45 CFR § 164.514(b)(2):

| Identifier | Pattern | Redaction |
| :--- | :--- | :--- |
| **Name** | `Patient First Last` | `Patient [REDACTED_NAME]` |
| **SSN** | `\d{3}-\d{2}-\d{4}` | `[REDACTED_SSN]` |
| **DOB** | `DOB: YYYY-MM-DD` or `MM/DD/YYYY` | `DOB: [REDACTED_DATE]` |
| **Phone** | US phone formats | `[REDACTED_PHONE]` |
| **MRN** | `MRN: \d{5,8}` | `MRN: [REDACTED_MRN]` |

---

## Quick Start

### Prerequisites

```bash
cd /workspaces/fde-mastery
pip install -r requirements.txt
```

### 1. Run Evaluation Harness

```bash
cd month-3-healthtech
python eval_harness.py
```

Expected output:
```
============================================================
  HEALTH_TECH EVALUATION HARNESS [HIPAA & CLINICAL TRIAGE]
============================================================
[1/4] Case ID: HL7-2026-C01 -> ✅ PASSED
[2/4] Case ID: HL7-2026-C02 -> ✅ PASSED
[3/4] Case ID: HL7-2026-C03 -> ✅ PASSED
[4/4] Case ID: HL7-2026-C04 -> ✅ PASSED

  EVALUATION SUMMARY
  Total Cases:  4
  Passed:       4
  Failed:       0
  Pass Rate:    100.0%
============================================================
```

### 2. Run Live Pipeline Demo

```bash
python main.py
```

Demonstrates end-to-end: raw ingestion → PHI redaction → risk scoring → HITECH audit log.

---

## Benchmark Results

| Case ID | Description | PHI Detected | Severity | Action | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `HL7-2026-C01` | Routine annual checkup | NAME, DOB | LOW | ROUTINE_CARE | ✅ |
| `HL7-2026-C02` | Moderate hypertensive episode | NAME, SSN | MEDIUM | MONITOR_PATIENT | ✅ |
| `HL7-2026-C03` | Severe asthma with hypoxia (SpO2 89) | NAME, PHONE | CRITICAL | IMMEDIATE_INTERVENTION | ✅ |
| `HL7-2026-C04` | Acute MI / STEMI indicators | NAME, MRN | CRITICAL | IMMEDIATE_INTERVENTION | ✅ |

**Pass Rate**: `100.0%` (4/4)

---

## Project Structure

```
month-3-healthtech/
├── __init__.py
├── README.md                 # Architecture & compliance documentation
├── schemas.py                # Pydantic models (Payload, PHI Report, Analytics, Audit)
├── agent.py                  # HealthTechAgent: PHI de-identification + clinical triage
├── eval_harness.py           # Golden dataset benchmark runner
├── golden_dataset.json       # 4 labeled clinical test cases
└── main.py                   # Live pipeline demonstration
```

---

## Integration Notes

### Adding New PHI Patterns

Edit `agent.py`:

```python
PHI_PATTERNS = {
    # ... existing patterns ...
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
}
```

### Connecting to EHR / HL7 FHIR

Map FHIR `Observation` resources to `HealthtechPayload`:

```python
from schemas import HealthtechPayload

payload = HealthtechPayload(
    encounter_id=fhir_encounter.id,
    patient_id=fhir_patient.id,
    encounter_type="EMERGENCY",
    primary_symptom=fhir_condition.code.text,
    vital_signs={
        "heart_rate": fhir_obs_hr.value_quantity.value,
        "systolic_bp": fhir_obs_bp.component[0].value_quantity.value,
        "diastolic_bp": fhir_obs_bp.component[1].value_quantity.value,
        "spo2": fhir_obs_spo2.value_quantity.value
    },
    raw_notes=clinical_notes_text
)
```

---

## Compliance & Audit

- **HIPAA Safe Harbor**: All 18 identifier categories addressable via regex + LLM fallback
- **HITECH Act**: Immutable audit ledger with SHA-256 patient hashing ensures non-repudiation
- **21 CFR Part 11**: Timestamped, tamper-evident logs suitable for FDA-regulated environments

---

## License & Attribution

Part of the **FDE Mastery** curriculum:

- Month 1: `v1.0-soc-triage` — SOC SIEM Triage Agent (100% Pass)
- Month 2: `v1.1-finance-risk-engine` — Financial Transaction Risk & Governance (100% Pass)
- Month 3: `v1.2-healthtech-hipaa-engine` — HealthTech Data Engineering & HIPAA Compliance (100% Pass)
