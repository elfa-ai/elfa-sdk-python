"""
Tests for Twitter API client integration
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from elfa.client.twitter_client import (
    TwitterClient,
    TwitterConfig,
    TwitterTweet,
    TwitterUser,
)
from elfa.exceptions import ElfaAPIError, ElfaNetworkError, ElfaTimeoutError


class TestTwitterConfig:
    """Test Twitter configuration"""

    def test_twitter_config_initialization(self):
        """Test TwitterConfig initialization"""
        config = TwitterConfig(
            bearer_token="test-bearer-token",
            api_key="test-api-key",
            api_secret="test-api-secret",
            timeout=60.0,
            max_retries=5,
        )

        assert config.bearer_token == "test-bearer-token"
        assert config.api_key == "test-api-key"
        assert config.api_secret == "test-api-secret"
        assert config.timeout == 60.0
        assert config.max_retries == 5

    def test_twitter_config_defaults(self):
        """Test TwitterConfig default values"""
        config = TwitterConfig(bearer_token="test-token")

        assert config.bearer_token == "test-token"
        assert config.api_key is None
        assert config.timeout == 30.0
        assert config.max_retries == 3


class TestTwitterClient:
    """Test Twitter API client"""

    def test_twitter_client_initialization(self):
        """Test TwitterClient initialization"""
        config = TwitterConfig(bearer_token="test-bearer-token")
        client = TwitterClient(config)

        assert client.config == config
        assert client.base_url == "https://api.twitter.com/2"
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == "Bearer test-bearer-token"

    def test_twitter_client_no_bearer_token(self):
        """Test TwitterClient fails without bearer token"""
        config = TwitterConfig()

        with pytest.raises(ValueError, match="Twitter Bearer Token is required"):
            TwitterClient(config)

    @pytest.mark.asyncio
    async def test_twitter_client_context_manager(self):
        """Test TwitterClient as async context manager"""
        config = TwitterConfig(bearer_token="test-token")

        async with TwitterClient(config) as client:
            assert client.config.bearer_token == "test-token"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.request", new_callable=AsyncMock)
    async def test_get_tweet_success(self, mock_request):
        """Test successful tweet retrieval"""
        config = TwitterConfig(bearer_token="test-token")
        client = TwitterClient(config)

        # Mock successful response
        tweet_data = {
            "data": {
                "id": "1234567890",
                "text": "This is a test tweet about Bitcoin!",
                "author_id": "987654321",
                "created_at": "2024-01-01T12:00:00.000Z",
                "public_metrics": {
                    "retweet_count": 10,
                    "like_count": 50,
                    "reply_count": 5,
                    "quote_count": 2,
                },
                "context_annotations": [
                    {
                        "domain": {
                            "id": "65",
                            "name": "Interests and Hobbies Vertical",
                        },
                        "entity": {
                            "id": "847618374766264320",
                            "name": "Cryptocurrency",
                        },
                    }
                ],
            }
        }

        response_mock = Mock()
        response_mock.is_success = True
        response_mock.json.return_value = tweet_data
        mock_request.return_value = response_mock

        try:
            tweet = await client.get_tweet("1234567890")

            assert tweet is not None
            assert tweet.id == "1234567890"
            assert tweet.text == "This is a test tweet about Bitcoin!"
            assert tweet.author_id == "987654321"
            assert tweet.public_metrics["like_count"] == 50
            assert len(tweet.context_annotations) == 1

            # Check request was made correctly
            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args[1]
            assert "/tweets/1234567890" in call_kwargs["url"]
            assert "tweet.fields" in call_kwargs["params"]

        finally:
            await client.close()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.request", new_callable=AsyncMock)
    async def test_get_tweet_not_found(self, mock_request):
        """Test tweet not found scenario"""
        config = TwitterConfig(bearer_token="test-token")
        client = TwitterClient(config)

        # Mock 404 response
        response_mock = Mock()
        response_mock.is_success = False
        response_mock.status_code = 404
        response_mock.headers = {"content-type": "application/json"}
        response_mock.json.return_value = {"errors": [{"title": "Not Found"}]}
        mock_request.return_value = response_mock

        try:
            tweet = await client.get_tweet("nonexistent")
            assert tweet is None

        finally:
            await client.close()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.request", new_callable=AsyncMock)
    async def test_get_tweets_batch(self, mock_request):
        """Test batch tweet retrieval"""
        config = TwitterConfig(bearer_token="test-token")
        client = TwitterClient(config)

        # Mock successful batch response
        batch_data = {
            "data": [
                {
                    "id": "1234567890",
                    "text": "First tweet",
                    "author_id": "987654321",
                    "created_at": "2024-01-01T12:00:00.000Z",
                    "public_metrics": {"like_count": 10},
                },
                {
                    "id": "1234567891",
                    "text": "Second tweet",
                    "author_id": "987654322",
                    "created_at": "2024-01-01T13:00:00.000Z",
                    "public_metrics": {"like_count": 20},
                },
            ]
        }

        response_mock = Mock()
        response_mock.is_success = True
        response_mock.json.return_value = batch_data
        mock_request.return_value = response_mock

        try:
            tweets = await client.get_tweets(["1234567890", "1234567891"])

            assert len(tweets) == 2
            assert tweets[0].id == "1234567890"
            assert tweets[0].text == "First tweet"
            assert tweets[1].id == "1234567891"
            assert tweets[1].text == "Second tweet"

            # Check request parameters
            call_kwargs = mock_request.call_args[1]
            assert (
                "ids=1234567890,1234567891" in call_kwargs["url"]
                or call_kwargs["params"]["ids"] == "1234567890,1234567891"
            )

        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_get_tweets_batch_too_large(self):
        """Test batch size limit"""
        config = TwitterConfig(bearer_token="test-token")
        client = TwitterClient(config)

        # Create list of 101 tweet IDs (exceeds limit)
        tweet_ids = [f"tweet_{i}" for i in range(101)]

        try:
            with pytest.raises(ValueError, match="Maximum 100 tweet IDs allowed"):
                await client.get_tweets(tweet_ids)

        finally:
            await client.close()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.request", new_callable=AsyncMock)
    async def test_get_user_by_username(self, mock_request):
        """Test user retrieval by username"""
        config = TwitterConfig(bearer_token="test-token")
        client = TwitterClient(config)

        # Mock successful user response
        user_data = {
            "data": {
                "id": "987654321",
                "username": "testuser",
                "name": "Test User",
                "verified": True,
                "public_metrics": {
                    "followers_count": 1000,
                    "following_count": 500,
                    "tweet_count": 2000,
                },
            }
        }

        response_mock = Mock()
        response_mock.is_success = True
        response_mock.json.return_value = user_data
        mock_request.return_value = response_mock

        try:
            user = await client.get_user_by_username("testuser")

            assert user is not None
            assert user.id == "987654321"
            assert user.username == "testuser"
            assert user.name == "Test User"
            assert user.verified is True
            assert user.public_metrics["followers_count"] == 1000

            # Check request was made correctly
            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args[1]
            assert "/users/by/username/testuser" in call_kwargs["url"]

        finally:
            await client.close()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.request", new_callable=AsyncMock)
    async def test_rate_limit_handling(self, mock_request):
        """Test rate limit handling"""
        config = TwitterConfig(bearer_token="test-token", max_retries=1)
        client = TwitterClient(config)

        # Mock rate limit response, then success
        rate_limit_response = Mock()
        rate_limit_response.is_success = False
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"content-type": "application/json"}
        rate_limit_response.json.return_value = {
            "errors": [{"title": "Rate limit exceeded"}]
        }

        success_response = Mock()
        success_response.is_success = True
        success_response.json.return_value = {
            "data": {
                "id": "1234567890",
                "text": "Test tweet",
                "author_id": "987654321",
                "created_at": "2024-01-01T12:00:00.000Z",
            }
        }

        mock_request.side_effect = [rate_limit_response, success_response]

        try:
            # This should succeed after retry
            tweet = await client.get_tweet("1234567890")
            assert tweet is not None
            assert tweet.id == "1234567890"

            # Should have made 2 requests (rate limit + retry)
            assert mock_request.call_count == 2

        finally:
            await client.close()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.request", new_callable=AsyncMock)
    async def test_network_error_handling(self, mock_request):
        """Test network error handling"""
        config = TwitterConfig(bearer_token="test-token")
        client = TwitterClient(config)

        # Mock network error
        mock_request.side_effect = httpx.NetworkError("Connection failed")

        try:
            with pytest.raises(ElfaNetworkError):
                await client.get_tweet("1234567890")

        finally:
            await client.close()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.request", new_callable=AsyncMock)
    async def test_timeout_error_handling(self, mock_request):
        """Test timeout error handling"""
        config = TwitterConfig(bearer_token="test-token")
        client = TwitterClient(config)

        # Mock timeout error
        mock_request.side_effect = httpx.TimeoutException("Request timed out")

        try:
            with pytest.raises(ElfaTimeoutError):
                await client.get_tweet("1234567890")

        finally:
            await client.close()


class TestTwitterModels:
    """Test Twitter model classes"""

    def test_twitter_tweet_model(self):
        """Test TwitterTweet model validation"""
        tweet_data = {
            "id": "1234567890",
            "text": "This is a test tweet",
            "author_id": "987654321",
            "created_at": "2024-01-01T12:00:00.000Z",
            "public_metrics": {"retweet_count": 10, "like_count": 50},
        }

        tweet = TwitterTweet(**tweet_data)

        assert tweet.id == "1234567890"
        assert tweet.text == "This is a test tweet"
        assert tweet.author_id == "987654321"
        assert tweet.created_at == "2024-01-01T12:00:00.000Z"
        assert tweet.public_metrics["like_count"] == 50

    def test_twitter_user_model(self):
        """Test TwitterUser model validation"""
        user_data = {
            "id": "987654321",
            "username": "testuser",
            "name": "Test User",
            "verified": True,
            "public_metrics": {"followers_count": 1000, "following_count": 500},
        }

        user = TwitterUser(**user_data)

        assert user.id == "987654321"
        assert user.username == "testuser"
        assert user.name == "Test User"
        assert user.verified is True
        assert user.public_metrics["followers_count"] == 1000
