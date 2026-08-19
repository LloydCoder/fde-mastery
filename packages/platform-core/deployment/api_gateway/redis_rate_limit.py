"""Redis-backed rate limiter for horizontally scaled deployments."""

import os
import time
import uuid

from fastapi import HTTPException, Request


class RedisRateLimiter:
    def __init__(self, url: str | None = None):
        try:
            import redis
        except ImportError as exc:
            raise RuntimeError("Install redis to use Redis rate limiting") from exc
        redis_url = url or os.getenv("FDE_REDIS_URL")
        if not redis_url:
            raise ValueError("FDE_REDIS_URL is required for Redis rate limiting")
        self.client = redis.Redis.from_url(redis_url, decode_responses=True)
        self.window = int(os.getenv("FDE_RATE_LIMIT_WINDOW_SECONDS", "60"))
        self.limit = int(os.getenv("FDE_RATE_LIMIT_REQUESTS", "60"))
        self.max_body_bytes = int(os.getenv("FDE_MAX_BODY_BYTES", str(256 * 1024)))
        if self.window <= 0 or self.limit <= 0 or self.max_body_bytes <= 0:
            raise ValueError("Rate-limit settings must be positive")

    def enforce(self, request: Request, client_id: str) -> None:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_bytes:
                    raise HTTPException(status_code=413, detail="Request body too large.")
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid Content-Length header.") from exc

        now = time.time()
        bucket = f"fde:ratelimit:{client_id}:{int(now) // self.window}"
        with self.client.pipeline() as pipe:
            pipe.incr(bucket)
            pipe.expire(bucket, self.window + 1)
            count, _ = pipe.execute()
        if count > self.limit:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded.",
                headers={"Retry-After": str(self.window)},
            )
