"""Gated live integration tests against a real Elfa API.

Skipped unless ``ELFA_API_KEY`` is set. Optional env:
``ELFA_BASE_URL``, ``ELFA_STAGING_SECRET``, and
``ELFA_CHAT_STREAM=1`` to exercise chat streaming on a PAYG or Enterprise key.
"""

import os

import pytest

from elfa import ElfaClient

API_KEY = os.environ.get("ELFA_API_KEY")
BASE_URL = os.environ.get("ELFA_BASE_URL")
STAGING_SECRET = os.environ.get("ELFA_STAGING_SECRET")

pytestmark = pytest.mark.skipif(not API_KEY, reason="ELFA_API_KEY not set")

NOTIFY_QUERY = {
    "query": {
        "conditions": {
            "AND": [
                {
                    "source": "price",
                    "method": "current",
                    "args": {"symbol": "BTC", "exchange": "hyperliquid"},
                    "operator": ">",
                    "value": 9_999_999,
                }
            ]
        },
        "actions": [
            {"stepId": "step_1", "type": "notify", "params": {"message": "sdk it"}}
        ],
        "expiresIn": "1h",
    },
    "title": "python sdk integration test",
}


@pytest.fixture
def client():
    kwargs = {"api_key": API_KEY}
    if BASE_URL:
        kwargs["base_url"] = BASE_URL
    if STAGING_SECRET:
        kwargs["headers"] = {"x-staging-secret": STAGING_SECRET}
    instance = ElfaClient(**kwargs)
    yield instance
    instance.close()


def test_ping(client):
    assert client.ping().success is True


def test_key_status(client):
    assert client.get_api_key_status().success is True


def test_trending_tokens(client):
    result = client.get_trending_tokens(time_window="24h")
    assert result.success is True
    assert isinstance(result.data.data, list)


def test_top_mentions(client):
    assert client.get_top_mentions("BTC", time_window="24h").success is True


def test_keyword_mentions(client):
    result = client.get_keyword_mentions(keywords="bitcoin", time_window="1h", limit=3)
    assert result.success is True


def test_trending_narratives(client):
    result = client.get_trending_narratives(
        time_frame="day", max_narratives=2, max_tweets_per_narrative=2
    )
    assert result.success is True
    assert isinstance(result.data.trending_narratives, list)


def test_account_smart_stats(client):
    assert client.get_account_smart_stats("cz_binance").success is True


def test_auto_validate_query(client):
    assert client.auto.validate_query(NOTIFY_QUERY).valid is True


def test_auto_validate_symbol(client):
    assert client.auto.validate_symbol("hyperliquid", "BTC").supported == "true"


def test_auto_notification_lifecycle(client):
    created = client.auto.create_query(NOTIFY_QUERY)
    query_id = created.id or created.query_id
    assert query_id

    polled = client.auto.get_query(query_id)
    assert polled.query_id == query_id

    client.auto.cancel_query(query_id)
    client.auto.delete_query(query_id)


@pytest.mark.skipif(
    not os.environ.get("ELFA_CHAT_STREAM"),
    reason="requires a PAYG or Enterprise key (set ELFA_CHAT_STREAM=1)",
)
def test_chat_stream_yields_events(client):
    events = [event.type for event in client.chat_stream("what is bitcoin")]
    assert events
    assert events[-1] == "complete"
