import pytest

from fde_platform.api import IdempotencyKey, Page, ProblemDetails, RequestMetadata


def test_idempotency_key_accepts_visible_ascii() -> None:
    key = IdempotencyKey("01JAPI-unique_123")
    assert key.value.endswith("123")


def test_idempotency_key_rejects_whitespace_and_oversize() -> None:
    with pytest.raises(ValueError):
        IdempotencyKey("bad key")
    with pytest.raises(ValueError):
        IdempotencyKey("x" * 256)


def test_request_metadata_requires_uuid_request_id() -> None:
    with pytest.raises(ValueError):
        RequestMetadata("not-a-uuid")
    metadata = RequestMetadata("00000000-0000-0000-0000-000000000001")
    assert metadata.idempotency_key is None


def test_problem_details_is_http_error_only() -> None:
    problem = ProblemDetails(status=409, code="idempotency_conflict", request_id="req-1")
    assert problem.status == 409
    assert problem.retryable is False
    with pytest.raises(ValueError):
        ProblemDetails(status=200)


def test_page_limit_is_bounded() -> None:
    assert Page((1, 2), 2, "next").next_cursor == "next"
    with pytest.raises(ValueError):
        Page((), 101)
