"""Live Legal Tech & Contract Risk Analysis Demo."""

import json
import sys
from pathlib import Path

try:
    from .agent import LegalAgent
    from .schemas import ContractPayload
except ImportError:
    from agent import LegalAgent
    from schemas import ContractPayload


def run_demo(dataset_path: str = "golden_dataset.json"):
    print("\n" + "=" * 75)
    print(" ⚖️  MONTH 5: LIVE LEGAL TECH & CONTRACT RISK ANALYSIS DEMO")
    print("=" * 75)

    path = Path(dataset_path)
    if not path.exists():
        print(f"Dataset not found: {dataset_path}")
        sys.exit(1)

    with open(path, "r") as f:
        cases = json.load(f)

    agent = LegalAgent()

    for case in cases:
        payload = ContractPayload(**case["payload"])
        print(f"\n------------ CONTRACT: {payload.contract_id} ({payload.title}) ------------")
        print(f"Counterparty: {payload.counterparty:<25} Jurisdiction: {payload.governing_jurisdiction}")
        print(f"Annual Contract Value: ${payload.annual_contract_value_usd:,.2f} USD")

        result = agent.evaluate(payload)
        audit_record = agent.create_audit_record(payload, result)

        print("\n📋 EVALUATION & RISK SUMMARY:")
        print(f"   Action: {result.recommended_action.value:<22} Risk Score: {result.overall_risk_score} [{result.risk_tier.value}]")
        print(f"   Reasoning: {result.reasoning_trace}")
        print(f"   Exception Flags: {result.exception_flags}")

        if result.proposed_redlines:
            print("\n📝 PROPOSED CONTRACT REDLINES:")
            for redline in result.proposed_redlines:
                print(f"   [Clause {redline.clause_id}] Reason: {redline.risk_reasoning}")
                print(f"   \u2514\u2500 Original: \"{redline.original_text}\"")
                print(f"   \u2514\u2500 Proposed: \"{redline.proposed_redline}\"")

        print("\n🏛️ MITIGATION & ESCALATION WORKFLOW:")
        for step in result.mitigation_plan:
            counsel_str = "[COUNSEL APPROVAL REQUIRED]" if step.requires_counsel_approval else "[AUTOMATED WORKFLOW]"
            print(f"   \u2514\u2500 Step {step.step_number}: {step.description} {counsel_str}")

        print("\n🔒 LEGAL AUDIT & COMPLIANCE LEDGER:")
        print(f"   Log ID: {audit_record.log_id} | Event: {audit_record.event_type}")
        print(f"   Summary: {json.dumps(audit_record.summary)}")
        print("-" * 75)

    print("\n===========================================================================")
    print(" PIPELINE EXECUTION COMPLETE: CONTRACT RISK & REDLINES AUDITED")
    print("===========================================================================\n")


if __name__ == "__main__":
    run_demo()