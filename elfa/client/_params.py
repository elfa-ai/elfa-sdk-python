"""Pure request builders for the data endpoints.

Each returns ``(path, query)`` or ``(path, body)`` so the sync and async clients
share one source of truth for URL/param mapping and client-side validation.
"""

from typing import Any, Dict, Optional, Tuple

from elfa.exceptions import ElfaValidationError

Query = Tuple[str, Dict[str, Any]]


def _drop_none(params: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in params.items() if value is not None}


def _require_window_or_range(
    time_window: Optional[str], from_time: Optional[int], to_time: Optional[int]
) -> None:
    has_from = from_time is not None
    has_to = to_time is not None
    if has_from != has_to:
        raise ElfaValidationError("When using from_time/to_time, both must be provided")
    if not time_window and not (has_from and has_to):
        raise ElfaValidationError(
            "You must provide either time_window or both from_time and to_time"
        )


def trending_tokens(
    time_window: Optional[str],
    from_time: Optional[int],
    to_time: Optional[int],
    page: Optional[int],
    page_size: Optional[int],
    min_mentions: Optional[int],
) -> Query:
    _require_window_or_range(time_window, from_time, to_time)
    return "/v2/aggregations/trending-tokens", _drop_none(
        {
            "timeWindow": time_window,
            "from": from_time,
            "to": to_time,
            "page": page,
            "pageSize": page_size,
            "minMentions": min_mentions,
        }
    )


def account_smart_stats(username: str) -> Query:
    if not username:
        raise ElfaValidationError("username is required")
    return "/v2/account/smart-stats", {"username": username}


def keyword_mentions(
    keywords: Optional[str],
    account_name: Optional[str],
    time_window: Optional[str],
    from_time: Optional[int],
    to_time: Optional[int],
    limit: Optional[int],
    search_type: Optional[str],
    cursor: Optional[str],
    reposts: Optional[bool],
) -> Query:
    if not keywords and not account_name:
        raise ElfaValidationError("Either keywords or account_name must be provided")
    return "/v2/data/keyword-mentions", _drop_none(
        {
            "keywords": keywords,
            "accountName": account_name,
            "timeWindow": time_window,
            "from": from_time,
            "to": to_time,
            "limit": limit,
            "searchType": search_type,
            "cursor": cursor,
            "reposts": reposts,
        }
    )


def token_news(
    time_window: Optional[str],
    from_time: Optional[int],
    to_time: Optional[int],
    page: Optional[int],
    page_size: Optional[int],
    coin_ids: Optional[str],
    reposts: Optional[bool],
) -> Query:
    return "/v2/data/token-news", _drop_none(
        {
            "timeWindow": time_window,
            "from": from_time,
            "to": to_time,
            "page": page,
            "pageSize": page_size,
            "coinIds": coin_ids,
            "reposts": reposts,
        }
    )


def trending_cas(
    platform: str,
    time_window: Optional[str],
    from_time: Optional[int],
    to_time: Optional[int],
    page: Optional[int],
    page_size: Optional[int],
    min_mentions: Optional[int],
) -> Query:
    _require_window_or_range(time_window, from_time, to_time)
    return f"/v2/aggregations/trending-cas/{platform}", _drop_none(
        {
            "timeWindow": time_window,
            "from": from_time,
            "to": to_time,
            "page": page,
            "pageSize": page_size,
            "minMentions": min_mentions,
        }
    )


def top_mentions(
    ticker: str,
    time_window: Optional[str],
    from_time: Optional[int],
    to_time: Optional[int],
    page: Optional[int],
    page_size: Optional[int],
    reposts: Optional[bool],
) -> Query:
    if not ticker:
        raise ElfaValidationError("ticker is required")
    return "/v2/data/top-mentions", _drop_none(
        {
            "ticker": ticker,
            "timeWindow": time_window,
            "from": from_time,
            "to": to_time,
            "page": page,
            "pageSize": page_size,
            "reposts": reposts,
        }
    )


def event_summary(
    keywords: str,
    from_time: Optional[int],
    to_time: Optional[int],
    time_window: Optional[str],
    search_type: Optional[str],
) -> Query:
    if not keywords:
        raise ElfaValidationError("keywords is required")
    return "/v2/data/event-summary", _drop_none(
        {
            "keywords": keywords,
            "from": from_time,
            "to": to_time,
            "timeWindow": time_window,
            "searchType": search_type,
        }
    )


def trending_narratives(
    time_frame: Optional[str],
    max_narratives: Optional[int],
    max_tweets_per_narrative: Optional[int],
) -> Query:
    return "/v2/data/trending-narratives", _drop_none(
        {
            "timeFrame": time_frame,
            "maxNarratives": max_narratives,
            "maxTweetsPerNarrative": max_tweets_per_narrative,
        }
    )


def chat_body(
    message: Optional[str],
    session_id: Optional[str],
    analysis_type: Optional[str],
    speed: Optional[str],
    asset_metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if (analysis_type or "chat") == "chat" and not (message and message.strip()):
        raise ElfaValidationError("message is required for chat analysis")
    return _drop_none(
        {
            "message": message,
            "sessionId": session_id,
            "analysisType": analysis_type,
            "speed": speed,
            "assetMetadata": asset_metadata,
        }
    )
