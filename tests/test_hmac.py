"""HMAC signing: payload composition and exact-byte signatures."""

import hashlib
import hmac
from unittest.mock import patch

from elfa.utils.hmac import sign_request


def _expected(secret: str, payload: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def test_sign_request_headers_and_payload():
    with patch("elfa.utils.hmac.time.time", return_value=1700000000.9):
        headers = sign_request("secret", "POST", "/orders", '{"a":1}')

    assert headers["x-elfa-timestamp"] == "1700000000"
    assert headers["x-elfa-signature"] == _expected(
        "secret", "1700000000POST/orders" + '{"a":1}'
    )


def test_sign_request_empty_body():
    with patch("elfa.utils.hmac.time.time", return_value=1700000000):
        headers = sign_request("s", "DELETE", "/queries/abc", "")

    assert headers["x-elfa-signature"] == _expected("s", "1700000000DELETE/queries/abc")
