"""Compact JSON serialization.

Signed mutations must send the exact bytes the server signs over: a compact JSON
string with no spaces after separators. Using anything else (e.g. the default
``json.dumps`` spacing) produces a signature mismatch and a 401.

The server does not sign the bytes we sent — it re-serializes the body it parsed,
with ``JSON.stringify``. So our output has to survive a JSON round-trip through
JavaScript unchanged, and Python and JavaScript do not agree on how to render
every float. The one that matters in practice is the *integral* float: Python
writes ``50.0`` where ``JSON.stringify`` writes ``50``. Since the EQL surface
takes percentages, leverage and price thresholds as numbers, a caller writing
``value=50.0`` — or any value that came out of a ``/`` division — would otherwise
sign bytes the server can never reproduce. ``_js_number`` normalizes those back
to ints before serializing.
"""

import json
from typing import Any

# JavaScript renders a number in plain decimal notation below 1e21 and switches
# to exponential at or above it. Below the threshold an integral float must
# become an int to match; at or above it Python's own exponential form (``1e+21``)
# already agrees with JavaScript's, so leave it alone.
_JS_EXPONENTIAL_THRESHOLD = 1e21


def _js_number(value: float) -> Any:
    """Return ``value`` as an int when JavaScript would render it as one."""
    if value.is_integer() and abs(value) < _JS_EXPONENTIAL_THRESHOLD:
        return int(value)
    return value


def _normalize(body: Any) -> Any:
    """Recursively rewrite floats that JavaScript would serialize differently."""
    if isinstance(body, float):
        return _js_number(body)
    if isinstance(body, dict):
        return {key: _normalize(value) for key, value in body.items()}
    if isinstance(body, (list, tuple)):
        return [_normalize(item) for item in body]
    return body


def to_compact_json(body: Any) -> str:
    """Serialize ``body`` to compact JSON (``","``/``":"`` separators, no spaces).

    Floats are normalized so the output round-trips through ``JSON.parse`` /
    ``JSON.stringify`` unchanged — see the module docstring.
    """
    return json.dumps(_normalize(body), separators=(",", ":"), ensure_ascii=False)
