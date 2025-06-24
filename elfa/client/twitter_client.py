"""
Twitter API integration client for enhanced tweet content
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, Field

from elfa.exceptions import ElfaAPIError, ElfaNetworkError, ElfaTimeoutError


class TwitterConfig(BaseModel):
    """Configuration for Twitter API integration"""

    bearer_token: Optional[str] = Field(None, description="Twitter API Bearer Token")
    api_key: Optional[str] = Field(None, description="Twitter API Key")
    api_secret: Optional[str] = Field(None, description="Twitter API Secret")
    access_token: Optional[str] = Field(None, description="Twitter Access Token")
    access_token_secret: Optional[str] = Field(
        None, description="Twitter Access Token Secret"
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class TwitterTweet(BaseModel):
    """Enhanced tweet data from Twitter API"""

    id: str = Field(..., description="Tweet ID")
    text: str = Field(..., description="Full tweet text")
    author_id: str = Field(..., description="Author user ID")
    created_at: str = Field(..., description="Tweet creation timestamp")
    public_metrics: Optional[Dict[str, int]] = Field(None, description="Tweet metrics")
    context_annotations: Optional[List[Dict[str, Any]]] = Field(
        None, description="Context annotations"
    )
    entities: Optional[Dict[str, Any]] = Field(None, description="Tweet entities")
    referenced_tweets: Optional[List[Dict[str, Any]]] = Field(
        None, description="Referenced tweets"
    )


class TwitterUser(BaseModel):
    """Twitter user information"""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    name: str = Field(..., description="Display name")
    verified: Optional[bool] = Field(None, description="Verification status")
    public_metrics: Optional[Dict[str, int]] = Field(None, description="User metrics")


class TwitterClient:
    """
    Twitter API client for fetching raw tweet content

    This client enables fetching original tweet content to enhance
    Elfa API responses with additional context and data.

    Args:
        config: Twitter API configuration
        base_url: Twitter API base URL (defaults to v2 API)

    Example:
        ```python
        from elfa.client.twitter_client import TwitterClient, TwitterConfig

        twitter_config = TwitterConfig(
            bearer_token="your-bearer-token"
        )

        twitter_client = TwitterClient(twitter_config)

        # Fetch tweet details
        tweet = await twitter_client.get_tweet("1234567890")
        print(tweet.text)
        ```
    """

    def __init__(
        self,
        config: TwitterConfig,
        base_url: str = "https://api.twitter.com/2",
    ):
        self.config = config
        self.base_url = base_url.rstrip("/")

        if not config.bearer_token:
            raise ValueError("Twitter Bearer Token is required")

        # Default headers
        self.headers = {
            "Authorization": f"Bearer {config.bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Create HTTP client
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=config.timeout,
            follow_redirects=True,
        )

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to Twitter API with retries and error handling
        """
        url = urljoin(f"{self.base_url}/", endpoint.lstrip("/"))

        # Clean up None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    params=params,
                )

                # Handle HTTP errors
                if not response.is_success:
                    if response.status_code == 429:
                        # Rate limited - wait longer
                        if attempt < self.config.max_retries:
                            await asyncio.sleep(60)  # Wait 1 minute for rate limit
                            continue

                    error_data = (
                        response.json()
                        if response.headers.get("content-type", "").startswith(
                            "application/json"
                        )
                        else {}
                    )
                    raise ElfaAPIError(
                        f"Twitter API error: {response.status_code} - {error_data}"
                    )

                # Parse JSON response
                try:
                    return response.json()
                except Exception as e:
                    raise ElfaAPIError(
                        f"Failed to parse Twitter API response JSON: {e}"
                    )

            except httpx.TimeoutException as e:
                last_exception = ElfaTimeoutError(f"Twitter API request timed out: {e}")
            except httpx.NetworkError as e:
                last_exception = ElfaNetworkError(f"Twitter API network error: {e}", e)
            except ElfaAPIError:
                # Re-raise our custom exceptions without retry
                raise
            except Exception as e:
                last_exception = ElfaAPIError(f"Unexpected Twitter API error: {e}")

            # Wait before retry (except on last attempt)
            if attempt < self.config.max_retries:
                await asyncio.sleep(1 * (2**attempt))  # Exponential backoff

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        else:
            raise ElfaAPIError("Twitter API request failed after all retries")

    async def get_tweet(
        self,
        tweet_id: str,
        tweet_fields: Optional[List[str]] = None,
        user_fields: Optional[List[str]] = None,
        expansions: Optional[List[str]] = None,
    ) -> Optional[TwitterTweet]:
        """
        Get a single tweet by ID

        Args:
            tweet_id: The ID of the tweet to retrieve
            tweet_fields: Tweet fields to include in response
            user_fields: User fields to include in response
            expansions: Expansions to include (e.g., "author_id")

        Returns:
            TwitterTweet: Tweet data or None if not found
        """
        default_tweet_fields = [
            "id",
            "text",
            "author_id",
            "created_at",
            "public_metrics",
            "context_annotations",
            "entities",
            "referenced_tweets",
        ]

        params = {
            "tweet.fields": ",".join(tweet_fields or default_tweet_fields),
            "user.fields": ",".join(
                user_fields or ["id", "username", "name", "verified", "public_metrics"]
            ),
            "expansions": ",".join(expansions or ["author_id"]),
        }

        try:
            data = await self._make_request("GET", f"/tweets/{tweet_id}", params=params)

            if "data" in data:
                return TwitterTweet(**data["data"])
            return None

        except ElfaAPIError as e:
            # Handle case where tweet is not found or private
            if "404" in str(e) or "403" in str(e):
                return None
            raise

    async def get_tweets(
        self,
        tweet_ids: List[str],
        tweet_fields: Optional[List[str]] = None,
        user_fields: Optional[List[str]] = None,
        expansions: Optional[List[str]] = None,
    ) -> List[TwitterTweet]:
        """
        Get multiple tweets by IDs (batch request)

        Args:
            tweet_ids: List of tweet IDs to retrieve (max 100)
            tweet_fields: Tweet fields to include in response
            user_fields: User fields to include in response
            expansions: Expansions to include

        Returns:
            List[TwitterTweet]: List of tweet data
        """
        if len(tweet_ids) > 100:
            raise ValueError("Maximum 100 tweet IDs allowed per request")

        default_tweet_fields = [
            "id",
            "text",
            "author_id",
            "created_at",
            "public_metrics",
            "context_annotations",
            "entities",
            "referenced_tweets",
        ]

        params = {
            "ids": ",".join(tweet_ids),
            "tweet.fields": ",".join(tweet_fields or default_tweet_fields),
            "user.fields": ",".join(
                user_fields or ["id", "username", "name", "verified", "public_metrics"]
            ),
            "expansions": ",".join(expansions or ["author_id"]),
        }

        try:
            data = await self._make_request("GET", "/tweets", params=params)

            tweets = []
            if "data" in data:
                for tweet_data in data["data"]:
                    tweets.append(TwitterTweet(**tweet_data))

            return tweets

        except ElfaAPIError:
            # Return empty list if batch fails
            return []

    async def get_user_by_username(self, username: str) -> Optional[TwitterUser]:
        """
        Get user information by username

        Args:
            username: Twitter username (without @)

        Returns:
            TwitterUser: User data or None if not found
        """
        params = {"user.fields": "id,username,name,verified,public_metrics"}

        try:
            data = await self._make_request(
                "GET", f"/users/by/username/{username}", params=params
            )

            if "data" in data:
                return TwitterUser(**data["data"])
            return None

        except ElfaAPIError as e:
            # Handle case where user is not found
            if "404" in str(e):
                return None
            raise
