"""Compact JSON serialization — exact bytes the server signs over."""

import json
import shutil
import subprocess

import pytest

from elfa.utils.serialize import to_compact_json


def test_no_spaces_after_separators():
    assert to_compact_json({"a": 1, "b": 2}) == '{"a":1,"b":2}'


def test_preserves_insertion_order_not_sorted():
    assert to_compact_json({"z": 1, "a": 2}) == '{"z":1,"a":2}'


def test_preserves_non_ascii_literally():
    out = to_compact_json({"name": "héllo 世界"})
    assert out == '{"name":"héllo 世界"}'
    assert "\\u" not in out


def test_nested_and_lists_compact():
    assert to_compact_json({"a": [1, {"b": "c"}]}) == '{"a":[1,{"b":"c"}]}'


# The server signs a body it re-serializes itself with JSON.stringify, so our
# bytes have to match *JavaScript's* rendering, not Python's. The expected
# strings below are what JSON.stringify emits; test_matches_node_json_stringify
# checks them against a real engine when one is available.


@pytest.mark.parametrize(
    "body,expected",
    [
        # Integral floats: Python would write 50.0, JavaScript writes 50. This is
        # the case that reaches real callers — close_percent=50.0, leverage=10.0,
        # or anything that came out of a division.
        ({"closePercent": 50.0}, '{"closePercent":50}'),
        ({"leverage": 10.0}, '{"leverage":10}'),
        ({"positionSizePercent": 25.0}, '{"positionSizePercent":25}'),
        ({"value": -3.0}, '{"value":-3}'),
        ({"value": 0.0}, '{"value":0}'),
        # Fractional floats already agree — both use shortest round-trip.
        ({"value": 3.5}, '{"value":3.5}'),
        ({"value": 0.1}, '{"value":0.1}'),
        # Ints and bools pass through untouched (bool is an int subclass, and
        # must not be coerced to 1/0).
        ({"n": 7, "flag": True, "off": False}, '{"n":7,"flag":true,"off":false}'),
        # Below 1e21 JavaScript writes plain digits, so the float must become an int.
        ({"value": 1e16}, '{"value":10000000000000000}'),
        # At/above 1e21 it switches to exponential, which Python already matches.
        ({"value": 1e21}, '{"value":1e+21}'),
        # Normalization has to reach nested structures, not just the top level.
        (
            {"query": {"conditions": [{"value": 100000.0}]}},
            '{"query":{"conditions":[{"value":100000}]}}',
        ),
    ],
)
def test_matches_javascript_number_rendering(body, expected):
    assert to_compact_json(body) == expected


NODE_PARITY_CASES = [
    {"closePercent": 50.0},
    {"leverage": 10.0, "size": "0.001"},
    {"value": 1e16},
    {"value": 1e21},
    {"value": 3.5},
    {"n": 7, "flag": True, "off": False},
    {"query": {"conditions": [{"value": 100000.0}]}, "title": "héllo 世界"},
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("body", NODE_PARITY_CASES)
def test_matches_node_json_stringify(body):
    """Round-trip our bytes through the engine the server actually uses.

    This is the load-bearing check: the server computes its signature over
    JSON.stringify(JSON.parse(<our bytes>)), so any divergence here is a 401 the
    caller cannot work around.
    """
    ours = to_compact_json(body)
    theirs = subprocess.run(
        [
            "node",
            "-e",
            "process.stdout.write(JSON.stringify(JSON.parse(process.argv[1])))",
            ours,
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert ours == theirs


def test_normalization_does_not_change_parsed_value():
    """Rewriting 50.0 to 50 must not change what the server reads."""
    for body in NODE_PARITY_CASES:
        assert json.loads(to_compact_json(body)) == json.loads(json.dumps(body))
