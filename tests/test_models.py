"""
Tests for Pydantic models
"""

import pytest
from pydantic import ValidationError

from elfa.models import (
    AccountSmartStatsResponse,
    ApiKeyStatusResponse,
    KeywordMentionsV2Response,
    PingResponse,
    TokenNewsV2Response,
    TrendingCAsV2Response,
    TrendingTokensResponse,
)


class TestPingResponse:
    """Test PingResponse model"""

    def test_valid_ping_response(self):
        """Test valid ping response"""
        data = {"success": True, "data": {"message": "pong"}}

        response = PingResponse.model_validate(data)
        assert response.success is True
        assert response.data["message"] == "pong"

    def test_invalid_ping_response(self):
        """Test invalid ping response"""
        data = {
            "success": True,
            # Missing data field
        }

        with pytest.raises(ValidationError):
            PingResponse.model_validate(data)


class TestApiKeyStatusResponse:
    """Test ApiKeyStatusResponse model"""

    def test_valid_api_key_status_response(self):
        """Test valid API key status response"""
        data = {
            "success": True,
            "data": {
                "name": "Test API Key",
                "dailyLimit": 1000.0,
                "monthlyLimit": 30000.0,
                "tier": "pro",
                "usage": {
                    "remainingMonthly": 25000.0,
                    "remainingDaily": 800.0,
                    "month": 5000.0,
                    "today": 200.0,
                },
                "allowOverage": False,
            },
        }

        response = ApiKeyStatusResponse.model_validate(data)
        assert response.success is True
        assert response.data.name == "Test API Key"
        assert response.data.daily_limit == 1000.0
        assert response.data.usage.remaining_monthly == 25000.0

    def test_api_key_status_with_detailed_format(self):
        """Test API key status with detailed format"""
        data = {
            "success": True,
            "data": {
                "id": 123.0,
                "name": "Test Key",
                "status": "active",
                "dailyRequestLimit": 1000.0,
                "monthlyRequestLimit": 30000.0,
                "expiresAt": "2024-12-31T23:59:59Z",
                "createdAt": "2024-01-01T00:00:00Z",
                "usage": {"monthly": 5000.0, "daily": 200.0},
                "limits": {"monthly": 30000.0, "daily": 1000.0},
                "isExpired": False,
                "remainingRequests": {"monthly": 25000.0, "daily": 800.0},
            },
        }

        response = ApiKeyStatusResponse.model_validate(data)
        assert response.success is True
        assert response.data.id == 123.0
        assert response.data.status == "active"


class TestTrendingTokensResponse:
    """Test TrendingTokensResponse model"""

    def test_valid_trending_tokens_response(self):
        """Test valid trending tokens response"""
        data = {
            "success": True,
            "data": {
                "pageSize": 50.0,
                "page": 1.0,
                "total": 100.0,
                "data": [
                    {
                        "change_percent": 25.5,
                        "previous_count": 100.0,
                        "current_count": 125.0,
                        "token": "bitcoin",
                    },
                    {
                        "change_percent": 15.2,
                        "previous_count": 80.0,
                        "current_count": 92.0,
                        "token": "ethereum",
                    },
                ],
            },
        }

        response = TrendingTokensResponse.model_validate(data)
        assert response.success is True
        assert response.data.page_size == 50.0
        assert len(response.data.data) == 2
        assert response.data.data[0].token == "bitcoin"
        assert response.data.data[0].change_percent == 25.5

    def test_empty_trending_tokens_response(self):
        """Test empty trending tokens response"""
        data = {
            "success": True,
            "data": {"pageSize": 50.0, "page": 1.0, "total": 0.0, "data": []},
        }

        response = TrendingTokensResponse.model_validate(data)
        assert response.success is True
        assert len(response.data.data) == 0
        assert response.data.total == 0.0


class TestKeywordMentionsV2Response:
    """Test KeywordMentionsV2Response model"""

    def test_valid_keyword_mentions_response(self):
        """Test valid keyword mentions response"""
        data = {
            "success": True,
            "data": [
                {
                    "tweetId": "1234567890",
                    "link": "https://twitter.com/user/status/1234567890",
                    "likeCount": 100.0,
                    "repostCount": 25.0,
                    "viewCount": 1000.0,
                    "quoteCount": 5.0,
                    "replyCount": 15.0,
                    "bookmarkCount": 10.0,
                    "mentionedAt": "2024-01-01T12:00:00Z",
                    "account": {"isVerified": True, "username": "testuser"},
                }
            ],
            "metadata": {"total": 50.0, "cursor": "next-cursor-token"},
        }

        response = KeywordMentionsV2Response.model_validate(data)
        assert response.success is True
        assert len(response.data) == 1
        assert response.data[0].tweet_id == "1234567890"
        assert response.data[0].account.username == "testuser"
        assert response.metadata.total == 50.0
        assert response.metadata.cursor == "next-cursor-token"

    def test_keyword_mentions_with_none_values(self):
        """Test keyword mentions with None metric values"""
        data = {
            "success": True,
            "data": [
                {
                    "tweetId": "1234567890",
                    "link": "https://twitter.com/user/status/1234567890",
                    "likeCount": None,
                    "repostCount": None,
                    "viewCount": None,
                    "quoteCount": None,
                    "replyCount": None,
                    "bookmarkCount": None,
                    "mentionedAt": "2024-01-01T12:00:00Z",
                }
            ],
            "metadata": {"total": 1.0},
        }

        response = KeywordMentionsV2Response.model_validate(data)
        assert response.success is True
        assert response.data[0].like_count is None
        assert response.data[0].view_count is None


class TestAccountSmartStatsResponse:
    """Test AccountSmartStatsResponse model"""

    def test_valid_account_smart_stats_response(self):
        """Test valid account smart stats response"""
        data = {
            "success": True,
            "data": {
                "followerEngagementRatio": 0.15,
                "averageEngagement": 0.08,
                "smartFollowingCount": 50.0,
            },
        }

        response = AccountSmartStatsResponse.model_validate(data)
        assert response.success is True
        assert response.data.follower_engagement_ratio == 0.15
        assert response.data.average_engagement == 0.08
        assert response.data.smart_following_count == 50.0


class TestTrendingCAsV2Response:
    """Test TrendingCAsV2Response model"""

    def test_valid_trending_cas_response(self):
        """Test valid trending contract addresses response"""
        data = {
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
                    },
                    {
                        "contractAddress": "AbCdEf123456789",
                        "chain": "solana",
                        "mentionCount": 75.0,
                        "changePercent": -10.2,
                    },
                ],
            },
        }

        response = TrendingCAsV2Response.model_validate(data)
        assert response.success is True
        assert len(response.data.data) == 2
        assert response.data.data[0].contract_address == "0x1234567890abcdef"
        assert response.data.data[0].chain == "ethereum"
        assert response.data.data[1].chain == "solana"

    def test_invalid_chain_type(self):
        """Test invalid chain type validation"""
        data = {
            "success": True,
            "data": {
                "pageSize": 50.0,
                "page": 1.0,
                "total": 1.0,
                "data": [
                    {
                        "contractAddress": "0x1234567890abcdef",
                        "chain": "invalid_chain",  # Invalid chain
                        "mentionCount": 100.0,
                        "changePercent": 25.5,
                    }
                ],
            },
        }

        with pytest.raises(ValidationError):
            TrendingCAsV2Response.model_validate(data)


class TestTokenNewsV2Response:
    """Test TokenNewsV2Response model"""

    def test_valid_token_news_response(self):
        """Test valid token news response"""
        data = {
            "success": True,
            "data": [
                {
                    "tweetId": "news123456",
                    "link": "https://twitter.com/news/status/news123456",
                    "likeCount": 500.0,
                    "repostCount": 100.0,
                    "viewCount": 5000.0,
                    "quoteCount": 25.0,
                    "replyCount": 50.0,
                    "bookmarkCount": 75.0,
                    "mentionedAt": "2024-01-01T15:30:00Z",
                    "account": {"isVerified": True, "username": "cryptonews"},
                }
            ],
            "metadata": {"pageSize": 20.0, "page": 1.0, "total": 1.0},
        }

        response = TokenNewsV2Response.model_validate(data)
        assert response.success is True
        assert len(response.data) == 1
        assert response.data[0].tweet_id == "news123456"
        assert response.data[0].account.username == "cryptonews"
        assert response.metadata.page_size == 20.0


class TestModelFieldAliases:
    """Test that field aliases work correctly"""

    def test_field_aliases_trending_tokens(self):
        """Test field aliases in trending tokens"""
        data = {
            "change_percent": 25.5,
            "previous_count": 100.0,
            "current_count": 125.0,
            "token": "bitcoin",
        }

        from elfa.models.aggregations import TrendingToken

        token = TrendingToken.model_validate(data)

        # Should be accessible via Python naming convention
        assert token.change_percent == 25.5
        assert token.previous_count == 100.0
        assert token.current_count == 125.0

    def test_field_aliases_api_key_status(self):
        """Test field aliases in API key status"""
        data = {"dailyLimit": 1000.0, "monthlyLimit": 30000.0, "allowOverage": False}

        from elfa.models.auth import ApiKeyStatusData

        # This should fail due to missing required fields, but let's test partial validation
        with pytest.raises(ValidationError):
            ApiKeyStatusData.model_validate(data)
