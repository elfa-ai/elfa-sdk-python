"""Synchronous Elfa client: core data + AI chat, with ``.auto`` and ``.trade``."""

from typing import Any, Dict, Optional

from elfa.client import _params as build
from elfa.client.auto_client import AutoClient
from elfa.client.base import parse_model
from elfa.client.trade_client import TradeClient
from elfa.exceptions import ElfaValidationError
from elfa.models.chat import ChatResponse
from elfa.models.elfa import (
    AccountSmartStatsResponse,
    ApiKeyStatusResponse,
    EventSummaryV2Response,
    KeywordMentionsV2Response,
    PingResponse,
    TokenNewsV2Response,
    TopMentionsV2Response,
    TrendingCAsV2Response,
    TrendingNarrativesResponse,
    TrendingTokensResponse,
)
from elfa.utils.http import DEFAULT_BASE_URL, SyncTransport
from elfa.utils.serialize import to_compact_json


class ElfaClient:
    """Synchronous client for the Elfa API.

    Args:
        api_key: Your Elfa API key (sent as ``x-elfa-api-key``).
        base_url: API base URL. Defaults to production.
        timeout: Per-request timeout in seconds.
        retries: Retries for idempotent (GET) requests.
        retry_delay: Base delay for exponential backoff.
        hmac_secret: Secret for signing Auto/Trade mutations. Required for
            trade-action queries and all trade writes; optional otherwise.

    Example:
        >>> from elfa import ElfaClient
        >>> client = ElfaClient(api_key="your-api-key")
        >>> trending = client.get_trending_tokens(time_window="24h")
        >>> for token in trending.data.data:
        ...     print(token.token, token.current_count)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        retries: int = 3,
        retry_delay: float = 1.0,
        hmac_secret: Optional[str] = None,
    ):
        if not api_key:
            raise ElfaValidationError("api_key is required")

        self._transport = SyncTransport(
            api_key, base_url, timeout, retries, retry_delay
        )
        self.auto = AutoClient(self._transport, hmac_secret)
        self.trade = TradeClient(self._transport, hmac_secret)

    def __enter__(self) -> "ElfaClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._transport.close()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._transport.request_json("GET", path, params=params)

    def ping(self) -> PingResponse:
        return parse_model(PingResponse, self._get("/v2/ping"))

    def get_api_key_status(self) -> ApiKeyStatusResponse:
        return parse_model(ApiKeyStatusResponse, self._get("/v2/key-status"))

    def get_trending_tokens(
        self,
        *,
        time_window: Optional[str] = None,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        min_mentions: Optional[int] = None,
    ) -> TrendingTokensResponse:
        path, params = build.trending_tokens(
            time_window, from_time, to_time, page, page_size, min_mentions
        )
        return parse_model(TrendingTokensResponse, self._get(path, params))

    def get_account_smart_stats(self, username: str) -> AccountSmartStatsResponse:
        path, params = build.account_smart_stats(username)
        return parse_model(AccountSmartStatsResponse, self._get(path, params))

    def get_keyword_mentions(
        self,
        *,
        keywords: Optional[str] = None,
        account_name: Optional[str] = None,
        time_window: Optional[str] = None,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        limit: Optional[int] = None,
        search_type: Optional[str] = None,
        cursor: Optional[str] = None,
        reposts: Optional[bool] = None,
    ) -> KeywordMentionsV2Response:
        path, params = build.keyword_mentions(
            keywords,
            account_name,
            time_window,
            from_time,
            to_time,
            limit,
            search_type,
            cursor,
            reposts,
        )
        return parse_model(KeywordMentionsV2Response, self._get(path, params))

    def get_token_news(
        self,
        *,
        time_window: Optional[str] = None,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        coin_ids: Optional[str] = None,
        reposts: Optional[bool] = None,
    ) -> TokenNewsV2Response:
        path, params = build.token_news(
            time_window, from_time, to_time, page, page_size, coin_ids, reposts
        )
        return parse_model(TokenNewsV2Response, self._get(path, params))

    def get_trending_cas_twitter(
        self,
        *,
        time_window: Optional[str] = None,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        min_mentions: Optional[int] = None,
    ) -> TrendingCAsV2Response:
        path, params = build.trending_cas(
            "twitter", time_window, from_time, to_time, page, page_size, min_mentions
        )
        return parse_model(TrendingCAsV2Response, self._get(path, params))

    def get_trending_cas_telegram(
        self,
        *,
        time_window: Optional[str] = None,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        min_mentions: Optional[int] = None,
    ) -> TrendingCAsV2Response:
        path, params = build.trending_cas(
            "telegram", time_window, from_time, to_time, page, page_size, min_mentions
        )
        return parse_model(TrendingCAsV2Response, self._get(path, params))

    def get_top_mentions(
        self,
        ticker: str,
        *,
        time_window: Optional[str] = None,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        reposts: Optional[bool] = None,
    ) -> TopMentionsV2Response:
        path, params = build.top_mentions(
            ticker, time_window, from_time, to_time, page, page_size, reposts
        )
        return parse_model(TopMentionsV2Response, self._get(path, params))

    def get_event_summary(
        self,
        keywords: str,
        *,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        time_window: Optional[str] = None,
        search_type: Optional[str] = None,
    ) -> EventSummaryV2Response:
        path, params = build.event_summary(
            keywords, from_time, to_time, time_window, search_type
        )
        return parse_model(EventSummaryV2Response, self._get(path, params))

    def get_trending_narratives(
        self,
        *,
        time_frame: Optional[str] = None,
        max_narratives: Optional[int] = None,
        max_tweets_per_narrative: Optional[int] = None,
    ) -> TrendingNarrativesResponse:
        path, params = build.trending_narratives(
            time_frame, max_narratives, max_tweets_per_narrative
        )
        return parse_model(TrendingNarrativesResponse, self._get(path, params))

    def chat(
        self,
        message: Optional[str] = None,
        *,
        session_id: Optional[str] = None,
        analysis_type: Optional[str] = None,
        speed: Optional[str] = None,
        asset_metadata: Optional[Dict[str, Any]] = None,
    ) -> ChatResponse:
        body = build.chat_body(
            message, session_id, analysis_type, speed, asset_metadata
        )
        data = self._transport.request_json(
            "POST", "/v2/chat", content=to_compact_json(body)
        )
        return parse_model(ChatResponse, data)
