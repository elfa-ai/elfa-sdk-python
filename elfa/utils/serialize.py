"""Compact JSON serialization.

Signed mutations must send the exact bytes the server signs over: a compact JSON
string with no spaces after separators. Using anything else (e.g. the default
``json.dumps`` spacing) produces a signature mismatch and a 401.
"""

import json
from typing import Any


def to_compact_json(body: Any) -> str:
    """Serialize ``body`` to compact JSON (``","``/``":"`` separators, no spaces)."""
    return json.dumps(body, separators=(",", ":"), ensure_ascii=False)
