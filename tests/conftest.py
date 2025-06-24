"""
Test configuration and fixtures for Elfa SDK tests
"""

from unittest.mock import Mock

import httpx
import pytest
import pytest_asyncio

from elfa import AsyncElfaClient, ElfaClient


@pytest.fixture
def api_key():
    """Test API key"""
    return "test-api-key-12345"


@pytest.fixture
def base_url():
    """Test base URL"""
    return "https://api.test.elfa.ai"


@pytest.fixture
def client(api_key, base_url):
    """Sync client for testing"""
    return ElfaClient(api_key=api_key, base_url=base_url)


@pytest_asyncio.fixture
async def async_client(api_key, base_url):
    """Async client for testing"""
    client = AsyncElfaClient(api_key=api_key, base_url=base_url)
    yield client
    await client.close()


@pytest.fixture
def mock_response():
    """Mock HTTP response"""

    def _mock_response(data, status_code=200, headers=None):
        response = Mock(spec=httpx.Response)
        response.is_success = status_code < 400
        response.status_code = status_code
        response.json.return_value = data
        response.headers = headers or {}
        return response

    return _mock_response


@pytest.fixture
def sample_ping_response():
    """Sample ping response"""
    return {"success": True, "data": {"message": "pong"}}


@pytest.fixture
def sample_api_key_status_response():
    """Sample API key status response"""
    return {
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


@pytest.fixture
def sample_trending_tokens_response():
    """Sample trending tokens response"""
    return {
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


@pytest.fixture
def sample_keyword_mentions_response():
    """Sample keyword mentions response"""
    return {
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


@pytest.fixture
def sample_token_news_response():
    """Sample token news response with page pagination"""
    return {
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
        "metadata": {"pageSize": 20.0, "page": 1.0, "total": 50.0},
    }


@pytest.fixture
def sample_account_smart_stats_response():
    """Sample account smart stats response"""
    return {
        "success": True,
        "data": {
            "followerEngagementRatio": 0.15,
            "averageEngagement": 0.08,
            "smartFollowingCount": 50.0,
        },
    }
