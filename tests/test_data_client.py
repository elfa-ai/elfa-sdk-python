"""Data + chat client behaviour (sync and async) with mocked HTTP."""

import httpx
import pytest
import respx

from elfa import AsyncElfaClient, ElfaClient
from elfa.exceptions import ElfaValidationError
from tests.conftest import BASE_URL


def _client():
    return ElfaClient(api_key="k", base_url=BASE_URL, retries=0)


@respx.mock
def test_ping():
    respx.get(f"{BASE_URL}/v2/ping").mock(
        return_value=httpx.Response(
            200, json={"success": True, "data": {"message": "pong"}}
        )
    )
    client = _client()
    assert client.ping().data.message == "pong"
    client.close()


@respx.mock
def test_trending_tokens_sends_params_and_parses():
    route = respx.get(f"{BASE_URL}/v2/aggregations/trending-tokens").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "data": {
                    "total": 1,
                    "page": 1,
                    "pageSize": 50,
                    "data": [
                        {
                            "token": "btc",
                            "current_count": 890,
                            "previous_count": 470,
                            "change_percent": 89.36,
                        }
                    ],
                },
            },
        )
    )
    client = _client()
    result = client.get_trending_tokens(time_window="24h", page_size=50, min_mentions=5)
    assert result.data.data[0].token == "btc"
    params = route.calls[-1].request.url.params
    assert params["timeWindow"] == "24h"
    assert params["pageSize"] == "50"
    assert params["minMentions"] == "5"
    client.close()


def test_trending_tokens_requires_window_or_range():
    client = _client()
    with pytest.raises(ElfaValidationError):
        client.get_trending_tokens()
    with pytest.raises(ElfaValidationError):
        client.get_trending_tokens(from_time=1)
    client.close()


def test_keyword_mentions_requires_keywords_or_account():
    client = _client()
    with pytest.raises(ElfaValidationError):
        client.get_keyword_mentions()
    client.close()


@respx.mock
def test_keyword_mentions_headers_and_bool_param():
    route = respx.get(f"{BASE_URL}/v2/data/keyword-mentions").mock(
        return_value=httpx.Response(
            200, json={"success": True, "data": [], "metadata": {"total": 0}}
        )
    )
    client = _client()
    client.get_keyword_mentions(
        keywords="bitcoin", time_window="1h", limit=3, reposts=False
    )
    request = route.calls[-1].request
    assert request.headers["x-elfa-api-key"] == "k"
    assert request.url.params["keywords"] == "bitcoin"
    assert request.url.params["reposts"] == "false"
    client.close()


def test_top_mentions_requires_ticker():
    client = _client()
    with pytest.raises(ElfaValidationError):
        client.get_top_mentions("")
    client.close()


def test_event_summary_requires_keywords():
    client = _client()
    with pytest.raises(ElfaValidationError):
        client.get_event_summary("")
    client.close()


@respx.mock
def test_chat_posts_compact_body():
    route = respx.post(f"{BASE_URL}/v2/chat").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "data": {"message": "hi", "sessionId": "s", "creditsConsumed": 1},
            },
        )
    )
    client = _client()
    result = client.chat("hello", session_id="s1")
    assert result.data.session_id == "s"
    body = route.calls[-1].request.content.decode()
    assert body == '{"message":"hello","sessionId":"s1"}'
    client.close()


def test_chat_requires_message_for_chat_analysis():
    client = _client()
    with pytest.raises(ElfaValidationError):
        client.chat()
    client.close()


@respx.mock
async def test_async_ping_and_smart_stats():
    respx.get(f"{BASE_URL}/v2/ping").mock(
        return_value=httpx.Response(
            200, json={"success": True, "data": {"message": "pong"}}
        )
    )
    respx.get(f"{BASE_URL}/v2/account/smart-stats").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "data": {
                    "smartFollowingCount": 1,
                    "averageEngagement": 0.1,
                    "averageReach": 2.0,
                },
            },
        )
    )
    async with AsyncElfaClient(api_key="k", base_url=BASE_URL, retries=0) as client:
        assert (await client.ping()).data.message == "pong"
        stats = await client.get_account_smart_stats("x")
        assert stats.data.smart_following_count == 1
