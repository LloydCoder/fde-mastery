"""Select the API rate limiter from environment configuration."""

import os

from deployment.api_gateway.rate_limit import enforce_request_limits


def build_rate_limiter():
    backend = os.getenv("FDE_RATE_LIMIT_BACKEND", "memory").strip().lower()
    if backend == "memory":
        return enforce_request_limits
    if backend == "redis":
        from deployment.api_gateway.redis_rate_limit import RedisRateLimiter

        limiter = RedisRateLimiter()
        return limiter.enforce
    raise ValueError("FDE_RATE_LIMIT_BACKEND must be 'memory' or 'redis'")
