"""
HMAC-SHA256 request signing for Auto/Trade mutations.

The server verifies the signature over ``timestamp + METHOD + mounted_path + body``,
where ``body`` is the compact JSON string it re-serializes from the parsed request
body (empty string for a bodyless request). The client must therefore sign and send
those exact bytes — see ``elfa.utils.serialize.to_compact_json``.
"""

import hashlib
import hmac
import time
from typing import Dict


def sign_request(
    secret: str, method: str, mounted_path: str, body: str
) -> Dict[str, str]:
    """Return the signature headers for a signed request.

    Args:
        secret: The account's HMAC secret.
        method: Uppercase HTTP method (e.g. ``"POST"``).
        mounted_path: Router-relative path (e.g. ``"/orders"``).
        body: The exact compact JSON body string, or ``""`` for a bodyless request.
    """
    timestamp = str(int(time.time()))
    payload = f"{timestamp}{method}{mounted_path}{body}"
    signature = hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return {"x-elfa-timestamp": timestamp, "x-elfa-signature": signature}
