"""Redis-backed rate limiter for horizontally scaled deployments.

Optional dependency: redis>=5.0. The in-memory limiter remains the default for
local development and tests.
"""

import os
import time

from fastapi import HTTPException, Request


class RedisRateLimiter:
    def __init__(self, url: str | None = None):
        try:
            import redis
        except ImportError as exc:
            raise RuntimeError("Install redis to use Redis rate limiting") from exc
        self.client = redis.Redis.from_url(url or os.environ["FDE_REDIS_URL"], decode_responses=True)
        self.window = int(os.getenv("FDE_RATE_LIMIT_WINDOW_SECONDS", "60"))
        self.limit = int(os.getenv("FDE_RATE_LIMIT_REQUESTS", "60"))

    def enforce(self, request: Request, client_id: str) -> None:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > int(os.getenv("FDE_MAX_BODY_BYTES", str(256 * 1024))):
            raise HTTPException(status_code=413, detail="Request body too large.")
        bucket = f"fde:ratelimit:{client_id}:{int(time.time()) // self.window}"
        count = self.client.incr(bucket)
        if count == 1:
            self.client.expire(bucket, self.window)
        if count > self.limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded.", headers={"Retry-After": str(self.window)})
