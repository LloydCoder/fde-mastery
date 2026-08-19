"""Local, dependency-light interactive demonstration for customer walkthroughs."""

from __future__ import annotations

from shared_orchestrator.router import AgentRouter
from schemas import Domain


def run_demo() -> None:
    router = AgentRouter()
    try:
        router.register_defaults()
        print("FDE Mastery — six-domain live router demo")
        print("Available:", ", ".join(router.list_domains()))
        while True:
            choice = input("Domain (or 'quit'): ").strip().lower()
            if choice == "quit":
                break
            try:
                domain = Domain(choice)
                print(router.route(domain, {}))
            except (ValueError, TypeError) as exc:
                print(f"Request rejected: {exc}")
    finally:
        router.close()


if __name__ == "__main__":
    run_demo()
