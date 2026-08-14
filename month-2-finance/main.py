"""
month-2-finance/main.py
-----------------------
Live Financial Transaction Processing, Execution Order Generation,
and Audit Logging Demo.
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import List

from agent import FinancialRiskAgent
from schemas import (
    FinancialTransaction,
    RiskAssessmentReport,
    ExecutionOrder,
    MitigationStep,
    AuditLedgerEntry,
    FinancialAction,
    ExecutionStatus,
    RiskLevel
)

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
logger = logging.getLogger("FinanceMain")


def build_mitigation_plan(report: RiskAssessmentReport) -> List[MitigationStep]:
    """Dynamically generates mitigation and execution steps based on risk assessment."""
    action = report.recommended_action
    steps = []

    if action == FinancialAction.APPROVE:
        steps.append(
            MitigationStep(
                step_number=1,
                action_item="Execute settlement and credit destination account.",
                requires_human_approval=False,
                assigned_role="SYSTEM"
            )
        )
    elif action == FinancialAction.MONITOR:
        steps.append(
            MitigationStep(
                step_number=1,
                action_item="Execute transaction under active monitoring flag.",
                requires_human_approval=False,
                assigned_role="SYSTEM"
            )
        )
        steps.append(
            MitigationStep(
                step_number=2,
                action_item="Enqueue account ID for 24-hour liquidity and velocity audit.",
                requires_human_approval=False,
                assigned_role="RISK_ENGINE"
            )
        )
    elif action == FinancialAction.FLAG_FOR_REVIEW:
        steps.append(
            MitigationStep(
                step_number=1,
                action_item="Place transaction in temporary 24-hour compliance escrow.",
                requires_human_approval=False,
                assigned_role="SYSTEM"
            )
        )
        steps.append(
            MitigationStep(
                step_number=2,
                action_item="Dispatch review ticket with reasoning trace to Compliance Desk.",
                requires_human_approval=True,
                assigned_role="COMPLIANCE_OFFICER"
            )
        )
        steps.append(
            MitigationStep(
                step_number=3,
                action_item="Request Beneficial Ownership Verification (KYC/UBO) from counterparty.",
                requires_human_approval=True,
                assigned_role="COMPLIANCE_OFFICER"
            )
        )
    elif action in [FinancialAction.AUTO_REJECT, FinancialAction.FREEZE_ACCOUNT]:
        steps.append(
            MitigationStep(
                step_number=1,
                action_item="Immediately reject transaction and cancel downstream settlement.",
                requires_human_approval=False,
                assigned_role="SYSTEM"
            )
        )
        steps.append(
            MitigationStep(
                step_number=2,
                action_item="Place temporary lock on account outbound transfers.",
                requires_human_approval=True,
                assigned_role="MLRO_OFFICER"
            )
        )
        steps.append(
            MitigationStep(
                step_number=3,
                action_item="Generate auto-drafted Suspicious Activity Report (SAR) for regulatory filing.",
                requires_human_approval=True,
                assigned_role="COMPLIANCE_LEAD"
            )
        )

    return steps


def process_transaction(
    tx: FinancialTransaction,
    agent: FinancialRiskAgent
) -> tuple[ExecutionOrder, AuditLedgerEntry]:
    """Processes a single financial transaction through risk assessment, order routing, and audit logging."""
    # 1. Run Agent Risk Assessment
    report: RiskAssessmentReport = agent.evaluate_transaction(tx)

    # 2. Derive Execution Order Status
    if report.recommended_action in [FinancialAction.APPROVE, FinancialAction.MONITOR]:
        order_status = ExecutionStatus.EXECUTED
    elif report.recommended_action == FinancialAction.FLAG_FOR_REVIEW:
        order_status = ExecutionStatus.HELD_FOR_APPROVAL
    else:
        order_status = ExecutionStatus.REJECTED

    # 3. Build Order
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    execution_order = ExecutionOrder(
        order_id=order_id,
        transaction_id=tx.transaction_id,
        action=report.recommended_action,
        status=order_status,
        mitigation_plan=build_mitigation_plan(report),
        approved_by="SYSTEM_AUTO" if not any(s.requires_human_approval for s in build_mitigation_plan(report)) else None
    )

    # 4. Create Immutable Audit Ledger Record
    ledger_entry = AuditLedgerEntry(
        log_id=f"LEDGER-{uuid.uuid4().hex[:8].upper()}",
        transaction_id=tx.transaction_id,
        account_id=tx.account_id,
        event_type=f"TRANSACTION_EVALUATED_{report.recommended_action.value}",
        payload={
            "risk_score": str(report.risk_score),
            "risk_level": report.risk_level.value,
            "amount_usd": str(tx.amount),
            "order_id": order_id,
            "status": order_status.value
        }
    )

    return execution_order, ledger_entry


def run_live_demo():
    """Runs a live demonstration using samples from golden dataset or inline payloads."""
    print("\n" + "=" * 70)
    print(" 🚀 MONTH 2: LIVE FINANCIAL TRANSACTION & RISK PROCESSING DEMO")
    print("=" * 70 + "\n")

    # Load test cases from golden dataset
    dataset_path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
    if os.path.exists(dataset_path):
        with open(dataset_path, "r") as f:
            transactions_data = json.load(f)
    else:
        logger.error(f"Golden dataset not found at {dataset_path}")
        return

    # Use mock/heuristic fallback if no Anthropic key present
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  No ANTHROPIC_API_KEY detected in environment. Running with deterministic fallback engine.\n")

    agent = FinancialRiskAgent(api_key=api_key)

    for case in transactions_data:
        tx = FinancialTransaction(**case)
        
        print(f"------------ TRANSACTION: {tx.transaction_id} ------------")
        print(f"Type: {tx.transaction_type.value:<16} Amount: ${tx.amount:,.2f} {tx.currency}")
        print(f"Route: {tx.source_country} ➔ {tx.destination_country:<12} Account: {tx.account_id}")

        order, ledger = process_transaction(tx, agent)

        print("\n📋 EXECUTION ORDER & MITIGATION PLAN:")
        print(f"   Order ID: {order.order_id} | Status: {order.status.value} | Action: {order.action.value}")
        for step in order.mitigation_plan:
            human_flag = "[HUMAN APPROVAL REQUIRED]" if step.requires_human_approval else "[AUTONOMOUS]"
            print(f"   └─ Step {step.step_number}: {step.action_item} {human_flag}")

        print("\n🔒 IMMUTABLE AUDIT LEDGER ENTRY:")
        print(f"   Log ID: {ledger.log_id} | Event: {ledger.event_type}")
        print(f"   Payload: {json.dumps(ledger.payload)}")
        print("-" * 70 + "\n")


if __name__ == "__main__":
    run_live_demo()