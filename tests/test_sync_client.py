"""
Tests for the synchronous Elfa client
"""

from unittest.mock import Mock, patch

import httpx
import pytest
from pydantic import ValidationError

from elfa import ElfaClient
from elfa.exceptions import (
    ElfaAPIError,
    ElfaAuthenticationError,
    ElfaNetworkError,
    ElfaTimeoutError,
    ElfaValidationError,
)


class TestElfaClientInit:
    """Test client initialization"""

    def test_init_with_api_key(self):
        """Test successful initialization with API key"""
        client = ElfaClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.elfa.ai"
        assert "x-elfa-api-key" in client.headers
        assert client.headers["x-elfa-api-key"] == "test-key"

    def test_init_without_api_key(self):
        """Test initialization fails without API key"""
        with pytest.raises(ValueError, match="API key is required"):
            ElfaClient(api_key="")

    def test_init_with_custom_settings(self):
        """Test initialization with custom settings"""
        client = ElfaClient(
            api_key="test-key",
            base_url="https://custom.api.com",
            timeout=60.0,
            max_retries=5,
            user_agent="custom-agent",
        )

        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.headers["User-Agent"] == "custom-agent"

    def test_context_manager(self):
        """Test client works as context manager"""
        with ElfaClient(api_key="test-key") as client:
            assert client.api_key == "test-key"


class TestElfaClientMakeRequest:
    """Test the _make_request method"""

    @patch("httpx.Client.request")
    def test_successful_request(self, mock_request, client, mock_response):
        """Test successful HTTP request"""
        response_data = {"success": True, "data": "test"}
        mock_request.return_value = mock_response(response_data)

        result = client._make_request("GET", "/test")

        assert result == response_data
        mock_request.assert_called_once()

    @patch("httpx.Client.request")
    def test_request_with_params(self, mock_request, client, mock_response):
        """Test request with query parameters"""
        response_data = {"success": True, "data": "test"}
        mock_request.return_value = mock_response(response_data)

        params = {"param1": "value1", "param2": None}
        result = client._make_request("GET", "/test", params=params)

        # None values should be filtered out
        expected_params = {"param1": "value1"}
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["params"] == expected_params

    @patch("httpx.Client.request")
    def test_http_error_handling(self, mock_request, client, mock_response):
        """Test HTTP error handling"""
        mock_request.return_value = mock_response(
            {"message": "Unauthorized"}, status_code=401
        )

        with pytest.raises(ElfaAuthenticationError):
            client._make_request("GET", "/test")

    @patch("httpx.Client.request")
    def test_network_error_with_retry(self, mock_request, client):
        """Test network error with retry logic"""
        mock_request.side_effect = [
            httpx.NetworkError("Connection failed"),
            httpx.NetworkError("Connection failed"),
            Mock(is_success=True, json=lambda: {"success": True}),
        ]

        # Should succeed on third attempt
        result = client._make_request("GET", "/test")
        assert result == {"success": True}
        assert mock_request.call_count == 3

    @patch("httpx.Client.request")
    def test_timeout_error(self, mock_request, client):
        """Test timeout error handling"""
        mock_request.side_effect = httpx.TimeoutException("Request timed out")

        with pytest.raises(ElfaTimeoutError):
            client._make_request("GET", "/test")


class TestElfaClientEndpoints:
    """Test individual API endpoints"""

    @patch("httpx.Client.request")
    def test_ping(self, mock_request, client, mock_response, sample_ping_response):
        """Test ping endpoint"""
        mock_request.return_value = mock_response(sample_ping_response)

        result = client.ping()

        assert result.success is True
        assert result.data["message"] == "pong"
        mock_request.assert_called_once()

        # Check the request was made to correct endpoint
        call_args = mock_request.call_args
        assert "/v2/ping" in call_args[1]["url"]

    @patch("httpx.Client.request")
    def test_get_api_key_status(
        self, mock_request, client, mock_response, sample_api_key_status_response
    ):
        """Test API key status endpoint"""
        mock_request.return_value = mock_response(sample_api_key_status_response)

        result = client.get_api_key_status()

        assert result.success is True
        assert result.data.name == "Test API Key"
        assert result.data.daily_limit == 1000.0
        assert "/v2/key-status" in mock_request.call_args[1]["url"]

    @patch("httpx.Client.request")
    def test_get_trending_tokens(
        self, mock_request, client, mock_response, sample_trending_tokens_response
    ):
        """Test trending tokens endpoint"""
        mock_request.return_value = mock_response(sample_trending_tokens_response)

        result = client.get_trending_tokens(
            time_window="24h", page=1, page_size=50, min_mentions=5
        )

        assert result.success is True
        assert len(result.data.data) == 2
        assert result.data.data[0].token == "bitcoin"
        assert result.data.data[0].change_percent == 25.5

        # Check request parameters
        call_kwargs = mock_request.call_args[1]
        expected_params = {
            "timeWindow": "24h",
            "page": 1,
            "pageSize": 50,
            "minMentions": 5,
        }
        assert call_kwargs["params"] == expected_params

    @patch("httpx.Client.request")
    def test_get_keyword_mentions(
        self, mock_request, client, mock_response, sample_keyword_mentions_response
    ):
        """Test keyword mentions endpoint"""
        mock_request.return_value = mock_response(sample_keyword_mentions_response)

        result = client.get_keyword_mentions(
            keywords="bitcoin,ethereum", period="24h", limit=20
        )

        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0].tweet_id == "1234567890"
        assert result.data[0].account.username == "testuser"
        assert result.metadata.total == 50.0

    @patch("httpx.Client.request")
    def test_get_keyword_mentions_validation_error(self, mock_request, client):
        """Test keyword mentions without required parameters"""
        with pytest.raises(
            ValueError, match="Either keywords or account_name must be provided"
        ):
            client.get_keyword_mentions()

    @patch("httpx.Client.request")
    def test_get_account_smart_stats(
        self, mock_request, client, mock_response, sample_account_smart_stats_response
    ):
        """Test account smart stats endpoint"""
        mock_request.return_value = mock_response(sample_account_smart_stats_response)

        result = client.get_account_smart_stats(username="testuser")

        assert result.success is True
        assert result.data.follower_engagement_ratio == 0.15
        assert result.data.smart_following_count == 50.0

        # Check request parameters
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["params"]["username"] == "testuser"

    @patch("httpx.Client.request")
    def test_get_trending_contract_addresses_twitter(
        self, mock_request, client, mock_response
    ):
        """Test trending contract addresses Twitter endpoint"""
        response_data = {
            "success": True,
            "data": {
                "pageSize": 50.0,
                "page": 1.0,
                "total": 10.0,
                "data": [
                    {
                        "contractAddress": "0x1234567890abcdef",
                        "chain": "ethereum",
                        "mentionCount": 100.0,
                        "changePercent": 25.5,
                    }
                ],
            },
        }
        mock_request.return_value = mock_response(response_data)

        result = client.get_trending_contract_addresses_twitter()

        assert result.success is True
        assert len(result.data.data) == 1
        assert result.data.data[0].contract_address == "0x1234567890abcdef"
        assert result.data.data[0].chain == "ethereum"
        assert (
            "/v2/aggregations/trending-cas/twitter" in mock_request.call_args[1]["url"]
        )

    @patch("httpx.Client.request")
    def test_get_token_news(
        self, mock_request, client, mock_response, sample_token_news_response
    ):
        """Test token news endpoint"""
        mock_request.return_value = mock_response(sample_token_news_response)

        result = client.get_token_news(
            coin_ids="bitcoin,ethereum", page=1, page_size=20
        )

        assert result.success is True
        assert len(result.data) == 1
        assert "/v2/data/token-news" in mock_request.call_args[1]["url"]


class TestErrorHandling:
    """Test error handling scenarios"""

    @patch("httpx.Client.request")
    def test_authentication_error(self, mock_request, client, mock_response):
        """Test 401 authentication error"""
        mock_request.return_value = mock_response(
            {"message": "Invalid API key"}, status_code=401
        )

        with pytest.raises(ElfaAuthenticationError, match="Invalid API key"):
            client.ping()

    @patch("httpx.Client.request")
    def test_validation_error(self, mock_request, client, mock_response):
        """Test 400 validation error"""
        mock_request.return_value = mock_response(
            {"message": "Invalid parameters", "errors": {"param1": "is required"}},
            status_code=400,
        )

        with pytest.raises(ElfaValidationError) as exc_info:
            client.ping()

        assert "Invalid parameters" in str(exc_info.value)
        assert exc_info.value.validation_errors == {"param1": "is required"}

    @patch("httpx.Client.request")
    def test_invalid_json_response(self, mock_request, client):
        """Test invalid JSON response handling"""
        response = Mock(spec=httpx.Response)
        response.is_success = True
        response.json.side_effect = ValueError("Invalid JSON")
        mock_request.return_value = response

        with pytest.raises(ElfaAPIError, match="Failed to parse response JSON"):
            client.ping()

    def test_response_validation_error(self, client):
        """Test response validation against Pydantic models"""
        invalid_data = {"invalid": "response"}

        with pytest.raises(ElfaAPIError, match="Invalid response format"):
            client._validate_response(
                invalid_data,
                type(
                    "MockModel",
                    (),
                    {
                        "model_validate": Mock(
                            side_effect=ValidationError.from_exception_data(
                                "MockModel", []
                            )
                        )
                    },
                ),
            )


class TestV1Endpoints:
    """Test V1 API endpoints"""

    @patch("httpx.Client.request")
    def test_get_mentions_with_smart_engagement(
        self, mock_request, client, mock_response
    ):
        """Test V1 mentions with smart engagement endpoint"""
        # V1 method now uses V2 internally, so mock V2 response format
        response_data = {
            "success": True,
            "data": [
                {
                    "tweetId": "12345",
                    "link": "https://twitter.com/user/status/12345",
                    "likeCount": 100,
                    "quoteCount": 10,
                    "replyCount": 5,
                    "repostCount": 20,
                    "viewCount": 1000,
                    "mentionedAt": "2024-01-01T12:00:00Z",
                    "bookmarkCount": 15,
                    "account": {"username": "testuser", "isVerified": True},
                }
            ],
            "metadata": {"total": 1.0, "cursor": "test-cursor"},
        }
        mock_request.return_value = mock_response(response_data)

        result = client.get_mentions_with_smart_engagement(
            from_timestamp=1704067200,  # 2024-01-01
            to_timestamp=1704153600,  # 2024-01-02
            limit=20,
            mentioned_by_type="smart",
            sentiment="bullish",
            include_account_info=True,
            include_coins=True,
        )

        assert result.success is True
        assert len(result.data) == 1
        # Content will be empty since V2 response doesn't include full text
        assert result.data[0].content == ""
        assert result.data[0].account.username == "testuser"

        # V1 method now calls V2 internally - check for V2 endpoint
        call_kwargs = mock_request.call_args[1]
        # Should be calling keyword mentions with period-based parameters
        assert "keywords" in call_kwargs["params"]
        assert "period" in call_kwargs["params"]
        assert "/v2/data/keyword-mentions" in call_kwargs["url"]

    @patch("httpx.Client.request")
    def test_get_mentions_by_keywords_v1(self, mock_request, client, mock_response):
        """Test V1 keyword mentions endpoint"""
        # V1 method now uses V2 internally, so mock V2 response format
        response_data = {
            "success": True,
            "data": [
                {
                    "tweetId": "1234567890",
                    "link": "https://twitter.com/user/status/1234567890",
                    "likeCount": 300.0,
                    "quoteCount": 0,
                    "replyCount": 50.0,
                    "repostCount": 100.0,
                    "viewCount": 5000.0,
                    "mentionedAt": "2024-01-01T12:00:00Z",
                    "bookmarkCount": 0,
                    "account": {"username": "cryptoexpert", "isVerified": True},
                }
            ],
            "metadata": {"total": 1.0, "cursor": "next-cursor-token"},
        }
        mock_request.return_value = mock_response(response_data)

        result = client.get_mentions_by_keywords_v1(
            keywords="bitcoin,ethereum,crypto",
            from_timestamp=1704067200,
            to_timestamp=1704153600,
            limit=30,
            search_type="or",
            cursor="test-cursor",
        )

        assert result.success is True
        assert len(result.data) == 1
        # Content will be empty since V2 response doesn't include full text
        assert result.data[0].content == ""
        assert result.data[0].twitter_id == "1234567890"

        # V1 method now calls V2 internally - check for V2 endpoint
        call_kwargs = mock_request.call_args[1]
        # Should be calling keyword mentions with period-based parameters
        assert "keywords" in call_kwargs["params"]
        assert "period" in call_kwargs["params"]
        assert "/v2/data/keyword-mentions" in call_kwargs["url"]


class TestEnhancedConfiguration:
    """Test enhanced configuration options"""

    def test_enhanced_config_initialization(self):
        """Test client initialization with enhanced config options"""
        client = ElfaClient(
            api_key="test-key",
            fetch_raw_tweets=True,
            enhancement_timeout=60.0,
            max_batch_size=100,
            strict_mode=True,
            cache_enhancements=False,
        )

        assert client.fetch_raw_tweets is True
        assert client.enhancement_timeout == 60.0
        assert client.max_batch_size == 100
        assert client.strict_mode is True
        assert client.cache_enhancements is False

    def test_default_enhanced_config(self):
        """Test default values for enhanced configuration"""
        client = ElfaClient(api_key="test-key")

        assert client.fetch_raw_tweets is False
        assert client.enhancement_timeout == 30.0
        assert client.max_batch_size == 50
        assert client.strict_mode is False
        assert client.cache_enhancements is True
