"""Error mapping, retry classification, and rate-limit reset parsing."""

from datetime import datetime, timezone

import httpx
import pytest

from elfa.exceptions.base import (
    ElfaAPIError,
    ElfaAuthenticationError,
    ElfaNetworkError,
    ElfaNotFoundError,
    ElfaRateLimitError,
    ElfaValidationError,
    compute_rate_limit_reset,
    is_retryable_error,
    raise_for_response,
)


def _response(status, json=None, headers=None):
    return httpx.Response(status, json=json or {}, headers=headers or {})


def test_maps_401():
    with pytest.raises(ElfaAuthenticationError):
        raise_for_response(_response(401, {"message": "nope"}))


def test_maps_404():
    with pytest.raises(ElfaNotFoundError):
        raise_for_response(_response(404))


def test_maps_400_with_validation_errors():
    with pytest.raises(ElfaValidationError) as exc:
        raise_for_response(_response(400, {"message": "bad", "errors": {"x": "y"}}))
    assert exc.value.validation_errors == {"x": "y"}


def test_maps_429_with_retry_after():
    with pytest.raises(ElfaRateLimitError) as exc:
        raise_for_response(_response(429, {"message": "slow"}, {"retry-after": "30"}))
    assert exc.value.retry_after == 30
    assert exc.value.reset_time is not None


def test_maps_5xx():
    with pytest.raises(ElfaAPIError) as exc:
        raise_for_response(_response(503, {"message": "down"}))
    assert exc.value.status_code == 503


def test_is_retryable_error():
    assert is_retryable_error(ElfaRateLimitError())
    assert is_retryable_error(ElfaNetworkError("x"))
    assert is_retryable_error(ElfaAPIError("x", status_code=502))
    assert not is_retryable_error(ElfaAPIError("x", status_code=400))
    assert not is_retryable_error(ElfaAuthenticationError())


def test_rate_limit_reset_from_epoch():
    reset = compute_rate_limit_reset(
        lambda name: "1700000000" if name == "x-ratelimit-reset" else None
    )
    assert reset == datetime.fromtimestamp(1700000000, tz=timezone.utc)
