"""Entry point for SOC Triage Agent."""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

from schemas import RawSecurityLog
from agent import SOCTriageAgent
from eval_harness import EvaluationHarness

PROJECT_ROOT = Path(__file__).resolve().parent.parent
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:10}</level> | <cyan>{message}</cyan>",
    level="INFO",
)


def run_live_demo(agent: SOCTriageAgent):
    logger.info("=== RUNNING LIVE SIEM LOG TRIAGE DEMO ===")

    incoming_log = RawSecurityLog(
        log_id="LOG-2026-X88",
        timestamp=datetime.now(),
        source_ip="10.12.80.44",
        destination_ip="45.33.32.156",
        user_id="svc_database_backup",
        event_type="UNUSUAL_OUTBOUND_DATABASE_DUMP",
        payload_summary=(
            "Service account 'svc_database_backup' executed pg_dump on core customer DB "
            "and established an unencrypted HTTP connection to 45.33.32.156 transferring 4.8 GB."
        ),
    )

    logger.info(f"Incoming Event: {incoming_log.event_type} from {incoming_log.source_ip}")
    report = agent.triage_log(incoming_log)

    print("\n" + "=" * 60)
    print(f"  THREAT TRIAGE REPORT: {report.log_id}")
    print("=" * 60)
    print(f"Severity:           {report.severity.value}")
    print(f"Category:           {report.category.value}")
    print(f"Action:             {report.recommended_action.value}")
    print(f"Confidence Score:   {report.confidence_score * 100:.1f}%")
    print(f"Summary:            {report.summary}")
    print("\nMitigation Plan:")
    for step in report.mitigation_plan:
        flag = "[HUMAN APPROVAL REQUIRED]" if step.requires_human_approval else "[AUTONOMOUS]"
        print(f"  Step {step.step_number}: {step.action} {flag}")
    print("\nReasoning Trace:")
    print(f"  {report.reasoning_trace}")
    print("=" * 60 + "\n")


def run_evaluations(provider: str, model: str | None, fuzzy: bool = False):
    logger.info("=== RUNNING GOLDEN DATASET BENCHMARK ===")
    dataset_file = "golden_dataset.json"

    if not os.path.exists(dataset_file):
        logger.error(f"Dataset not found: {dataset_file}")
        return

    harness = EvaluationHarness(dataset_file, provider=provider, model=model, fuzzy=fuzzy)
    summary = harness.run_evaluation()

    print("\n" + "=" * 60)
    print(f"  EVALUATION SUMMARY [{provider.upper()}]" + (" [FUZZY MODE]" if fuzzy else ""))
    print("=" * 60)
    print(f"Total:   {summary['total_tests']}")
    print(f"Passed:  {summary['passed']}")
    print(f"Failed:  {summary['failed']}")
    print(f"Rate:    {summary['pass_rate_percentage']}%")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="SOC Triage Agent CLI")
    parser.add_argument("--provider", choices=["openai", "anthropic"], default=os.getenv("LLM_PROVIDER", "openai"))
    parser.add_argument("--model", type=str, default=None, help="Model ID")
    parser.add_argument("--mock", action="store_true", help="Offline synthetic responses")
    parser.add_argument("--eval-only", action="store_true")
    parser.add_argument("--demo-only", action="store_true")
    parser.add_argument("--list-models", action="store_true", help="Print Anthropic model IDs")
    parser.add_argument(
        "--fuzzy",
        action="store_true",
        help="Allow near-match actions in evaluation (e.g., ESCALATE_TO_SOC ≈ AUTO_CONTAIN for exfil)",
    )
    args = parser.parse_args()

    if args.list_models:
        SOCTriageAgent.list_anthropic_models()
        return 0

    if args.mock:
        os.environ["MOCK_LLM"] = "true"
        logger.warning("🧪 MOCK MODE: Using synthetic LLM responses")

    provider = args.provider.lower()

    if not args.mock:
        if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY missing. Set it in .env or export it.")
            sys.exit(1)
        elif provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
            logger.error("ANTHROPIC_API_KEY missing. Set it in .env or export it.")
            sys.exit(1)

    try:
        agent = SOCTriageAgent(provider=provider, model=args.model)
    except ValueError as e:
        logger.error(str(e))
        print("\n📋 Quick fixes:")
        print("  1. Add real API keys to /workspaces/fde-mastery/.env")
        print("  2. Or test offline:  python main.py --mock")
        print("  3. Or list models:   python main.py --list-models")
        print("  4. Claude 3.x is RETIRED. Use Claude 4.x:")
        print("     python main.py --provider anthropic --model claude-sonnet-4-6")
        sys.exit(1)

    logger.info(f"Initializing SOC Triage Agent | Provider: {provider.upper()} | Model: {agent.model}")

    if not args.eval_only:
        run_live_demo(agent)

    if not args.demo_only:
        run_evaluations(provider=provider, model=args.model, fuzzy=args.fuzzy)


if __name__ == "__main__":
    main()