"""
Base exception classes for the Elfa SDK
"""

from typing import Any, Dict, Optional

import httpx


class ElfaAPIError(Exception):
    """Base exception for all Elfa API errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        self.request_id = request_id

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.request_id:
            parts.append(f"Request ID: {self.request_id}")
        return " | ".join(parts)


class ElfaAuthenticationError(ElfaAPIError):
    """Raised when API key is invalid or missing"""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, status_code=401)


class ElfaRateLimitError(ElfaAPIError):
    """Raised when API rate limit is exceeded"""

    def __init__(
        self,
        message: str = "API rate limit exceeded",
        retry_after: Optional[int] = None,
        limit_type: Optional[str] = None,
    ):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after
        self.limit_type = limit_type


class ElfaNotFoundError(ElfaAPIError):
    """Raised when requested resource is not found"""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ElfaValidationError(ElfaAPIError):
    """Raised when request parameters are invalid"""

    def __init__(
        self, message: str, validation_errors: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=400)
        self.validation_errors = validation_errors or {}


class ElfaNetworkError(ElfaAPIError):
    """Raised when network/connection issues occur"""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ElfaTimeoutError(ElfaAPIError):
    """Raised when request times out"""

    def __init__(self, message: str = "Request timed out"):
        super().__init__(message)


def handle_http_error(response: httpx.Response) -> None:
    """
    Convert HTTP response errors to appropriate Elfa exceptions
    """
    try:
        error_data = response.json()
    except Exception:
        error_data = {}

    message = error_data.get("message", f"HTTP {response.status_code}")
    request_id = response.headers.get("x-request-id")

    if response.status_code == 401:
        raise ElfaAuthenticationError(message)
    elif response.status_code == 404:
        raise ElfaNotFoundError(message)
    elif response.status_code == 429:
        retry_after = response.headers.get("retry-after")
        retry_after_int = int(retry_after) if retry_after else None
        raise ElfaRateLimitError(
            message,
            retry_after=retry_after_int,
            limit_type=error_data.get("limit_type"),
        )
    elif response.status_code == 400:
        validation_errors = error_data.get("errors", {})
        raise ElfaValidationError(message, validation_errors)
    elif response.status_code >= 500:
        raise ElfaAPIError(
            f"Server error: {message}",
            status_code=response.status_code,
            response_data=error_data,
            request_id=request_id,
        )
    else:
        raise ElfaAPIError(
            message,
            status_code=response.status_code,
            response_data=error_data,
            request_id=request_id,
        )
