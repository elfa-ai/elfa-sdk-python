"""Transport retry policy, error mapping, streaming, and query-param cleaning."""

import httpx
import pytest
import respx

from elfa.exceptions import (
    ElfaAPIError,
    ElfaAuthenticationError,
    ElfaNetworkError,
    ElfaRateLimitError,
    ElfaTimeoutError,
)
from elfa.utils.http import (
    AsyncTransport,
    SyncTransport,
    backoff_delay,
    clean_params,
    default_headers,
)
from tests.conftest import BASE_URL


def test_clean_params_drops_none_and_lowercases_bools():
    assert clean_params({"a": 1, "b": None, "c": True, "d": False, "e": "x"}) == {
        "a": "1",
        "c": "true",
        "d": "false",
        "e": "x",
    }


@respx.mock
def test_get_retries_on_5xx_then_succeeds():
    route = respx.get(f"{BASE_URL}/v2/ping").mock(
        side_effect=[
            httpx.Response(500, json={"message": "boom"}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    transport = SyncTransport("k", BASE_URL, retries=2, retry_delay=0)
    assert transport.request_json("GET", "/v2/ping") == {"ok": True}
    assert route.call_count == 2
    transport.close()


@respx.mock
def test_post_is_not_retried():
    route = respx.post(f"{BASE_URL}/v2/x").mock(
        return_value=httpx.Response(500, json={"message": "boom"})
    )
    transport = SyncTransport("k", BASE_URL, retries=3, retry_delay=0)
    with pytest.raises(ElfaAPIError):
        transport.request_json("POST", "/v2/x", content="{}")
    assert route.call_count == 1
    transport.close()


@respx.mock
def test_retries_exhausted_raises_last_error():
    route = respx.get(f"{BASE_URL}/v2/ping").mock(
        return_value=httpx.Response(500, json={"message": "boom"})
    )
    transport = SyncTransport("k", BASE_URL, retries=2, retry_delay=0)
    with pytest.raises(ElfaAPIError):
        transport.request_json("GET", "/v2/ping")
    assert route.call_count == 3
    transport.close()


@respx.mock
def test_429_retried_on_get():
    route = respx.get(f"{BASE_URL}/v2/ping").mock(
        side_effect=[
            httpx.Response(429, json={"message": "slow"}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    transport = SyncTransport("k", BASE_URL, retries=2, retry_delay=0)
    assert transport.request_json("GET", "/v2/ping") == {"ok": True}
    assert route.call_count == 2
    transport.close()


@respx.mock
def test_post_429_not_retried():
    route = respx.post(f"{BASE_URL}/v2/x").mock(
        return_value=httpx.Response(429, json={"message": "slow"})
    )
    transport = SyncTransport("k", BASE_URL, retries=3, retry_delay=0)
    with pytest.raises(ElfaRateLimitError):
        transport.request_json("POST", "/v2/x", content="{}")
    assert route.call_count == 1
    transport.close()


@respx.mock
def test_timeout_mapped_and_retried():
    route = respx.get(f"{BASE_URL}/v2/ping").mock(
        side_effect=httpx.ConnectTimeout("slow")
    )
    transport = SyncTransport("k", BASE_URL, retries=2, retry_delay=0)
    with pytest.raises(ElfaTimeoutError):
        transport.request_json("GET", "/v2/ping")
    assert route.call_count == 3
    transport.close()


@respx.mock
def test_connect_error_mapped_to_network_error():
    original = httpx.ConnectError("refused")
    respx.get(f"{BASE_URL}/v2/ping").mock(side_effect=original)
    transport = SyncTransport("k", BASE_URL, retries=0, retry_delay=0)
    with pytest.raises(ElfaNetworkError) as exc:
        transport.request_json("GET", "/v2/ping")
    assert exc.value.original_error is original
    transport.close()


@respx.mock
def test_empty_body_returns_none():
    respx.get(f"{BASE_URL}/v2/ping").mock(return_value=httpx.Response(204))
    transport = SyncTransport("k", BASE_URL, retries=0)
    assert transport.request_json("GET", "/v2/ping") is None
    transport.close()


@respx.mock
def test_malformed_json_raises():
    respx.get(f"{BASE_URL}/v2/ping").mock(
        return_value=httpx.Response(200, content=b"not json")
    )
    transport = SyncTransport("k", BASE_URL, retries=0)
    with pytest.raises(ElfaAPIError, match="Failed to parse response JSON"):
        transport.request_json("GET", "/v2/ping")
    transport.close()


@respx.mock
def test_params_cleaned_end_to_end():
    route = respx.get(f"{BASE_URL}/v2/ping").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    transport = SyncTransport("k", BASE_URL, retries=0)
    transport.request_json("GET", "/v2/ping", params={"a": True, "b": None, "c": 1})
    params = route.calls[-1].request.url.params
    assert dict(params) == {"a": "true", "c": "1"}
    transport.close()


@respx.mock
def test_stream_lines_raises_on_non_success():
    respx.get(f"{BASE_URL}/v2/auto/queries/stream").mock(
        return_value=httpx.Response(401, json={"message": "nope"})
    )
    transport = SyncTransport("k", BASE_URL, retries=0)
    with pytest.raises(ElfaAuthenticationError):
        with transport.stream_lines("GET", "/v2/auto/queries/stream") as _:
            pass
    transport.close()


def test_backoff_delay_formula():
    assert backoff_delay(1.0, 0) == 1.0
    assert backoff_delay(1.0, 3) == 8.0
    assert backoff_delay(0.5, 2) == 2.0


def test_default_headers_extra_can_override():
    headers = default_headers("k", {"Content-Type": "text/plain", "x-c": "v"})
    assert headers["x-elfa-api-key"] == "k"
    assert headers["Content-Type"] == "text/plain"
    assert headers["x-c"] == "v"


@respx.mock
async def test_async_retries_then_succeeds():
    route = respx.get(f"{BASE_URL}/v2/ping").mock(
        side_effect=[
            httpx.Response(500, json={"message": "boom"}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    transport = AsyncTransport("k", BASE_URL, retries=2, retry_delay=0)
    assert await transport.request_json("GET", "/v2/ping") == {"ok": True}
    assert route.call_count == 2
    await transport.close()


@respx.mock
async def test_async_timeout_mapped():
    respx.get(f"{BASE_URL}/v2/ping").mock(side_effect=httpx.ReadTimeout("slow"))
    transport = AsyncTransport("k", BASE_URL, retries=0, retry_delay=0)
    with pytest.raises(ElfaTimeoutError):
        await transport.request_json("GET", "/v2/ping")
    await transport.close()


@respx.mock
async def test_async_stream_lines_raises_on_non_success():
    respx.get(f"{BASE_URL}/v2/auto/queries/stream").mock(
        return_value=httpx.Response(401, json={"message": "nope"})
    )
    transport = AsyncTransport("k", BASE_URL, retries=0)
    with pytest.raises(ElfaAuthenticationError):
        async with transport.stream_lines("GET", "/v2/auto/queries/stream") as _:
            pass
    await transport.close()
