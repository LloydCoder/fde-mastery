"""Enterprise sales simulation — walkthrough of zero-delay client journey."""

from datetime import datetime, timedelta


def simulate_sales_call():
    print("=" * 75)
    print("  FDE MASTERY — LIVE CLIENT SIMULATION")
    print("  Prospect: Fortune 500 Retailer | Use Case: SOC Triage")
    print("=" * 75)

    # Step 1: Discovery (5 min)
    print("\n🎯 DISCOVERY (Monday 9:00 AM)")
    print("   Prospect: 'We process 50K alerts/day. Our MTTR is 4 hours.'")
    print("   You:      'Our pre-built SOC Triage Agent reduces MTTR to <2 min.")
    print("             Let me show you with YOUR data right now.'")

    # Step 2: Live Onboarding (10 min)
    print("\n⚡ ONBOARDING (Monday 9:05 AM)")
    print("   • Upload: prospect_uploads/siem_sample_500.json")
    print("   • Auto-map: 12 fields → RawSecurityLog schema (3 min)")
    print("   • Generate: 50-case golden dataset from their event types")
    print("   • Eval run: 94% pass rate → PRODUCTION READY")

    # Step 3: Live Demo (10 min)
    print("\n🚀 PRODUCTION DEPLOYMENT (Monday 9:15 AM)")
    print("   • API endpoint: https://fde.ai/api/retailer-corp/cyber/triage")
    print("   • Slack bot: #security-alerts channel connected")
    print("   • First live alert triaged: LOG-2026-RET-001 → CRITICAL → AUTO_CONTAIN")

    # Step 4: Value Proof (Week 2)
    print("\n📊 VALUE REVIEW (Friday Week 2)")
    print("   • 12,400 alerts processed")
    print("   • 11,832 auto-contained correctly (95.4%)")
    print("   • 568 escalated → 541 approved by analysts (95.2% acceptance)")
    print("   • Estimated analyst hours saved: 340 hrs/week")
    print("   • Contract value: $18K/mo (started Day 1)")

    print("\n" + "=" * 75)
    print("  TOTAL TIME: Deal closed Monday 9am → Value proven Friday Week 2")
    print("  CUSTOM BUILD TIME: 0 days. Pre-built agent + config only.")
    print("=" * 75)


def simulate_multi_domain_expansion():
    print("\n" + "=" * 75)
    print("  MULTI-DOMAIN EXPANSION SIMULATION")
    print("  Client: Global Financial Services Firm")
    print("=" * 75)

    print("\n📅 MONTH 1: Cybersecurity")
    print("   Deploy: SOC Triage Agent | Pass Rate: 100% | MTTR: 4hr → 90sec")

    print("\n📅 MONTH 2: Finance")
    print("   Deploy: Transaction Fraud Agent | Pass Rate: 100% | False Positives: -40%")

    print("\n📅 MONTH 3: Legal")
    print("   Deploy: Contract Risk Agent | Pass Rate: 100% | Review Time: 8hr → 15min")

    print("\n📅 MONTH 4: RevOps")
    print("   Deploy: Pipeline Automation | Churn Flag Accuracy: 94% | AE Capacity: +30%")

    print("\n💰 CUMULATIVE CONTRACT VALUE: $50K/mo (Enterprise Tier)")
    print("   Cross-domain context sharing: Risk signals from Finance → Cybersecurity")
    print("   Unified audit ledger: 4 domains, 1 compliance report")
    print("=" * 75)


if __name__ == "__main__":
    simulate_sales_call()
    simulate_multi_domain_expansion()