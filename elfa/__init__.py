"""
Elfa AI Python SDK

Official Python SDK for the Elfa API - Social media analytics and insights.
"""

from elfa.client.async_client import AsyncElfaClient
from elfa.client.elfa_client import ElfaClient
from elfa.exceptions import (
    ElfaAPIError,
    ElfaAuthenticationError,
    ElfaNotFoundError,
    ElfaRateLimitError,
    ElfaValidationError,
)

__version__ = "2.0.0"
__author__ = "Elfa AI"
__email__ = "support@elfa.ai"

__all__ = [
    "ElfaClient",
    "AsyncElfaClient",
    "ElfaAPIError",
    "ElfaAuthenticationError",
    "ElfaRateLimitError",
    "ElfaNotFoundError",
    "ElfaValidationError",
]
