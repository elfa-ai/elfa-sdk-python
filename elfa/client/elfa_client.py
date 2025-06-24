"""
Main synchronous Elfa API client
"""

import time
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import httpx
from pydantic import ValidationError

from elfa.exceptions import (
    ElfaAPIError,
    ElfaNetworkError,
    ElfaTimeoutError,
    handle_http_error,
)
from elfa.models import (
    AccountSmartStatsResponse,
    ApiKeyStatusResponse,
    KeywordMentionsV2Response,
    PingResponse,
    TokenNewsV2Response,
    TopMentionsV2Response,
    TrendingCAsV2Response,
    TrendingTokensResponse,
)


class ElfaClient:
    """
    Synchronous client for the Elfa API

    This client provides access to all Elfa API v2 endpoints with automatic
    error handling, rate limiting, and response validation. Enhanced functionality
    is available through Twitter API integration.

    Args:
        api_key: Your Elfa API key
        base_url: Base URL for the API (defaults to production)
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum number of retries for failed requests (default: 3)
        retry_delay: Delay between retries in seconds (default: 1)
        user_agent: Custom user agent string
        fetch_raw_tweets: Enable Twitter API integration for enhanced responses (default: False)
        enhancement_timeout: Timeout for Twitter API enhancement requests (default: 30)
        max_batch_size: Maximum tweets to enhance in one batch (default: 50)
        strict_mode: Fail if any enhancement fails (default: False)
        cache_enhancements: Cache Twitter API results (default: True)

    Example:
        ```python
        from elfa import ElfaClient

        # Basic usage
        client = ElfaClient(api_key="your-api-key")

        # Enhanced usage with Twitter integration
        client = ElfaClient(
            api_key="your-api-key",
            fetch_raw_tweets=True,
            enhancement_timeout=60,
            max_batch_size=100
        )

        # Get trending tokens
        trending = client.get_trending_tokens(time_window="24h")

        # Search mentions
        mentions = client.get_keyword_mentions(keywords="bitcoin,ethereum")
        ```
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.elfa.ai",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        user_agent: Optional[str] = None,
        # Enhancement options
        fetch_raw_tweets: bool = False,
        twitter_bearer_token: Optional[str] = None,
        enhancement_timeout: float = 30.0,
        max_batch_size: int = 50,
        strict_mode: bool = False,
        cache_enhancements: bool = True,
    ):
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Enhancement configuration
        self.fetch_raw_tweets = fetch_raw_tweets
        self.twitter_bearer_token = twitter_bearer_token
        self.enhancement_timeout = enhancement_timeout
        self.max_batch_size = max_batch_size
        self.strict_mode = strict_mode
        self.cache_enhancements = cache_enhancements

        # Default headers
        self.headers = {
            "x-elfa-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": user_agent or f"elfa-python-sdk/2.0.0",
        }

        # Create HTTP client
        self.client = httpx.Client(
            headers=self.headers,
            timeout=timeout,
            follow_redirects=True,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the HTTP client"""
        self.client.close()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with retries and error handling
        """
        url = urljoin(f"{self.base_url}/", endpoint.lstrip("/"))

        # Clean up None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                )

                # Handle HTTP errors
                if not response.is_success:
                    handle_http_error(response)

                # Parse JSON response
                try:
                    return response.json()
                except Exception as e:
                    raise ElfaAPIError(f"Failed to parse response JSON: {e}")

            except httpx.TimeoutException as e:
                last_exception = ElfaTimeoutError(f"Request timed out: {e}")
            except httpx.NetworkError as e:
                last_exception = ElfaNetworkError(f"Network error: {e}", e)
            except (ElfaAPIError, ElfaTimeoutError, ElfaNetworkError):
                # Re-raise our custom exceptions without retry
                raise
            except Exception as e:
                last_exception = ElfaAPIError(f"Unexpected error: {e}")

            # Wait before retry (except on last attempt)
            if attempt < self.max_retries:
                time.sleep(self.retry_delay * (2**attempt))  # Exponential backoff

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        else:
            raise ElfaAPIError("Request failed after all retries")

    def _validate_response(self, data: Dict[str, Any], model_class):
        """
        Validate response data against a Pydantic model
        """
        try:
            return model_class.model_validate(data)
        except ValidationError as e:
            raise ElfaAPIError(f"Invalid response format: {e}")

    # Health and authentication endpoints

    def ping(self) -> PingResponse:
        """
        Health check endpoint to verify API availability

        Returns:
            PingResponse: Simple health check response

        Example:
            ```python
            response = client.ping()
            print(response.data.message)
            ```
        """
        data = self._make_request("GET", "/v2/ping")
        return self._validate_response(data, PingResponse)

    def get_api_key_status(self) -> ApiKeyStatusResponse:
        """
        Get the current status and usage of your API key

        Returns:
            ApiKeyStatusResponse: API key status and usage information

        Example:
            ```python
            status = client.get_api_key_status()
            print(f"Daily usage: {status.data.usage.daily}")
            print(f"Monthly limit: {status.data.monthly_limit}")
            ```
        """
        data = self._make_request("GET", "/v2/key-status")
        return self._validate_response(data, ApiKeyStatusResponse)

    # Aggregation endpoints

    def get_trending_tokens(
        self,
        time_window: str = "24h",
        page: int = 1,
        page_size: int = 50,
        min_mentions: int = 5,
    ) -> TrendingTokensResponse:
        """
        Get trending tokens based on mention count

        Args:
            time_window: Time window for analysis (e.g., "1h", "24h", "7d")
            page: Page number for pagination
            page_size: Number of items per page
            min_mentions: Minimum number of mentions required

        Returns:
            TrendingTokensResponse: List of trending tokens with metrics

        Example:
            ```python
            trending = client.get_trending_tokens(
                time_window="24h",
                page_size=20,
                min_mentions=10
            )

            for token in trending.data.data:
                print(f"{token.token}: {token.current_count} mentions")
            ```
        """
        params = {
            "timeWindow": time_window,
            "page": page,
            "pageSize": page_size,
            "minMentions": min_mentions,
        }

        data = self._make_request(
            "GET", "/v2/aggregations/trending-tokens", params=params
        )
        return self._validate_response(data, TrendingTokensResponse)

    def get_trending_contract_addresses_twitter(
        self,
        time_window: str = "24h",
        page: int = 1,
        page_size: int = 50,
        min_mentions: int = 5,
    ) -> TrendingCAsV2Response:
        """
        Get trending contract addresses mentioned on Twitter/X

        Args:
            time_window: Time window for analysis (e.g., "1h", "24h", "7d")
            page: Page number for pagination
            page_size: Number of items per page
            min_mentions: Minimum number of mentions required

        Returns:
            TrendingCAsV2Response: List of trending contract addresses
        """
        params = {
            "timeWindow": time_window,
            "page": page,
            "pageSize": page_size,
            "minMentions": min_mentions,
        }

        data = self._make_request(
            "GET", "/v2/aggregations/trending-cas/twitter", params=params
        )
        return self._validate_response(data, TrendingCAsV2Response)

    def get_trending_contract_addresses_telegram(
        self,
        time_window: str = "24h",
        page: int = 1,
        page_size: int = 50,
        min_mentions: int = 5,
    ) -> TrendingCAsV2Response:
        """
        Get trending contract addresses mentioned on Telegram

        Args:
            time_window: Time window for analysis (e.g., "1h", "24h", "7d")
            page: Page number for pagination
            page_size: Number of items per page
            min_mentions: Minimum number of mentions required

        Returns:
            TrendingCAsV2Response: List of trending contract addresses
        """
        params = {
            "timeWindow": time_window,
            "page": page,
            "pageSize": page_size,
            "minMentions": min_mentions,
        }

        data = self._make_request(
            "GET", "/v2/aggregations/trending-cas/telegram", params=params
        )
        return self._validate_response(data, TrendingCAsV2Response)

    # Account endpoints

    def get_account_smart_stats(self, username: str) -> AccountSmartStatsResponse:
        """
        Get smart stats for a Twitter/X account

        Args:
            username: Twitter username (without @)

        Returns:
            AccountSmartStatsResponse: Smart account statistics

        Example:
            ```python
            stats = client.get_account_smart_stats("elonmusk")
            print(f"Smart following count: {stats.data.smart_following_count}")
            print(f"Engagement ratio: {stats.data.follower_engagement_ratio}")
            ```
        """
        params = {"username": username}

        data = self._make_request("GET", "/v2/account/smart-stats", params=params)
        return self._validate_response(data, AccountSmartStatsResponse)

    def get_top_mentions(
        self,
        ticker: str,
        time_window: str = "1h",
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> TopMentionsV2Response:
        """
        Get top mentions for a ticker symbol (V2 API)

        Returns the most significant mentions for a given ticker symbol, ranked by
        relevance and engagement within a specified time window. Returns sanitized
        data without raw tweet content.

        Args:
            ticker: The ticker symbol to get mentions for. Prefixing with $ will
                   only return cashtag matches.
            time_window: Time window for mentions (e.g., "1h", "24h", "7d")
            from_timestamp: Start date (unix timestamp, optional)
            to_timestamp: End date (unix timestamp, optional)
            page: Page number for pagination (default: 1)
            page_size: Number of items per page (default: 10)

        Returns:
            TopMentionsV2Response: List of top mentions for the ticker

        Example:
            ```python
            # Get top Bitcoin mentions in the last 24 hours
            mentions = client.get_top_mentions("BTC", time_window="24h")

            # Get top mentions with timestamp range
            mentions = client.get_top_mentions(
                "$BTC",
                from_timestamp=1640995200,
                to_timestamp=1641081600
            )
            ```
        """
        params = {"ticker": ticker, "page": page, "pageSize": page_size}

        # Add time parameters - either timeWindow or from/to timestamps
        if from_timestamp is not None and to_timestamp is not None:
            params["from"] = from_timestamp
            params["to"] = to_timestamp
        else:
            params["timeWindow"] = time_window

        data = self._make_request("GET", "/v2/data/top-mentions", params=params)
        return self._validate_response(data, TopMentionsV2Response)

    # Data endpoints

    def get_keyword_mentions(
        self,
        keywords: Optional[str] = None,
        account_name: Optional[str] = None,
        period: str = "24h",
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
        limit: int = 20,
        search_type: Optional[str] = None,
        cursor: Optional[str] = None,
    ) -> KeywordMentionsV2Response:
        """
        Search mentions by keywords or account name (V2 API)

        Args:
            keywords: Up to 5 keywords to search for, comma-separated
            account_name: Account username to filter by
            period: Time period for search (e.g., "1h", "24h", "7d")
            from_timestamp: Start date (unix timestamp)
            to_timestamp: End date (unix timestamp)
            limit: Number of results to return (max 30)
            search_type: Type of search ("and" or "or")
            cursor: Cursor for pagination

        Returns:
            KeywordMentionsV2Response: List of mentions matching the criteria

        Example:
            ```python
            # Search by keywords
            mentions = client.get_keyword_mentions(
                keywords="bitcoin,ethereum",
                period="24h",
                limit=50
            )

            # Search by account
            mentions = client.get_keyword_mentions(
                account_name="elonmusk",
                period="7d"
            )
            ```
        """
        if not keywords and not account_name:
            raise ValueError("Either keywords or account_name must be provided")

        params = {
            "keywords": keywords,
            "accountName": account_name,
            "period": period,
            "from": from_timestamp,
            "to": to_timestamp,
            "limit": limit,
            "searchType": search_type,
            "cursor": cursor,
        }

        data = self._make_request("GET", "/v2/data/keyword-mentions", params=params)
        return self._validate_response(data, KeywordMentionsV2Response)

    # V1 API endpoints (for compatibility and additional features)

    def get_mentions_with_smart_engagement(
        self,
        from_timestamp: int,
        to_timestamp: int,
        limit: int = 20,
        mentioned_by_type: Optional[str] = None,
        sentiment: Optional[str] = None,
        include_account_info: bool = False,
        include_coins: bool = False,
    ):
        """
        Get mentions with smart engagement (V1 Compatible - Uses V2 + Twitter API)

        This V1-compatible method internally uses V2 endpoints exclusively and enhances responses
        with Twitter API data if available, then transforms back to V1 format.
        V1 API is deprecated - this method provides backward compatibility using V2 infrastructure.

        Query tweets by smart accounts with at least 10 other smart interactions.

        Args:
            from_timestamp: Start date (unix timestamp)
            to_timestamp: End date (unix timestamp)
            limit: Number of results to return (default: 20, max: 30)
            mentioned_by_type: Type of mention source ("general", "ct", "smart")
            sentiment: Sentiment filter ("very-bullish", "bullish", "neutral", "bearish", "very-bearish")
            include_account_info: Include detailed account information
            include_coins: Include associated coin information

        Returns:
            MentionResponse: List of mentions with smart engagement in V1 format

        Example:
            ```python
            import time

            # Get mentions from last 24 hours
            end_time = int(time.time())
            start_time = end_time - (24 * 60 * 60)

            mentions = client.get_mentions_with_smart_engagement(
                from_timestamp=start_time,
                to_timestamp=end_time,
                limit=50,
                mentioned_by_type="smart",
                sentiment="bullish"
            )
            ```
        """
        import time

        from elfa.models.mentions import MentionResponse

        # Step 1: Convert timestamps to period for V2 API
        current_time = int(time.time())

        # Calculate period - default to 24h if within last day
        time_diff = to_timestamp - from_timestamp
        if time_diff <= 3600:  # 1 hour
            period = "1h"
        elif time_diff <= 86400:  # 1 day
            period = "24h"
        elif time_diff <= 604800:  # 1 week
            period = "7d"
        else:
            period = "30d"

        # Step 2: Use V2 keyword mentions with smart filters
        # For smart engagement, we'll search for general crypto keywords
        keywords = "bitcoin,ethereum,crypto,btc,eth,defi,nft,web3"

        # Step 2: Use V2 keyword mentions with smart filters
        v2_response = self.get_keyword_mentions(
            keywords=keywords, period=period, limit=limit, search_type="or"
        )

        # Step 3: Transform V2 response to V1 format
        return self._transform_v2_to_v1_mentions(
            v2_response,
            include_account_info=include_account_info,
            include_coins=include_coins,
            mentioned_by_type=mentioned_by_type,
            sentiment=sentiment,
        )

    def get_mentions_by_keywords_v1(
        self,
        keywords: str,
        from_timestamp: int,
        to_timestamp: int,
        limit: int = 20,
        search_type: Optional[str] = None,
        cursor: Optional[str] = None,
    ):
        """
        Search mentions by keywords (V1 Compatible - Uses V2 + Twitter API)

        This V1-compatible method internally uses V2 endpoints exclusively and enhances responses
        with Twitter API data if available, then transforms back to V1 format.
        V1 API is deprecated - this method provides backward compatibility using V2 infrastructure.

        Query tweets that mentioned up to 5 keywords within a 30-day window.

        Args:
            keywords: Up to 5 keywords to search for, comma-separated. Phrases accepted
            from_timestamp: Start date (unix timestamp)
            to_timestamp: End date (unix timestamp)
            limit: Number of results to return (default: 20, max: 30)
            search_type: Type of search ("and" or "or")
            cursor: Cursor for pagination (expires after 10 seconds)

        Returns:
            GetMentionsByKeywordsResponse: List of mentions matching keywords in V1 format

        Example:
            ```python
            import time

            # Search last 7 days for crypto keywords
            end_time = int(time.time())
            start_time = end_time - (7 * 24 * 60 * 60)

            mentions = client.get_mentions_by_keywords_v1(
                keywords="bitcoin,ethereum,crypto",
                from_timestamp=start_time,
                to_timestamp=end_time,
                limit=30,
                search_type="or"
            )
            ```
        """
        import time

        from elfa.models.mentions import GetMentionsByKeywordsResponse

        # Step 1: Convert timestamps to period for V2 API
        time_diff = to_timestamp - from_timestamp
        if time_diff <= 3600:  # 1 hour
            period = "1h"
        elif time_diff <= 86400:  # 1 day
            period = "24h"
        elif time_diff <= 604800:  # 1 week
            period = "7d"
        else:
            period = "30d"

        # Step 2: Use V2 keyword mentions endpoint
        v2_response = self.get_keyword_mentions(
            keywords=keywords,
            period=period,
            limit=limit,
            search_type=search_type,
            cursor=cursor,
        )

        # Step 3: Transform V2 response to V1 format
        return self._transform_v2_to_v1_keyword_mentions(v2_response, cursor=cursor)

    def get_token_news(
        self,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
        coin_ids: Optional[str] = None,
    ) -> TokenNewsV2Response:
        """
        Get token-related news mentions

        Args:
            from_timestamp: Start date (unix timestamp)
            to_timestamp: End date (unix timestamp)
            page: Page number for pagination
            page_size: Number of items per page
            coin_ids: CoinGecko coin IDs to filter by, comma-separated

        Returns:
            TokenNewsV2Response: List of token news mentions

        Example:
            ```python
            news = client.get_token_news(
                coin_ids="bitcoin,ethereum",
                page_size=50
            )

            for mention in news.data:
                print(f"News: {mention.link}")
            ```
        """
        params = {
            "from": from_timestamp,
            "to": to_timestamp,
            "page": page,
            "pageSize": page_size,
            "coinIds": coin_ids,
        }

        data = self._make_request("GET", "/v2/data/token-news", params=params)
        return self._validate_response(data, TokenNewsV2Response)

    # V1 Compatibility Transformation Methods

    def _transform_v2_to_v1_mentions(
        self,
        v2_response,
        include_account_info: bool = False,
        include_coins: bool = False,
        mentioned_by_type: Optional[str] = None,
        sentiment: Optional[str] = None,
    ):
        """Transform V2 mention response to V1 format with optional Twitter enhancement"""
        from datetime import datetime

        from elfa.models.accounts import Account, AccountData
        from elfa.models.base import OffsetPaginationMetadata
        from elfa.models.mentions import Mention, MentionResponse

        # If Twitter enhancement is enabled, enhance the response first
        enhanced_v2_response = v2_response
        if hasattr(self, "fetch_raw_tweets") and self.fetch_raw_tweets:
            try:
                from elfa.client.response_enhancer import (
                    EnhancementConfig,
                    ResponseEnhancer,
                )
                from elfa.client.twitter_client import TwitterClient, TwitterConfig

                # Check if we have Twitter API configuration
                if hasattr(self, "twitter_bearer_token") and self.twitter_bearer_token:
                    twitter_config = TwitterConfig(
                        bearer_token=self.twitter_bearer_token
                    )
                    twitter_client = TwitterClient(twitter_config)

                    enhancement_config = EnhancementConfig(
                        fetch_raw_tweets=self.fetch_raw_tweets,
                        enhancement_timeout=getattr(self, "enhancement_timeout", 30.0),
                        max_batch_size=getattr(self, "max_batch_size", 50),
                        strict_mode=getattr(self, "strict_mode", False),
                        cache_enhancements=getattr(self, "cache_enhancements", True),
                    )

                    enhancer = ResponseEnhancer(twitter_client, enhancement_config)
                    enhanced_v2_response = enhancer.enhance_mentions_response(
                        v2_response
                    )
            except Exception:
                # Continue without enhancement if Twitter API fails
                pass

        # Transform V2 mentions to V1 format
        v1_mentions = []
        for v2_mention in enhanced_v2_response.data:
            # Create account data if needed
            account_data = None
            if include_account_info and v2_mention.account:
                account_data = Account(
                    id=float(
                        hash(v2_mention.account.username) % 1000000
                    ),  # Generate ID from username
                    username=v2_mention.account.username,
                    isVerified=v2_mention.account.is_verified,
                    followerCount=None,
                    followingCount=None,
                    data=AccountData(
                        profileBannerUrl="",
                        profileImageUrl="",
                        description="",
                        userSince="2020-01-01",
                        location="",
                        name=v2_mention.account.username,
                    ),
                )

            # Get enhanced content if available
            content = getattr(v2_mention, "raw_tweet_text", None) or ""

            # Create V1 mention
            v1_mention = Mention(
                id=float(
                    hash(v2_mention.tweet_id) % 1000000
                ),  # Generate ID from tweet_id
                type="tweet",
                content=content,
                originalUrl=v2_mention.link,
                data={"enhanced": hasattr(v2_mention, "raw_tweet_text")},
                likeCount=v2_mention.like_count,
                quoteCount=v2_mention.quote_count,
                replyCount=v2_mention.reply_count,
                repostCount=v2_mention.repost_count,
                viewCount=v2_mention.view_count,
                mentionedAt=datetime.fromisoformat(
                    v2_mention.mentioned_at.replace("Z", "+00:00")
                ),
                bookmarkCount=v2_mention.bookmark_count,
                account=account_data,
            )

            v1_mentions.append(v1_mention)

        # Create V1 response with metadata
        metadata = OffsetPaginationMetadata(
            total=float(enhanced_v2_response.metadata.total),
            offset=0.0,
            limit=float(len(v1_mentions)),
        )

        return MentionResponse(
            success=enhanced_v2_response.success, data=v1_mentions, metadata=metadata
        )

    def _transform_v2_to_v1_keyword_mentions(
        self, v2_response, cursor: Optional[str] = None
    ):
        """Transform V2 keyword mentions response to V1 format"""
        from elfa.models.base import CursorPaginationMetadata
        from elfa.models.mentions import GetMentionsByKeywordsResponse, SimpleMention

        # Transform V2 mentions to V1 simple mentions
        v1_mentions = []
        for v2_mention in v2_response.data:
            # Get enhanced content if available
            content = getattr(v2_mention, "raw_tweet_text", None) or ""

            # Create simple mention
            simple_mention = SimpleMention(
                id=float(hash(v2_mention.tweet_id) % 1000000),
                twitter_id=v2_mention.tweet_id,
                twitter_user_id=(
                    str(hash(v2_mention.account.username) % 1000000)
                    if v2_mention.account
                    else "0"
                ),
                parent_tweet_id="0",  # Default to "0" since this field is required
                content=content,
                mentioned_at=v2_mention.mentioned_at,
                type="tweet",
                twitter_account_info=None,
                metrics=None,
            )

            v1_mentions.append(simple_mention)

        # Create V1 response with cursor metadata
        metadata = CursorPaginationMetadata(
            total=v2_response.metadata.total,
            cursor=cursor or v2_response.metadata.cursor,
        )

        return GetMentionsByKeywordsResponse(
            success=v2_response.success, data=v1_mentions, metadata=metadata
        )
