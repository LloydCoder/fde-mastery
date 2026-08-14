"""FDE Mastery Platform CLI — unified command-line interface."""

import argparse
import json
import sys
from pathlib import Path

from client_onboarding.onboard_cli import onboard_client
from demo.enterprise_sales_simulation import simulate_sales_call, simulate_multi_domain_expansion
from eval_harness import PlatformEvalHarness


def cmd_onboard(args):
    result = onboard_client(
        client_id=args.client_id,
        client_name=args.client_name,
        domains=[d.strip() for d in args.domains.split(",")],
        sample_data_dir=args.sample_dir,
        api_tier=args.tier,
    )
    print(json.dumps(result.model_dump(), indent=2))


def cmd_eval(args):
    harness = PlatformEvalHarness()
    result = harness.run()
    sys.exit(0 if result["failed"] == 0 else 1)


def cmd_simulate(args):
    if args.scenario == "sales":
        simulate_sales_call()
    elif args.scenario == "expansion":
        simulate_multi_domain_expansion()
    else:
        simulate_sales_call()
        simulate_multi_domain_expansion()


def main():
    parser = argparse.ArgumentParser(description="FDE Mastery Platform CLI v7.0")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # onboard
    onboard_parser = subparsers.add_parser("onboard", help="Onboard a new client")
    onboard_parser.add_argument("--client-id", required=True)
    onboard_parser.add_argument("--client-name", required=True)
    onboard_parser.add_argument("--domains", required=True, help="Comma-separated domains")
    onboard_parser.add_argument("--sample-dir", required=True)
    onboard_parser.add_argument("--tier", default="growth", choices=["starter", "growth", "enterprise"])
    onboard_parser.set_defaults(func=cmd_onboard)

    # eval
    eval_parser = subparsers.add_parser("eval", help="Run platform evaluation harness")
    eval_parser.set_defaults(func=cmd_eval)

    # simulate
    sim_parser = subparsers.add_parser("simulate", help="Run sales simulation")
    sim_parser.add_argument("--scenario", choices=["sales", "expansion", "all"], default="all")
    sim_parser.set_defaults(func=cmd_simulate)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()