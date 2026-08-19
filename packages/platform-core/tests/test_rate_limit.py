"""Security tests for request-size and rate-limit controls."""

import os

os.environ.setdefault("FDE_RATE_LIMIT_REQUESTS", "2")
os.environ.setdefault("FDE_RATE_LIMIT_WINDOW_SECONDS", "60")

from fastapi import HTTPException
from starlette.requests import Request

from deployment.api_gateway import rate_limit


def make_request(headers=None):
    headers = headers or []
    scope = {"type": "http", "method": "POST", "path": "/api/test/finance/triage", "headers": [(k.lower().encode(), v.encode()) for k, v in headers]}
    return Request(scope)


def test_body_size_limit():
    old = rate_limit._MAX_BODY_BYTES
    rate_limit._MAX_BODY_BYTES = 10
    try:
        try:
            rate_limit.enforce_request_limits(make_request([("content-length", "11")]), "client")
        except HTTPException as exc:
            assert exc.status_code == 413
        else:
            raise AssertionError("expected body-size rejection")
    finally:
        rate_limit._MAX_BODY_BYTES = old
        rate_limit.reset_rate_limits()


def test_rate_limit_returns_429():
    old = rate_limit._MAX_REQUESTS
    rate_limit._MAX_REQUESTS = 2
    try:
        request = make_request()
        rate_limit.enforce_request_limits(request, "client")
        rate_limit.enforce_request_limits(request, "client")
        try:
            rate_limit.enforce_request_limits(request, "client")
        except HTTPException as exc:
            assert exc.status_code == 429
            assert "Retry-After" in exc.headers
        else:
            raise AssertionError("expected rate-limit rejection")
    finally:
        rate_limit._MAX_REQUESTS = old
        rate_limit.reset_rate_limits()
