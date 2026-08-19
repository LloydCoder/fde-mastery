"""Command-line entry point for platform inspection."""

from __future__ import annotations

import argparse
import json

from .manifest import manifest


def main() -> int:
    parser = argparse.ArgumentParser(prog="platformctl")
    parser.add_argument("command", choices=("manifest",), help="inspect the platform")
    args = parser.parse_args()
    if args.command == "manifest":
        print(json.dumps(manifest(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
