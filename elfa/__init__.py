"""
Elfa AI Python SDK

Official Python SDK for the Elfa API — social intelligence, AI chat, and the
Auto condition engine for crypto.
"""

from elfa.client.async_client import AsyncElfaClient
from elfa.client.auto_client import AsyncAutoClient, AutoClient
from elfa.client.elfa_client import ElfaClient
from elfa.exceptions import (
    ElfaAPIError,
    ElfaAuthenticationError,
    ElfaNetworkError,
    ElfaNotFoundError,
    ElfaRateLimitError,
    ElfaTimeoutError,
    ElfaValidationError,
)
from elfa.version import VERSION as __version__

__author__ = "Elfa AI"
__email__ = "support@elfa.ai"

__all__ = [
    "ElfaClient",
    "AsyncElfaClient",
    "AutoClient",
    "AsyncAutoClient",
    "ElfaAPIError",
    "ElfaAuthenticationError",
    "ElfaRateLimitError",
    "ElfaNotFoundError",
    "ElfaValidationError",
    "ElfaNetworkError",
    "ElfaTimeoutError",
    "__version__",
]
