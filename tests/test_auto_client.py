"""Auto client: signing, paths, param mapping, and SSE streaming."""

import hashlib
import hmac
from contextlib import asynccontextmanager, contextmanager

import httpx
import respx

from elfa.client.auto_client import AsyncAutoClient, AutoClient
from elfa.utils.http import SyncTransport
from tests.conftest import BASE_URL


def _transport():
    return SyncTransport("k", BASE_URL, retries=0)


def _sig(secret, timestamp, method, path, body):
    payload = f"{timestamp}{method}{path}{body}"
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


@respx.mock
def test_create_query_signs_over_relative_path_with_compact_body():
    captured = {}

    def handler(request):
        captured["body"] = request.content.decode()
        captured["ts"] = request.headers.get("x-elfa-timestamp")
        captured["sig"] = request.headers.get("x-elfa-signature")
        return httpx.Response(200, json={"id": "q1", "status": "pending"})

    respx.post(f"{BASE_URL}/v2/auto/queries").mock(side_effect=handler)
    client = AutoClient(_transport(), hmac_secret="sec")
    query = {
        "query": {"conditions": {"AND": []}, "actions": [], "expiresIn": "1h"},
        "title": "t",
    }
    result = client.create_query(query)

    assert result.id == "q1"
    body = captured["body"]
    assert body == (
        '{"query":{"conditions":{"AND":[]},"actions":[],"expiresIn":"1h"},"title":"t"}'
    )
    assert captured["sig"] == _sig("sec", captured["ts"], "POST", "/queries", body)


@respx.mock
def test_create_query_unsigned_without_secret():
    def handler(request):
        assert "x-elfa-signature" not in request.headers
        return httpx.Response(200, json={"id": "q1"})

    respx.post(f"{BASE_URL}/v2/auto/queries").mock(side_effect=handler)
    AutoClient(_transport()).create_query({"query": {}})


@respx.mock
def test_cancel_query_signs_empty_body():
    captured = {}

    def handler(request):
        captured["body"] = request.content.decode()
        captured["ts"] = request.headers.get("x-elfa-timestamp")
        captured["sig"] = request.headers.get("x-elfa-signature")
        return httpx.Response(200, json={"id": "q1", "status": "cancelled"})

    respx.post(f"{BASE_URL}/v2/auto/queries/q1/cancel").mock(side_effect=handler)
    AutoClient(_transport(), hmac_secret="sec").cancel_query("q1")

    assert captured["body"] == ""
    assert captured["sig"] == _sig(
        "sec", captured["ts"], "POST", "/queries/q1/cancel", ""
    )


@respx.mock
def test_get_query_parses_poll_response():
    respx.get(f"{BASE_URL}/v2/auto/queries/q1").mock(
        return_value=httpx.Response(
            200,
            json={
                "queryId": "q1",
                "status": "active",
                "latestEvaluation": {"evaluatedAt": None, "wouldTriggerNow": None},
                "executions": [],
            },
        )
    )
    result = AutoClient(_transport()).get_query("q1")
    assert result.query_id == "q1"
    assert result.status == "active"


@respx.mock
def test_list_queries_sends_params():
    route = respx.get(f"{BASE_URL}/v2/auto/queries").mock(
        return_value=httpx.Response(200, json={"queries": []})
    )
    AutoClient(_transport()).list_queries(status="active", limit=5)
    params = route.calls[-1].request.url.params
    assert params["status"] == "active"
    assert params["limit"] == "5"


@respx.mock
def test_validate_symbol_url_encodes_symbol():
    route = respx.get(url__regex=rf"{BASE_URL}/v2/auto/validate-symbol/.*").mock(
        return_value=httpx.Response(200, json={"supported": "true"})
    )
    result = AutoClient(_transport()).validate_symbol("hyperliquid", "BTC/USD")
    assert result.supported == "true"
    assert "BTC%2FUSD" in str(route.calls[-1].request.url)


@respx.mock
def test_disconnect_exchange_returns_raw():
    respx.delete(f"{BASE_URL}/v2/auto/exchanges/hyperliquid").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    assert AutoClient(_transport()).disconnect_exchange("hyperliquid") == {
        "success": True
    }


class _FakeStreamTransport:
    def __init__(self, lines):
        self._lines = lines
        self.path = None
        self.headers = None

    @contextmanager
    def stream_lines(self, method, path, headers=None):
        self.path = path
        self.headers = headers
        yield iter(self._lines)


def test_stream_query_maps_events_and_stops_on_end():
    lines = [
        "event: triggered",
        'data: {"queryId":"q1"}',
        "",
        "event: end",
        "data: {}",
        "",
        "event: after",
        "data: {}",
        "",
    ]
    transport = _FakeStreamTransport(lines)
    events = list(AutoClient(transport).stream_query("q1"))

    assert transport.path == "/v2/auto/queries/q1/stream"
    assert transport.headers == {"Accept": "text/event-stream"}
    assert [event.event for event in events] == ["triggered", "end"]
    assert events[0].data == {"queryId": "q1"}


class _FakeAsyncStreamTransport:
    def __init__(self, lines):
        self._lines = lines

    @asynccontextmanager
    async def stream_lines(self, method, path, headers=None):
        async def gen():
            for line in self._lines:
                yield line

        yield gen()


async def test_async_stream_all_maps_events():
    lines = ["event: update", 'data: {"n":1}', "", "event: end", "data: {}", ""]
    client = AsyncAutoClient(_FakeAsyncStreamTransport(lines))
    events = [event async for event in client.stream_all()]
    assert [event.event for event in events] == ["update", "end"]
    assert events[0].data == {"n": 1}
