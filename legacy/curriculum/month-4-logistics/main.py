"""
Main Execution Script for Month 4: Supply Chain Telemetry & Compliance Demo
Demonstrates end-to-end shipment evaluation, mitigation planning, and audit logging.
"""

import json
import os

try:
    from agent import LogisticsAgent
    from schemas import ShipmentPayload
except ImportError:
    from .agent import LogisticsAgent
    from .schemas import ShipmentPayload


def run_demo():
    print("\n" + "=" * 70)
    print(" 🚀 MONTH 4: LIVE SUPPLY CHAIN TELEMETRY & COMPLIANCE DEMO")
    print("=" * 70)

    dataset_path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
    if not os.path.exists(dataset_path):
        dataset_path = "golden_dataset.json"

    with open(dataset_path, "r") as f:
        cases = json.load(f)

    agent = LogisticsAgent()

    for case in cases:
        payload = ShipmentPayload(**case["payload"])
        print(f"\n------------ SHIPMENT: {payload.shipment_id} ------------")
        print(f"Mode: {payload.transport_mode.value:<18} Carrier: {payload.carrier}")
        print(f"Route: {payload.origin_country} ➔ {payload.destination_country:<12} Value: ${payload.goods_value_usd:,.2f} USD")
        print(f"HS Code: {payload.hs_code:<15} Telemetry Temp: {payload.telemetry.temperature_c}°C (Target: {payload.declared_temp_range_c})")

        result = agent.evaluate(payload)
        audit_record = agent.create_audit_record(payload, result)

        print("\n📋 MITIGATION PLAN:")
        print(f"   Action: {result.recommended_action.value} | Risk Score: {result.risk_score} [{result.risk_tier.value}]")
        for step in result.mitigation_plan:
            approval_str = "[HUMAN APPROVAL REQUIRED]" if step.requires_human_approval else "[AUTONOMOUS]"
            print(f"   └─ Step {step.step_number}: {step.description} {approval_str}")

        print("\n🔒 CHAIN-OF-CUSTODY IMMUTABLE AUDIT LEDGER:")
        print(f"   Log ID: {audit_record.log_id} | Event: {audit_record.event_type}")
        print(f"   Payload: {json.dumps(audit_record.payload_summary)}")
        print("-" * 70)

    print("\n======================================================================")
    print(" PIPELINE EXECUTION COMPLETE: TELEMETRY & COMPLIANCE AUDITED")
    print("======================================================================\n")


if __name__ == "__main__":
    run_demo()