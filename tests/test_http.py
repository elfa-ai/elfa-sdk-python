"""Transport retry policy and query-param cleaning."""

import httpx
import pytest
import respx

from elfa.exceptions import ElfaAPIError
from elfa.utils.http import SyncTransport, clean_params
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
