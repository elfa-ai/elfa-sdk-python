"""Compact JSON serialization — exact bytes the server signs over."""

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
