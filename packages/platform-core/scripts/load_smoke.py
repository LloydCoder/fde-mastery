"""Small deterministic load smoke for staging, not a production load generator."""
from __future__ import annotations

import argparse
import statistics
import time

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/health")
    parser.add_argument("--requests", type=int, default=50)
    args = parser.parse_args()
    if args.requests < 1 or args.requests > 10_000:
        raise SystemExit("requests must be between 1 and 10000")
    latencies = []
    failures = 0
    # CI runners may expose HTTP(S)_PROXY variables. The smoke target is a
    # loopback service, so bypass ambient proxy configuration for deterministic
    # local verification and to avoid false failures from proxy interception.
    with httpx.Client(timeout=5, trust_env=False) as client:
        for _ in range(args.requests):
            started = time.perf_counter()
            try:
                response = client.get(args.url)
                response.raise_for_status()
            except Exception:
                failures += 1
            finally:
                latencies.append((time.perf_counter() - started) * 1000)
    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    print({"requests": args.requests, "failures": failures, "failure_rate": failures / args.requests, "p95_ms": round(p95, 2)})
    if failures / args.requests > 0.01:
        raise SystemExit("load smoke failure rate exceeded 1%")


if __name__ == "__main__":
    main()
