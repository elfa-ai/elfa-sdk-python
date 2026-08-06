"""Model parsing: alias handling, tolerance of extras, nullable fields."""

import pytest

from elfa.client.base import parse_model
from elfa.exceptions import ElfaAPIError
from elfa.models.auto import AutoConvertDraftResponse
from elfa.models.elfa import KeywordMentionsV2Response, PingResponse, ProcessedMention


def test_tolerates_unknown_fields():
    result = PingResponse.model_validate(
        {"success": True, "data": {"message": "x"}, "unexpectedField": 1}
    )
    assert result.data.message == "x"


def test_parse_model_raises_on_missing_required():
    with pytest.raises(ElfaAPIError, match="Invalid response format"):
        parse_model(PingResponse, {"data": {"message": "x"}})


def test_processed_mention_nullable_counts_and_optional_nesting():
    mention = ProcessedMention.model_validate(
        {"tweetId": "1", "link": "l", "mentionedAt": "t", "type": "post"}
    )
    assert mention.like_count is None
    assert mention.account is None
    assert mention.repost_breakdown is None


def test_keyword_cursor_int_or_str():
    as_int = KeywordMentionsV2Response.model_validate(
        {"success": True, "data": [], "metadata": {"total": 1, "cursor": 123}}
    )
    assert as_int.metadata.cursor == 123
    as_str = KeywordMentionsV2Response.model_validate(
        {"success": True, "data": [], "metadata": {"total": 1, "cursor": "abc"}}
    )
    assert as_str.metadata.cursor == "abc"


def test_convert_draft_response_nested_query():
    result = AutoConvertDraftResponse.model_validate(
        {"draftId": "d1", "convertedAt": "t", "query": {"id": "q1"}}
    )
    assert result.draft_id == "d1"
    assert result.query.id == "q1"
