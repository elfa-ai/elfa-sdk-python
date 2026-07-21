"""
Elfa SDK exception classes
"""

from elfa.exceptions.base import (
    ElfaAPIError,
    ElfaAuthenticationError,
    ElfaNetworkError,
    ElfaNotFoundError,
    ElfaRateLimitError,
    ElfaTimeoutError,
    ElfaValidationError,
    compute_rate_limit_reset,
    handle_http_error,
    is_retryable_error,
    raise_for_response,
)

__all__ = [
    "ElfaAPIError",
    "ElfaAuthenticationError",
    "ElfaRateLimitError",
    "ElfaNotFoundError",
    "ElfaValidationError",
    "ElfaNetworkError",
    "ElfaTimeoutError",
    "is_retryable_error",
    "compute_rate_limit_reset",
    "raise_for_response",
    "handle_http_error",
]
