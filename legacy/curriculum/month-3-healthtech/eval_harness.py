"""
Evaluation Harness for Month 3: HealthTech Data Engineering & HIPAA Pipelines
Benchmarks PHI De-identification and Clinical Triage against golden_dataset.json
"""

import json
import sys
import os

try:
    from agent import HealthTechAgent
    from schemas import HealthtechPayload
except ImportError:
    from .agent import HealthTechAgent
    from .schemas import HealthtechPayload


def run_evaluation():
    dataset_path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
    if not os.path.exists(dataset_path):
        dataset_path = "golden_dataset.json"

    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    agent = HealthTechAgent()
    total_cases = len(dataset)
    passed_cases = 0

    print("=" * 70)
    print("  HEALTH_TECH EVALUATION HARNESS [HIPAA & CLINICAL TRIAGE]")
    print("=" * 70)

    for idx, case in enumerate(dataset, 1):
        case_id = case["case_id"]
        description = case["description"]
        enc_data = case["encounter"]

        payload = HealthtechPayload(
            encounter_id=enc_data["encounter_id"],
            patient_id=enc_data["patient_id"],
            encounter_type=enc_data["encounter_type"],
            primary_symptom=enc_data["primary_symptom"],
            vital_signs=enc_data["vital_signs"],
            raw_notes=enc_data["raw_notes"]
        )

        # 1. PHI De-identification
        phi_report = agent.deidentify_phi(payload.raw_notes)
        detected_phi = phi_report.identifiers_detected
        expected_phi = case["expected_phi_categories"]
        phi_match = set(detected_phi) == set(expected_phi)

        # 2. Clinical Risk Evaluation
        risk_report = agent.evaluate_clinical_risk(payload)
        severity_match = risk_report.severity.value == case["expected_severity"]
        action_match = risk_report.action.value == case["expected_action"]

        case_passed = phi_match and severity_match and action_match

        if case_passed:
            passed_cases += 1
            status_str = "✅ PASSED"
        else:
            status_str = "❌ FAILED"

        print(f"\n[{idx}/{total_cases}] Case ID: {case_id}")
        print(f"       Description: {description}")
        print(f"       -> PHI Detected: {detected_phi} (Expected: {expected_phi}) -> {'PASS' if phi_match else 'FAIL'}")
        print(f"       -> Severity: {risk_report.severity.value} (Expected: {case['expected_severity']}) -> {'PASS' if severity_match else 'FAIL'}")
        print(f"       -> Action:   {risk_report.action.value} (Expected: {case['expected_action']}) -> {'PASS' if action_match else 'FAIL'}")
        print(f"       -> Status:   {status_str}")
        print("-" * 70)

    print("\n" + "=" * 70)
    print(f"  EVALUATION SUMMARY")
    print(f"  Total Cases:  {total_cases}")
    print(f"  Passed:       {passed_cases}")
    print(f"  Failed:       {total_cases - passed_cases}")
    print(f"  Pass Rate:    {(passed_cases / total_cases) * 100:.1f}%")
    print("=" * 70)

    if passed_cases < total_cases:
        sys.exit(1)


if __name__ == "__main__":
    run_evaluation()