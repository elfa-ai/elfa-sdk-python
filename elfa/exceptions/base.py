"""
Exception hierarchy for the Elfa SDK
"""

import json
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Optional

import httpx


class ElfaAPIError(Exception):
    """Base exception for all Elfa SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Any] = None,
        request_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        self.request_id = request_id

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.request_id:
            parts.append(f"Request ID: {self.request_id}")
        return " | ".join(parts)


class ElfaAuthenticationError(ElfaAPIError):
    """Raised when the API key is invalid or missing (HTTP 401)."""

    def __init__(
        self, message: str = "Authentication failed", request_id: Optional[str] = None
    ):
        super().__init__(message, status_code=401, request_id=request_id)


class ElfaRateLimitError(ElfaAPIError):
    """Raised when the API rate limit is exceeded (HTTP 429)."""

    def __init__(
        self,
        message: str = "API rate limit exceeded",
        retry_after: Optional[int] = None,
        reset_time: Optional[datetime] = None,
        response_data: Optional[Any] = None,
        request_id: Optional[str] = None,
    ):
        super().__init__(
            message, status_code=429, response_data=response_data, request_id=request_id
        )
        self.retry_after = retry_after
        self.reset_time = reset_time


class ElfaNotFoundError(ElfaAPIError):
    """Raised when a requested resource is not found (HTTP 404)."""

    def __init__(
        self, message: str = "Resource not found", request_id: Optional[str] = None
    ):
        super().__init__(message, status_code=404, request_id=request_id)


class ElfaValidationError(ElfaAPIError):
    """Raised for invalid request parameters, client-side or server-side (HTTP 400)."""

    def __init__(
        self,
        message: str,
        validation_errors: Optional[Any] = None,
        status_code: Optional[int] = None,
        request_id: Optional[str] = None,
    ):
        super().__init__(message, status_code=status_code, request_id=request_id)
        self.validation_errors = validation_errors


class ElfaNetworkError(ElfaAPIError):
    """Raised when a network/connection issue occurs."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ElfaTimeoutError(ElfaAPIError):
    """Raised when a request times out."""

    def __init__(self, message: str = "Request timed out"):
        super().__init__(message)


def is_retryable_error(error: Exception) -> bool:
    """Retry rate limits, network/timeout errors, and 5xx server responses."""
    if isinstance(error, (ElfaRateLimitError, ElfaNetworkError, ElfaTimeoutError)):
        return True
    if isinstance(error, ElfaAPIError) and error.status_code is not None:
        return 500 <= error.status_code < 600
    return False


def _extract_message(data: Any) -> Optional[str]:
    if isinstance(data, str):
        return data or None
    if isinstance(data, dict):
        candidate = data.get("message") or data.get("error") or data.get("detail")
        if isinstance(candidate, str):
            return candidate
        if isinstance(candidate, dict):
            inner = candidate.get("message")
            return inner if isinstance(inner, str) else json.dumps(candidate)
    return None


def compute_rate_limit_reset(
    get_header: Callable[[str], Optional[str]],
) -> Optional[datetime]:
    """Derive a reset time from ``x-ratelimit-reset`` (epoch) or ``retry-after``."""
    reset = get_header("x-ratelimit-reset")
    if reset:
        try:
            return datetime.fromtimestamp(int(reset), tz=timezone.utc)
        except ValueError:
            pass

    retry_after = get_header("retry-after")
    if retry_after:
        trimmed = retry_after.strip()
        if trimmed.isdigit():
            return datetime.now(tz=timezone.utc) + timedelta(seconds=int(trimmed))
        try:
            return parsedate_to_datetime(trimmed)
        except (TypeError, ValueError):
            return None

    return None


def raise_for_response(response: httpx.Response) -> None:
    """Map a non-2xx httpx response to the matching Elfa exception."""
    try:
        data: Any = response.json()
    except Exception:
        data = response.text

    message = _extract_message(data) or f"HTTP {response.status_code}"
    request_id = response.headers.get("x-request-id")
    status = response.status_code

    if status == 401:
        raise ElfaAuthenticationError(message, request_id=request_id)
    if status == 404:
        raise ElfaNotFoundError(message, request_id=request_id)
    if status == 429:
        retry_after = response.headers.get("retry-after")
        raise ElfaRateLimitError(
            message,
            retry_after=(
                int(retry_after) if retry_after and retry_after.isdigit() else None
            ),
            reset_time=compute_rate_limit_reset(response.headers.get),
            response_data=data,
            request_id=request_id,
        )
    if status == 400:
        errors = data.get("errors") if isinstance(data, dict) else None
        raise ElfaValidationError(
            message, validation_errors=errors, status_code=400, request_id=request_id
        )

    raise ElfaAPIError(
        message, status_code=status, response_data=data, request_id=request_id
    )


# Backwards-compatible alias.
handle_http_error = raise_for_response
