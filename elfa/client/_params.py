"""Pure request builders for the data endpoints.

Each returns ``(path, query)`` or ``(path, body)`` so the sync and async clients
share one source of truth for URL/param mapping and client-side validation.
"""

from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from elfa.client.base import drop_none
from elfa.exceptions import ElfaValidationError

Query = Tuple[str, Dict[str, Any]]


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
    return "/v2/aggregations/trending-tokens", drop_none(
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
    return "/v2/data/keyword-mentions", drop_none(
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
    return "/v2/data/token-news", drop_none(
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
    return f"/v2/aggregations/trending-cas/{platform}", drop_none(
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
    return "/v2/data/top-mentions", drop_none(
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
    return "/v2/data/event-summary", drop_none(
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
    return "/v2/data/trending-narratives", drop_none(
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
    asset_metadata: Optional[Mapping[str, Any]],
    include_sources: Optional[bool],
) -> Dict[str, Any]:
    if (analysis_type or "chat") == "chat" and not (message and message.strip()):
        raise ElfaValidationError("message is required for chat analysis")
    return drop_none(
        {
            "message": message,
            "sessionId": session_id,
            "analysisType": analysis_type,
            "speed": speed,
            "assetMetadata": asset_metadata,
            "includeSources": include_sources,
        }
    )


def _csv(name: str, values: Optional[Sequence[str]]) -> Optional[str]:
    if values is None:
        return None
    if not values:
        raise ElfaValidationError(
            f"{name} is empty, which would drop the filter. "
            "Omit it, or pass at least one value."
        )
    if isinstance(values, str):
        return values
    return ",".join(values)


def _market(market: str) -> str:
    if market not in ("crypto", "equity"):
        raise ElfaValidationError('market must be "crypto" or "equity"')
    return market


def v3_entities(
    q: str,
    entity_type: Optional[Sequence[str]],
    limit: Optional[int],
    cursor: Optional[str],
) -> Query:
    if not q:
        raise ElfaValidationError("q is required")
    return "/v3/entities", drop_none(
        {
            "q": q,
            "entityType": _csv("entity_type", entity_type),
            "limit": limit,
            "cursor": cursor,
        }
    )


def v3_events(
    q: Optional[str],
    from_time: Optional[int],
    to_time: Optional[int],
    event_ids: Optional[Sequence[str]],
    event_class: Optional[str],
    event_type: Optional[str],
    implication: Optional[str],
    entity_ids: Optional[Sequence[str]],
    asset_class: Optional[str],
    novelty: Optional[str],
    alert_action: Optional[Sequence[str]],
    sort: Optional[str],
    has_storyline: Optional[bool],
    arc_id: Optional[str],
    notable: Optional[bool],
    order: Optional[str],
    limit: Optional[int],
    cursor: Optional[str],
) -> Query:
    return "/v3/events", drop_none(
        {
            "q": q,
            "from": from_time,
            "to": to_time,
            "eventIds": _csv("event_ids", event_ids),
            "eventClass": event_class,
            "eventType": event_type,
            "implication": implication,
            "entityIds": _csv("entity_ids", entity_ids),
            "assetClass": asset_class,
            "novelty": novelty,
            "alertAction": _csv("alert_action", alert_action),
            "sort": sort,
            "hasStoryline": has_storyline,
            "arcId": arc_id,
            "notable": notable,
            "order": order,
            "limit": limit,
            "cursor": cursor,
        }
    )


def v3_storylines(
    q: Optional[str],
    from_time: Optional[int],
    to_time: Optional[int],
    storyline_ids: Optional[Sequence[str]],
    entity_ids: Optional[Sequence[str]],
    status: Optional[str],
    relation: Optional[Sequence[str]],
    order: Optional[str],
    limit: Optional[int],
    cursor: Optional[str],
) -> Query:
    return "/v3/events/storylines", drop_none(
        {
            "q": q,
            "from": from_time,
            "to": to_time,
            "storylineIds": _csv("storyline_ids", storyline_ids),
            "entityIds": _csv("entity_ids", entity_ids),
            "status": status,
            "relation": _csv("relation", relation),
            "order": order,
            "limit": limit,
            "cursor": cursor,
        }
    )


def v3_arcs(
    q: Optional[str],
    arc_ids: Optional[Sequence[str]],
    status: Optional[str],
    asset_class: Optional[str],
    entity_ids: Optional[Sequence[str]],
    sort: Optional[str],
    order: Optional[str],
    limit: Optional[int],
    cursor: Optional[str],
) -> Query:
    return "/v3/events/arcs", drop_none(
        {
            "q": q,
            "arcIds": _csv("arc_ids", arc_ids),
            "status": status,
            "assetClass": asset_class,
            "entityIds": _csv("entity_ids", entity_ids),
            "sort": sort,
            "order": order,
            "limit": limit,
            "cursor": cursor,
        }
    )


def v3_call_book(
    market: str,
    from_time: int,
    to_time: Optional[int],
    order: Optional[str],
    limit: Optional[int],
    cursor: Optional[str],
) -> Query:
    return f"/v3/market/{_market(market)}/call-book", drop_none(
        {
            "from": from_time,
            "to": to_time,
            "order": order,
            "limit": limit,
            "cursor": cursor,
        }
    )


def v3_mindshare(
    market: str,
    period: Optional[str],
    to_time: Optional[int],
    limit: Optional[int],
    cursor: Optional[str],
) -> Query:
    return f"/v3/market/{_market(market)}/mindshare", drop_none(
        {"period": period, "to": to_time, "limit": limit, "cursor": cursor}
    )


def v3_trending_contracts(
    from_time: int,
    to_time: Optional[int],
    min_mentions: Optional[int],
    limit: Optional[int],
    cursor: Optional[str],
) -> Query:
    return "/v3/market/crypto/trending-contracts", drop_none(
        {
            "from": from_time,
            "to": to_time,
            "minMentions": min_mentions,
            "limit": limit,
            "cursor": cursor,
        }
    )


def v3_calls(
    from_time: Optional[int],
    to_time: Optional[int],
    call_ids: Optional[Sequence[str]],
    handle: Optional[str],
    entity_ids: Optional[Sequence[str]],
    order: Optional[str],
    limit: Optional[int],
    cursor: Optional[str],
) -> Query:
    return "/v3/calls", drop_none(
        {
            "from": from_time,
            "to": to_time,
            "callIds": _csv("call_ids", call_ids),
            "handle": handle,
            "entityIds": _csv("entity_ids", entity_ids),
            "order": order,
            "limit": limit,
            "cursor": cursor,
        }
    )


def v3_call_episodes(
    from_time: Optional[int],
    to_time: Optional[int],
    episode_ids: Optional[Sequence[str]],
    handle: Optional[str],
    entity_ids: Optional[Sequence[str]],
    status: Optional[str],
    direction: Optional[str],
    asset_class: Optional[str],
    order: Optional[str],
    limit: Optional[int],
    cursor: Optional[str],
) -> Query:
    return "/v3/calls/episodes", drop_none(
        {
            "from": from_time,
            "to": to_time,
            "episodeIds": _csv("episode_ids", episode_ids),
            "handle": handle,
            "entityIds": _csv("entity_ids", entity_ids),
            "status": status,
            "direction": direction,
            "assetClass": asset_class,
            "order": order,
            "limit": limit,
            "cursor": cursor,
        }
    )


def v3_positioning(entity_id: str) -> Query:
    if not entity_id:
        raise ElfaValidationError("entity_id is required")
    return "/v3/calls/positioning", {"entityId": entity_id}


def v3_top_accounts(
    metric: Optional[str],
    order: Optional[str],
    limit: Optional[int],
    cursor: Optional[str],
) -> Query:
    return "/v3/people/accounts", drop_none(
        {"metric": metric, "order": order, "limit": limit, "cursor": cursor}
    )
