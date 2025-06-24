"""
V1 Compatibility Layer for Elfa API
Provides backward compatibility for users migrating from V1 to V2
"""

import time
from typing import Any, Dict, List, Optional
from warnings import warn

from elfa.client.async_client import AsyncElfaClient
from elfa.client.elfa_client import ElfaClient


class V1CompatibilityLayer:
    """
    V1 Compatibility Layer for smooth migration from V1 to V2

    This class provides backward-compatible method signatures for V1 API users
    while internally using the V2 API endpoints. It includes deprecation warnings
    to guide users toward the new V2 methods.

    Args:
        client: ElfaClient or AsyncElfaClient instance
        show_deprecation_warnings: Whether to show deprecation warnings (default: True)

    Example:
        ```python
        from elfa import ElfaClient
        from elfa.client.v1_compatibility import V1CompatibilityLayer

        # Create V2 client
        client = ElfaClient(api_key="your-api-key")

        # Wrap with V1 compatibility
        v1_compat = V1CompatibilityLayer(client)

        # Use V1-style methods (with warnings)
        trending = v1_compat.get_trending_tokens(timeWindow="24h")
        mentions = v1_compat.get_mentions_by_keywords(
            keywords="bitcoin,ethereum",
            from_timestamp=int(time.time()) - 86400,
            to_timestamp=int(time.time())
        )
        ```
    """

    def __init__(
        self,
        client: ElfaClient,
        show_deprecation_warnings: bool = True,
    ):
        self.client = client
        self.show_deprecation_warnings = show_deprecation_warnings

    def _warn_deprecated(
        self, old_method: str, new_method: str, version: str = "3.0.0"
    ):
        """Show deprecation warning for V1 methods"""
        if self.show_deprecation_warnings:
            warn(
                f"{old_method} is deprecated and will be removed in version {version}. "
                f"Use {new_method} instead.",
                DeprecationWarning,
                stacklevel=3,
            )

    # Health and authentication endpoints (V1 compatible)

    def ping(self):
        """
        V1-compatible ping endpoint

        Deprecated: Use client.ping() directly
        """
        self._warn_deprecated("v1_compat.ping()", "client.ping()")
        return self.client.ping()

    def get_api_key_status(self):
        """
        V1-compatible API key status endpoint

        Deprecated: Use client.get_api_key_status() directly
        """
        self._warn_deprecated(
            "v1_compat.get_api_key_status()", "client.get_api_key_status()"
        )
        return self.client.get_api_key_status()

    # Trending tokens (V1 compatible signature)

    def get_trending_tokens(
        self,
        timeWindow: str = "24h",
        page: int = 1,
        pageSize: int = 50,
        minMentions: int = 5,
    ):
        """
        Get trending tokens (V1-compatible method signature)

        Args:
            timeWindow: Time window for analysis (V1 style parameter name)
            page: Page number for pagination
            pageSize: Number of items per page (V1 style parameter name)
            minMentions: Minimum number of mentions (V1 style parameter name)

        Deprecated: Use client.get_trending_tokens() with snake_case parameters
        """
        self._warn_deprecated(
            "v1_compat.get_trending_tokens(timeWindow=...)",
            "client.get_trending_tokens(time_window=...)",
        )

        return self.client.get_trending_tokens(
            time_window=timeWindow,
            page=page,
            page_size=pageSize,
            min_mentions=minMentions,
        )

    # Mentions endpoints (V1 compatible)

    def get_mentions_by_keywords(
        self,
        keywords: str,
        from_timestamp: int,
        to_timestamp: int,
        limit: int = 20,
        searchType: Optional[str] = None,
        cursor: Optional[str] = None,
    ):
        """
        Get mentions by keywords (V1-compatible method)

        This method automatically chooses between V1 and V2 endpoints based on
        the timeframe and provides the most appropriate response format.

        Args:
            keywords: Keywords to search for
            from_timestamp: Start timestamp (V1 style - required)
            to_timestamp: End timestamp (V1 style - required)
            limit: Maximum results to return
            searchType: Search type ("and" or "or") - V1 style parameter name
            cursor: Pagination cursor

        Deprecated: Use client.get_mentions_by_keywords_v1() or client.get_keyword_mentions()
        """
        self._warn_deprecated(
            "v1_compat.get_mentions_by_keywords()",
            "client.get_mentions_by_keywords_v1() or client.get_keyword_mentions()",
        )

        # Calculate time difference to choose appropriate endpoint
        time_diff = to_timestamp - from_timestamp

        # If timeframe is less than 30 days, use V1 endpoint for exact compatibility
        if time_diff <= (30 * 24 * 60 * 60):  # 30 days
            return self.client.get_mentions_by_keywords_v1(
                keywords=keywords,
                from_timestamp=from_timestamp,
                to_timestamp=to_timestamp,
                limit=limit,
                search_type=searchType,
                cursor=cursor,
            )
        else:
            # For longer timeframes, guide users to V2 API with period-based search
            warn(
                "Timeframe exceeds 30 days. Consider using V2 API with period-based search: "
                "client.get_keyword_mentions(keywords=..., period='30d')",
                UserWarning,
                stacklevel=2,
            )
            # Try to convert to V2 API call
            return self.client.get_keyword_mentions(
                keywords=keywords,
                period="30d",  # Use maximum period
                limit=limit,
                search_type=searchType,
                cursor=cursor,
            )

    def get_mentions_with_smart_engagement(
        self,
        from_timestamp: int,
        to_timestamp: int,
        limit: int = 20,
        mentionedByType: Optional[str] = None,
        sentiment: Optional[str] = None,
        includeAccountInfo: bool = False,
        includeCoins: bool = False,
    ):
        """
        Get mentions with smart engagement (V1-compatible method signature)

        Args:
            from_timestamp: Start timestamp
            to_timestamp: End timestamp
            limit: Maximum results
            mentionedByType: Type of mention source (V1 style parameter name)
            sentiment: Sentiment filter
            includeAccountInfo: Include account details (V1 style parameter name)
            includeCoins: Include coin information (V1 style parameter name)

        Deprecated: Use client.get_mentions_with_smart_engagement() with snake_case parameters
        """
        self._warn_deprecated(
            "v1_compat.get_mentions_with_smart_engagement(mentionedByType=...)",
            "client.get_mentions_with_smart_engagement(mentioned_by_type=...)",
        )

        return self.client.get_mentions_with_smart_engagement(
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            limit=limit,
            mentioned_by_type=mentionedByType,
            sentiment=sentiment,
            include_account_info=includeAccountInfo,
            include_coins=includeCoins,
        )

    # Account endpoints (V1 compatible)

    def get_account_smart_stats(self, username: str):
        """
        Get account smart stats (V1-compatible method)

        Deprecated: Use client.get_account_smart_stats() directly
        """
        self._warn_deprecated(
            "v1_compat.get_account_smart_stats()", "client.get_account_smart_stats()"
        )
        return self.client.get_account_smart_stats(username)

    # Helper methods for migration

    def get_migration_guide(self) -> Dict[str, str]:
        """
        Get a migration guide for moving from V1 to V2 API

        Returns:
            Dictionary mapping V1 methods to their V2 equivalents
        """
        return {
            "v1_compat.get_trending_tokens(timeWindow='24h')": "client.get_trending_tokens(time_window='24h')",
            "v1_compat.get_mentions_by_keywords(keywords, from_ts, to_ts)": "client.get_mentions_by_keywords_v1(keywords, from_ts, to_ts) or client.get_keyword_mentions(keywords=..., period='24h')",
            "v1_compat.get_mentions_with_smart_engagement(mentionedByType='smart')": "client.get_mentions_with_smart_engagement(mentioned_by_type='smart')",
            "v1_compat.get_account_smart_stats(username)": "client.get_account_smart_stats(username)",
            "Parameter naming": "V1 uses camelCase (timeWindow), V2 uses snake_case (time_window)",
            "Time specification": "V1 uses from/to timestamps, V2 supports both timestamps and period strings",
            "Response formats": "V2 provides enhanced response types with better type safety",
        }

    def list_deprecated_methods(self) -> List[str]:
        """
        List all deprecated V1-compatible methods

        Returns:
            List of deprecated method names
        """
        return [
            "ping",
            "get_api_key_status",
            "get_trending_tokens",
            "get_mentions_by_keywords",
            "get_mentions_with_smart_engagement",
            "get_account_smart_stats",
        ]


class AsyncV1CompatibilityLayer:
    """
    Async V1 Compatibility Layer for smooth migration from V1 to V2

    Similar to V1CompatibilityLayer but for async clients.
    """

    def __init__(
        self,
        client: AsyncElfaClient,
        show_deprecation_warnings: bool = True,
    ):
        self.client = client
        self.show_deprecation_warnings = show_deprecation_warnings

    def _warn_deprecated(
        self, old_method: str, new_method: str, version: str = "3.0.0"
    ):
        """Show deprecation warning for V1 methods"""
        if self.show_deprecation_warnings:
            warn(
                f"{old_method} is deprecated and will be removed in version {version}. "
                f"Use {new_method} instead.",
                DeprecationWarning,
                stacklevel=3,
            )

    async def ping(self):
        """V1-compatible async ping endpoint"""
        self._warn_deprecated("async_v1_compat.ping()", "async_client.ping()")
        return await self.client.ping()

    async def get_api_key_status(self):
        """V1-compatible async API key status endpoint"""
        self._warn_deprecated(
            "async_v1_compat.get_api_key_status()", "async_client.get_api_key_status()"
        )
        return await self.client.get_api_key_status()

    async def get_trending_tokens(
        self,
        timeWindow: str = "24h",
        page: int = 1,
        pageSize: int = 50,
        minMentions: int = 5,
    ):
        """Get trending tokens (V1-compatible async method signature)"""
        self._warn_deprecated(
            "async_v1_compat.get_trending_tokens(timeWindow=...)",
            "async_client.get_trending_tokens(time_window=...)",
        )

        return await self.client.get_trending_tokens(
            time_window=timeWindow,
            page=page,
            page_size=pageSize,
            min_mentions=minMentions,
        )

    async def get_mentions_by_keywords(
        self,
        keywords: str,
        from_timestamp: int,
        to_timestamp: int,
        limit: int = 20,
        searchType: Optional[str] = None,
        cursor: Optional[str] = None,
    ):
        """Get mentions by keywords (V1-compatible async method)"""
        self._warn_deprecated(
            "async_v1_compat.get_mentions_by_keywords()",
            "async_client.get_mentions_by_keywords_v1() or async_client.get_keyword_mentions()",
        )

        time_diff = to_timestamp - from_timestamp

        if time_diff <= (30 * 24 * 60 * 60):  # 30 days
            return await self.client.get_mentions_by_keywords_v1(
                keywords=keywords,
                from_timestamp=from_timestamp,
                to_timestamp=to_timestamp,
                limit=limit,
                search_type=searchType,
                cursor=cursor,
            )
        else:
            warn(
                "Timeframe exceeds 30 days. Consider using V2 API with period-based search.",
                UserWarning,
                stacklevel=2,
            )
            return await self.client.get_keyword_mentions(
                keywords=keywords,
                period="30d",
                limit=limit,
                search_type=searchType,
                cursor=cursor,
            )

    async def get_mentions_with_smart_engagement(
        self,
        from_timestamp: int,
        to_timestamp: int,
        limit: int = 20,
        mentionedByType: Optional[str] = None,
        sentiment: Optional[str] = None,
        includeAccountInfo: bool = False,
        includeCoins: bool = False,
    ):
        """Get mentions with smart engagement (V1-compatible async method signature)"""
        self._warn_deprecated(
            "async_v1_compat.get_mentions_with_smart_engagement(mentionedByType=...)",
            "async_client.get_mentions_with_smart_engagement(mentioned_by_type=...)",
        )

        return await self.client.get_mentions_with_smart_engagement(
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            limit=limit,
            mentioned_by_type=mentionedByType,
            sentiment=sentiment,
            include_account_info=includeAccountInfo,
            include_coins=includeCoins,
        )

    async def get_account_smart_stats(self, username: str):
        """Get account smart stats (V1-compatible async method)"""
        self._warn_deprecated(
            "async_v1_compat.get_account_smart_stats()",
            "async_client.get_account_smart_stats()",
        )
        return await self.client.get_account_smart_stats(username)
