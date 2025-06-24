"""
Elfa SDK Exception Classes
"""

from elfa.exceptions.base import (
    ElfaAPIError,
    ElfaAuthenticationError,
    ElfaNetworkError,
    ElfaNotFoundError,
    ElfaRateLimitError,
    ElfaTimeoutError,
    ElfaValidationError,
    handle_http_error,
)

__all__ = [
    "ElfaAPIError",
    "ElfaAuthenticationError",
    "ElfaRateLimitError",
    "ElfaNotFoundError",
    "ElfaValidationError",
    "ElfaNetworkError",
    "ElfaTimeoutError",
    "handle_http_error",
]
