"""Asynchronous Elfa client: core data + AI chat, with ``.auto``."""

from typing import Any, AsyncIterator, Dict, Optional

from elfa.client import _params as build
from elfa.client.auto_client import AsyncAutoClient
from elfa.client.base import chat_stream_event, parse_model
from elfa.exceptions import ElfaAPIError, ElfaValidationError
from elfa.models.chat import (
    ChatAnalysisType,
    ChatAssetMetadata,
    ChatResponse,
    ChatSpeed,
    ChatStreamEvent,
)
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
from elfa.utils.http import DEFAULT_BASE_URL, AsyncTransport
from elfa.utils.serialize import to_compact_json
from elfa.utils.sse import SSE_HEADERS, aiter_sse


class AsyncElfaClient:
    """Asynchronous client for the Elfa API. Mirrors :class:`ElfaClient`.

    Example:
        >>> import asyncio
        >>> from elfa import AsyncElfaClient
        >>> async def main():
        ...     async with AsyncElfaClient(api_key="your-api-key") as client:
        ...         stats = await client.get_account_smart_stats("elonmusk")
        ...         print(stats.data.smart_following_count)
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        retries: int = 3,
        retry_delay: float = 1.0,
        headers: Optional[Dict[str, str]] = None,
    ):
        if not api_key:
            raise ElfaValidationError("api_key is required")

        self._transport = AsyncTransport(
            api_key, base_url, timeout, retries, retry_delay, headers
        )
        self.auto = AsyncAutoClient(transport=self._transport)

    async def __aenter__(self) -> "AsyncElfaClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._transport.close()

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return await self._transport.request_json("GET", path, params=params)

    async def ping(self) -> PingResponse:
        return parse_model(PingResponse, await self._get("/v2/ping"))

    async def get_api_key_status(self) -> ApiKeyStatusResponse:
        return parse_model(ApiKeyStatusResponse, await self._get("/v2/key-status"))

    async def test_connection(self) -> bool:
        """Return True if the API is reachable and the key is accepted."""
        try:
            return (await self.ping()).success is True
        except ElfaAPIError:
            return False

    async def get_trending_tokens(
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
        return parse_model(TrendingTokensResponse, await self._get(path, params))

    async def get_account_smart_stats(self, username: str) -> AccountSmartStatsResponse:
        """Smart follower and engagement metrics for an X account.

        .. deprecated::
            ``GET /v2/account/smart-stats`` is legacy and is removed on
            28 October 2026. It returns raw account metrics, not a reputation
            score, and is not being extended. Rank on the account context
            returned by :meth:`get_keyword_mentions` instead.
        """
        path, params = build.account_smart_stats(username)
        return parse_model(AccountSmartStatsResponse, await self._get(path, params))

    async def get_keyword_mentions(
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
        return parse_model(KeywordMentionsV2Response, await self._get(path, params))

    async def get_token_news(
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
        return parse_model(TokenNewsV2Response, await self._get(path, params))

    async def get_trending_cas_twitter(
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
        return parse_model(TrendingCAsV2Response, await self._get(path, params))

    async def get_trending_cas_telegram(
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
        return parse_model(TrendingCAsV2Response, await self._get(path, params))

    async def get_top_mentions(
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
        return parse_model(TopMentionsV2Response, await self._get(path, params))

    async def get_event_summary(
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
        return parse_model(EventSummaryV2Response, await self._get(path, params))

    async def get_trending_narratives(
        self,
        *,
        time_frame: Optional[str] = None,
        max_narratives: Optional[int] = None,
        max_tweets_per_narrative: Optional[int] = None,
    ) -> TrendingNarrativesResponse:
        path, params = build.trending_narratives(
            time_frame, max_narratives, max_tweets_per_narrative
        )
        return parse_model(TrendingNarrativesResponse, await self._get(path, params))

    async def chat(
        self,
        message: Optional[str] = None,
        *,
        session_id: Optional[str] = None,
        analysis_type: Optional[ChatAnalysisType] = None,
        speed: Optional[ChatSpeed] = None,
        asset_metadata: Optional[ChatAssetMetadata] = None,
    ) -> ChatResponse:
        body = build.chat_body(
            message, session_id, analysis_type, speed, asset_metadata
        )
        data = await self._transport.request_json(
            "POST", "/v2/chat", content=to_compact_json(body)
        )
        return parse_model(ChatResponse, data)

    async def chat_stream(
        self,
        message: Optional[str] = None,
        *,
        session_id: Optional[str] = None,
        analysis_type: Optional[ChatAnalysisType] = None,
        speed: Optional[ChatSpeed] = None,
        asset_metadata: Optional[ChatAssetMetadata] = None,
    ) -> AsyncIterator[ChatStreamEvent]:
        """Stream a chat answer as SSE. Requires a PAYG or Enterprise API key."""
        body = build.chat_body(
            message, session_id, analysis_type, speed, asset_metadata
        )
        async with self._transport.stream_lines(
            "POST",
            "/v2/chat/stream",
            headers=SSE_HEADERS,
            content=to_compact_json(body),
        ) as lines:
            async for frame in aiter_sse(lines):
                if frame.data == "[DONE]":
                    return
                event = chat_stream_event(frame)
                if event is not None:
                    yield event
