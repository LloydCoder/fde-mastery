"""Live RevOps & Enterprise Automation Demo."""

import json
import sys
from pathlib import Path

try:
    from .agent import RevOpsAgent
    from .schemas import OpportunityPayload
except ImportError:
    from agent import RevOpsAgent
    from schemas import OpportunityPayload


def run_demo(dataset_path: str = "golden_dataset.json"):
    print("\n" + "=" * 75)
    print(" 🚀 MONTH 6: LIVE REVOPS & ENTERPRISE AUTOMATION DEMO")
    print("=" * 75)

    path = Path(dataset_path)
    if not path.exists():
        print(f"Dataset not found: {dataset_path}")
        sys.exit(1)

    with open(path, "r") as f:
        cases = json.load(f)

    agent = RevOpsAgent()

    for case in cases:
        payload = OpportunityPayload(**case["payload"])
        print(f"\n------------ OPPORTUNITY: {payload.opportunity_id} ({payload.account_name}) ------------")
        print(f"ARR: ${payload.annual_recurring_revenue_usd:,.2f} USD   Stage: {payload.deal_stage.value}")
        print(f"Lead Source: {payload.lead_source.value:<25} Exec Sponsor: {'Yes' if payload.has_exec_sponsor else 'No'}")
        print(f"Discount Requested: {payload.discount_requested_pct}%")
        print(f"Telemetry — MAU: {payload.telemetry.monthly_active_users}  Growth: {payload.telemetry.weekly_usage_growth_pct}%  Utilization: {payload.telemetry.license_utilization_pct}%")

        result = agent.evaluate(payload)
        audit_record = agent.create_audit_record(payload, result)

        print("\n📋 REVOPS EVALUATION & HEALTH SCORE:")
        print(f"   Health Score: {result.health_score}/100   Risk Tier: {result.risk_tier.value}")
        print(f"   Action: {result.recommended_action.value}")
        print(f"   Reasoning: {result.reasoning_trace}")
        print(f"   Exception Flags: {result.exception_flags}")

        print("\n⚙️ AUTOMATION WORKFLOW:")
        for step in result.automation_workflow:
            auto_str = "[AUTOMATED]" if step.is_automated else "[MANUAL]"
            print(f"   \u2514\u2500 Step {step.step_number}: [{step.system_target}] {step.action_description} {auto_str}")

        print("\n🔒 REVOPS AUDIT LEDGER:")
        print(f"   Log ID: {audit_record.log_id} | Event: {audit_record.event_type}")
        print(f"   Summary: {json.dumps(audit_record.summary)}")
        print("-" * 75)

    print("\n===========================================================================")
    print(" PIPELINE EXECUTION COMPLETE: REVOPS AUTOMATION & AUDIT COMPLETE")
    print("===========================================================================\n")


if __name__ == "__main__":
    run_demo()