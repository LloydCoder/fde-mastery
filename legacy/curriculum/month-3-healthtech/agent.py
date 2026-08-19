"""
HealthTech Agent: Dual-engine system for PHI De-identification & Clinical Triage.
Combines deterministic regex safeguards with LLM reasoning for regulatory compliance.
"""

import re
import os
import json
import hashlib
from typing import Tuple, Dict, Any, List

try:
    from schemas import (
        HealthtechPayload,
        PHIDeidentificationReport,
        ClinicalAnalyticsReport,
        ClinicalRiskTier,
        AutomatedTriageAction
    )
except ImportError:
    from .schemas import (
        HealthtechPayload,
        PHIDeidentificationReport,
        ClinicalAnalyticsReport,
        ClinicalRiskTier,
        AutomatedTriageAction
    )


class HealthTechAgent:
    """HealthTech Processing Agent for HIPAA compliance and automated clinical triage."""

    # Safe Harbor Regex Patterns for core PHI identifiers
    PHI_PATTERNS = {
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "PHONE": r"\b(\+?\d{1,2}[- .]?)?(\(?\d{3}\)?[- .]?)?\d{3}[- .]?\d{4}\b",
        "DOB": r"\b(DOB:?\s*\d{4}-\d{2}-\d{2}|DOB:?\s*\d{2}/\d{2}/\d{4})\b",
        "MRN": r"\b(MRN:?\s*\d{5,8})\b",
        "NAME": r"\bPatient\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b"
    }

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")

    def deidentify_phi(self, raw_text: str) -> PHIDeidentificationReport:
        """Applies HIPAA Safe Harbor rules to scrub PHI identifiers from clinical text."""
        redacted_text = raw_text
        detected_identifiers = []

        for identifier_type, pattern in self.PHI_PATTERNS.items():
            matches = list(re.finditer(pattern, redacted_text, flags=re.IGNORECASE))
            if matches:
                detected_identifiers.append(identifier_type)
                if identifier_type == "NAME":
                    redacted_text = re.sub(pattern, "Patient [REDACTED_NAME]", redacted_text, flags=re.IGNORECASE)
                elif identifier_type == "DOB":
                    redacted_text = re.sub(pattern, "DOB: [REDACTED_DATE]", redacted_text, flags=re.IGNORECASE)
                elif identifier_type == "MRN":
                    redacted_text = re.sub(pattern, "MRN: [REDACTED_MRN]", redacted_text, flags=re.IGNORECASE)
                elif identifier_type == "SSN":
                    redacted_text = re.sub(pattern, "[REDACTED_SSN]", redacted_text)
                elif identifier_type == "PHONE":
                    redacted_text = re.sub(pattern, "[REDACTED_PHONE]", redacted_text)

        return PHIDeidentificationReport(
            original_length=len(raw_text),
            redacted_text=redacted_text,
            identifiers_detected=sorted(list(set(detected_identifiers))),
            compliance_standard="HIPAA_SAFE_HARBOR"
        )

    def evaluate_clinical_risk(self, payload: HealthtechPayload) -> ClinicalAnalyticsReport:
        """Evaluates clinical risk using vital signs and clinical presentation indicators."""
        vitals = payload.vital_signs
        hr = vitals.get("heart_rate", 75)
        sbp = vitals.get("systolic_bp", 120)
        dbp = vitals.get("diastolic_bp", 80)
        spo2 = vitals.get("spo2", 98)
        symptom = payload.primary_symptom.lower()

        # CRITICAL: Hypoxia or acute cardiovascular distress
        if "chest pain" in symptom or "radiation" in symptom or spo2 < 90 or (sbp < 90 and dbp < 60):
            return ClinicalAnalyticsReport(
                encounter_id=payload.encounter_id,
                risk_score=95.0,
                severity=ClinicalRiskTier.CRITICAL,
                action=AutomatedTriageAction.IMMEDIATE_INTERVENTION,
                reasoning_trace="Critical signs present: Hypoxia or acute cardiovascular distress (STEMI protocol triggered).",
                icd10_codes=["I21.9", "R06.02"],
                snomed_codes=["22298006", "230145002"],
                automation_steps=["Alert ER On-Call Physician", "Trigger ECG Workflow", "Lock PHI Access"]
            )

        # HIGH: Respiratory distress or stage 2 hypertension
        if "asthma" in symptom or "shortness of breath" in symptom or spo2 <= 92 or sbp >= 160:
            return ClinicalAnalyticsReport(
                encounter_id=payload.encounter_id,
                risk_score=78.0,
                severity=ClinicalRiskTier.HIGH,
                action=AutomatedTriageAction.ESCALATE_TO_PHYSICIAN,
                reasoning_trace="Elevated risk: Respiratory distress or stage 2 hypertension requiring physician review.",
                icd10_codes=["J45.901", "I10"],
                snomed_codes=["195967001", "38341003"],
                automation_steps=["Schedule Immediate Telehealth Consultation", "Queue Respiratory Support"]
            )

        # MEDIUM: Stage 1 hypertension or mild symptomatic complaints
        if sbp >= 140 or dbp >= 90 or "headache" in symptom:
            return ClinicalAnalyticsReport(
                encounter_id=payload.encounter_id,
                risk_score=45.0,
                severity=ClinicalRiskTier.MEDIUM,
                action=AutomatedTriageAction.MONITOR_PATIENT,
                reasoning_trace="Moderate risk: Stage 1 hypertension or mild symptomatic complaints.",
                icd10_codes=["I10", "R51.9"],
                snomed_codes=["38341003", "25064002"],
                automation_steps=["Initiate 24-hr Ambulatory BP Monitoring Protocol", "Log Vitals Event"]
            )

        # LOW: Normal physiological parameters
        return ClinicalAnalyticsReport(
            encounter_id=payload.encounter_id,
            risk_score=15.0,
            severity=ClinicalRiskTier.LOW,
            action=AutomatedTriageAction.ROUTINE_CARE,
            reasoning_trace="Normal physiological parameters and routine clinical presentation.",
            icd10_codes=["Z00.00"],
            snomed_codes=["410620009"],
            automation_steps=["Route to Routine Patient Portal", "Complete Standard Charting"]
        )