"""Trade client: exact-byte signing, paths, and response parsing."""

import hashlib
import hmac

import httpx
import pytest
import respx

from elfa.client.trade_client import TradeClient
from elfa.utils.http import SyncTransport
from tests.conftest import BASE_URL


def _transport():
    return SyncTransport("k", BASE_URL, retries=0)


@respx.mock
def test_place_order_signs_exact_compact_bytes():
    captured = {}

    def handler(request):
        captured["body"] = request.content.decode()
        captured["ts"] = request.headers.get("x-elfa-timestamp")
        captured["sig"] = request.headers.get("x-elfa-signature")
        return httpx.Response(
            200,
            json={
                "success": True,
                "orderId": "o1",
                "filledSize": "0.001",
                "avgFillPrice": "50000",
            },
        )

    respx.post(f"{BASE_URL}/v2/trade/orders").mock(side_effect=handler)
    client = TradeClient(_transport(), hmac_secret="sec")
    order = {
        "exchange": "hyperliquid",
        "symbol": "BTC",
        "side": "buy",
        "orderType": "market",
        "size": "0.001",
    }
    result = client.place_order(order)

    assert result.order_id == "o1"
    body = captured["body"]
    assert body == (
        '{"exchange":"hyperliquid","symbol":"BTC","side":"buy",'
        '"orderType":"market","size":"0.001"}'
    )
    payload = f'{captured["ts"]}POST/orders{body}'
    assert (
        captured["sig"]
        == hmac.new(b"sec", payload.encode(), hashlib.sha256).hexdigest()
    )


@respx.mock
def test_preview_order_parses_and_needs_no_secret():
    respx.post(f"{BASE_URL}/v2/trade/orders/preview").mock(
        return_value=httpx.Response(200, json={"success": True, "wouldExecute": True})
    )
    result = TradeClient(_transport()).preview_order(
        {
            "exchange": "hyperliquid",
            "symbol": "BTC",
            "side": "buy",
            "orderType": "market",
        }
    )
    assert result.would_execute is True


@pytest.mark.parametrize(
    "method,path",
    [
        ("preview_order", "/v2/trade/orders/preview"),
        ("place_order", "/v2/trade/orders"),
        ("cancel_order", "/v2/trade/orders/cancel"),
        ("modify_order", "/v2/trade/orders/modify"),
        ("preview_close_position", "/v2/trade/positions/close/preview"),
        ("close_position", "/v2/trade/positions/close"),
        ("preview_set_position_tpsl", "/v2/trade/positions/tpsl/preview"),
        ("set_position_tpsl", "/v2/trade/positions/tpsl"),
    ],
)
@respx.mock
def test_trade_methods_hit_expected_paths(method, path):
    route = respx.post(f"{BASE_URL}{path}").mock(
        return_value=httpx.Response(200, json={"success": True, "wouldExecute": True})
    )
    getattr(TradeClient(_transport()), method)(
        {"exchange": "hyperliquid", "symbol": "BTC"}
    )
    assert route.called
