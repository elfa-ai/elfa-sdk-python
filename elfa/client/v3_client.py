"""API v3 clients (`/v3/*`), sync and async.

Every route is a ``GET`` that authenticates with the API key alone. Times are
unix seconds; list parameters are sent comma-separated.
"""

from typing import Any, Dict, List, Optional

from elfa.client import _params as build
from elfa.client.base import parse_model
from elfa.exceptions import ElfaValidationError
from elfa.models.v3 import (
    AccountMetricV3,
    AlertActionV3,
    ArcSortV3,
    ArcsResponseV3,
    ArcStatusV3,
    CallBookResponseV3,
    CallDirectionV3,
    CallEpisodesResponseV3,
    CallsResponseV3,
    CallStatusV3,
    EntitiesResponseV3,
    EntityTypeV3,
    EventClassV3,
    EventSortV3,
    EventsResponseV3,
    EventTypeV3,
    ImplicationV3,
    KeyStatusV3,
    MarketV3,
    MindsharePeriodV3,
    MindshareResponseV3,
    NoveltyV3,
    OrderV3,
    PositioningResponseV3,
    StorylineRelationV3,
    StorylinesResponseV3,
    StorylineStatusV3,
    TopAccountsResponseV3,
    TrendingContractsResponseV3,
)
from elfa.utils.http import DEFAULT_BASE_URL, AsyncTransport, SyncTransport


class V3Client:
    """Synchronous API v3 client. Access via ``ElfaClient.v3``,
    or construct standalone with an ``api_key``."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        retries: int = 3,
        retry_delay: float = 1.0,
        headers: Optional[Dict[str, str]] = None,
        app_name: Optional[str] = None,
        transport: Optional[SyncTransport] = None,
    ):
        if transport is not None and app_name is not None:
            raise ElfaValidationError(
                "app_name cannot be combined with transport; set it on the "
                "client that creates the transport"
            )
        self._owns_transport = transport is None
        if transport is None:
            if not api_key:
                raise ElfaValidationError("api_key is required")
            transport = SyncTransport(
                api_key,
                base_url,
                timeout,
                retries,
                retry_delay,
                headers,
                app_name=app_name,
            )
        self._transport = transport

    def close(self) -> None:
        """Close the connection pool if this client owns it (standalone use)."""
        if self._owns_transport:
            self._transport.close()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._transport.request_json("GET", path, params=params)

    def get_entities(
        self,
        q: str,
        *,
        entity_type: Optional[List[EntityTypeV3]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> EntitiesResponseV3:
        path, params = build.v3_entities(q, entity_type, limit, cursor)
        return parse_model(EntitiesResponseV3, self._get(path, params))

    def get_events(
        self,
        *,
        q: Optional[str] = None,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        event_ids: Optional[List[str]] = None,
        event_class: Optional[EventClassV3] = None,
        event_type: Optional[EventTypeV3] = None,
        implication: Optional[ImplicationV3] = None,
        entity_ids: Optional[List[str]] = None,
        asset_class: Optional[MarketV3] = None,
        novelty: Optional[NoveltyV3] = None,
        alert_action: Optional[List[AlertActionV3]] = None,
        sort: Optional[EventSortV3] = None,
        has_storyline: Optional[bool] = None,
        arc_id: Optional[str] = None,
        notable: Optional[bool] = None,
        order: Optional[OrderV3] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> EventsResponseV3:
        path, params = build.v3_events(
            q,
            from_time,
            to_time,
            event_ids,
            event_class,
            event_type,
            implication,
            entity_ids,
            asset_class,
            novelty,
            alert_action,
            sort,
            has_storyline,
            arc_id,
            notable,
            order,
            limit,
            cursor,
        )
        return parse_model(EventsResponseV3, self._get(path, params))

    def get_storylines(
        self,
        *,
        q: Optional[str] = None,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        storyline_ids: Optional[List[str]] = None,
        entity_ids: Optional[List[str]] = None,
        status: Optional[StorylineStatusV3] = None,
        relation: Optional[List[StorylineRelationV3]] = None,
        order: Optional[OrderV3] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> StorylinesResponseV3:
        path, params = build.v3_storylines(
            q,
            from_time,
            to_time,
            storyline_ids,
            entity_ids,
            status,
            relation,
            order,
            limit,
            cursor,
        )
        return parse_model(StorylinesResponseV3, self._get(path, params))

    def get_arcs(
        self,
        *,
        q: Optional[str] = None,
        arc_ids: Optional[List[str]] = None,
        status: Optional[ArcStatusV3] = None,
        asset_class: Optional[MarketV3] = None,
        entity_ids: Optional[List[str]] = None,
        sort: Optional[ArcSortV3] = None,
        order: Optional[OrderV3] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> ArcsResponseV3:
        path, params = build.v3_arcs(
            q, arc_ids, status, asset_class, entity_ids, sort, order, limit, cursor
        )
        return parse_model(ArcsResponseV3, self._get(path, params))

    def get_call_book(
        self,
        market: MarketV3,
        *,
        from_time: int,
        to_time: Optional[int] = None,
        order: Optional[OrderV3] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> CallBookResponseV3:
        path, params = build.v3_call_book(
            market, from_time, to_time, order, limit, cursor
        )
        return parse_model(CallBookResponseV3, self._get(path, params))

    def get_mindshare(
        self,
        market: MarketV3,
        *,
        period: Optional[MindsharePeriodV3] = None,
        to_time: Optional[int] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> MindshareResponseV3:
        path, params = build.v3_mindshare(market, period, to_time, limit, cursor)
        return parse_model(MindshareResponseV3, self._get(path, params))

    def get_trending_contracts(
        self,
        *,
        from_time: int,
        to_time: Optional[int] = None,
        min_mentions: Optional[int] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> TrendingContractsResponseV3:
        path, params = build.v3_trending_contracts(
            from_time, to_time, min_mentions, limit, cursor
        )
        return parse_model(TrendingContractsResponseV3, self._get(path, params))

    def get_calls(
        self,
        *,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        call_ids: Optional[List[str]] = None,
        handle: Optional[str] = None,
        entity_ids: Optional[List[str]] = None,
        order: Optional[OrderV3] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> CallsResponseV3:
        path, params = build.v3_calls(
            from_time, to_time, call_ids, handle, entity_ids, order, limit, cursor
        )
        return parse_model(CallsResponseV3, self._get(path, params))

    def get_call_episodes(
        self,
        *,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        episode_ids: Optional[List[str]] = None,
        handle: Optional[str] = None,
        entity_ids: Optional[List[str]] = None,
        status: Optional[CallStatusV3] = None,
        direction: Optional[CallDirectionV3] = None,
        asset_class: Optional[MarketV3] = None,
        order: Optional[OrderV3] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> CallEpisodesResponseV3:
        path, params = build.v3_call_episodes(
            from_time,
            to_time,
            episode_ids,
            handle,
            entity_ids,
            status,
            direction,
            asset_class,
            order,
            limit,
            cursor,
        )
        return parse_model(CallEpisodesResponseV3, self._get(path, params))

    def get_positioning(self, entity_id: str) -> PositioningResponseV3:
        path, params = build.v3_positioning(entity_id)
        return parse_model(PositioningResponseV3, self._get(path, params))

    def get_top_accounts(
        self,
        *,
        metric: Optional[AccountMetricV3] = None,
        order: Optional[OrderV3] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> TopAccountsResponseV3:
        path, params = build.v3_top_accounts(metric, order, limit, cursor)
        return parse_model(TopAccountsResponseV3, self._get(path, params))

    def get_key_status(self) -> KeyStatusV3:
        return parse_model(KeyStatusV3, self._get("/v3/key-status"))


class AsyncV3Client:
    """Asynchronous API v3 client. Access via ``AsyncElfaClient.v3``,
    or construct standalone with an ``api_key``."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        retries: int = 3,
        retry_delay: float = 1.0,
        headers: Optional[Dict[str, str]] = None,
        app_name: Optional[str] = None,
        transport: Optional[AsyncTransport] = None,
    ):
        if transport is not None and app_name is not None:
            raise ElfaValidationError(
                "app_name cannot be combined with transport; set it on the "
                "client that creates the transport"
            )
        self._owns_transport = transport is None
        if transport is None:
            if not api_key:
                raise ElfaValidationError("api_key is required")
            transport = AsyncTransport(
                api_key,
                base_url,
                timeout,
                retries,
                retry_delay,
                headers,
                app_name=app_name,
            )
        self._transport = transport

    async def close(self) -> None:
        """Close the connection pool if this client owns it (standalone use)."""
        if self._owns_transport:
            await self._transport.close()

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return await self._transport.request_json("GET", path, params=params)

    async def get_entities(
        self,
        q: str,
        *,
        entity_type: Optional[List[EntityTypeV3]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> EntitiesResponseV3:
        path, params = build.v3_entities(q, entity_type, limit, cursor)
        return parse_model(EntitiesResponseV3, await self._get(path, params))

    async def get_events(
        self,
        *,
        q: Optional[str] = None,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        event_ids: Optional[List[str]] = None,
        event_class: Optional[EventClassV3] = None,
        event_type: Optional[EventTypeV3] = None,
        implication: Optional[ImplicationV3] = None,
        entity_ids: Optional[List[str]] = None,
        asset_class: Optional[MarketV3] = None,
        novelty: Optional[NoveltyV3] = None,
        alert_action: Optional[List[AlertActionV3]] = None,
        sort: Optional[EventSortV3] = None,
        has_storyline: Optional[bool] = None,
        arc_id: Optional[str] = None,
        notable: Optional[bool] = None,
        order: Optional[OrderV3] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> EventsResponseV3:
        path, params = build.v3_events(
            q,
            from_time,
            to_time,
            event_ids,
            event_class,
            event_type,
            implication,
            entity_ids,
            asset_class,
            novelty,
            alert_action,
            sort,
            has_storyline,
            arc_id,
            notable,
            order,
            limit,
            cursor,
        )
        return parse_model(EventsResponseV3, await self._get(path, params))

    async def get_storylines(
        self,
        *,
        q: Optional[str] = None,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        storyline_ids: Optional[List[str]] = None,
        entity_ids: Optional[List[str]] = None,
        status: Optional[StorylineStatusV3] = None,
        relation: Optional[List[StorylineRelationV3]] = None,
        order: Optional[OrderV3] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> StorylinesResponseV3:
        path, params = build.v3_storylines(
            q,
            from_time,
            to_time,
            storyline_ids,
            entity_ids,
            status,
            relation,
            order,
            limit,
            cursor,
        )
        return parse_model(StorylinesResponseV3, await self._get(path, params))

    async def get_arcs(
        self,
        *,
        q: Optional[str] = None,
        arc_ids: Optional[List[str]] = None,
        status: Optional[ArcStatusV3] = None,
        asset_class: Optional[MarketV3] = None,
        entity_ids: Optional[List[str]] = None,
        sort: Optional[ArcSortV3] = None,
        order: Optional[OrderV3] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> ArcsResponseV3:
        path, params = build.v3_arcs(
            q, arc_ids, status, asset_class, entity_ids, sort, order, limit, cursor
        )
        return parse_model(ArcsResponseV3, await self._get(path, params))

    async def get_call_book(
        self,
        market: MarketV3,
        *,
        from_time: int,
        to_time: Optional[int] = None,
        order: Optional[OrderV3] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> CallBookResponseV3:
        path, params = build.v3_call_book(
            market, from_time, to_time, order, limit, cursor
        )
        return parse_model(CallBookResponseV3, await self._get(path, params))

    async def get_mindshare(
        self,
        market: MarketV3,
        *,
        period: Optional[MindsharePeriodV3] = None,
        to_time: Optional[int] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> MindshareResponseV3:
        path, params = build.v3_mindshare(market, period, to_time, limit, cursor)
        return parse_model(MindshareResponseV3, await self._get(path, params))

    async def get_trending_contracts(
        self,
        *,
        from_time: int,
        to_time: Optional[int] = None,
        min_mentions: Optional[int] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> TrendingContractsResponseV3:
        path, params = build.v3_trending_contracts(
            from_time, to_time, min_mentions, limit, cursor
        )
        return parse_model(TrendingContractsResponseV3, await self._get(path, params))

    async def get_calls(
        self,
        *,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        call_ids: Optional[List[str]] = None,
        handle: Optional[str] = None,
        entity_ids: Optional[List[str]] = None,
        order: Optional[OrderV3] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> CallsResponseV3:
        path, params = build.v3_calls(
            from_time, to_time, call_ids, handle, entity_ids, order, limit, cursor
        )
        return parse_model(CallsResponseV3, await self._get(path, params))

    async def get_call_episodes(
        self,
        *,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        episode_ids: Optional[List[str]] = None,
        handle: Optional[str] = None,
        entity_ids: Optional[List[str]] = None,
        status: Optional[CallStatusV3] = None,
        direction: Optional[CallDirectionV3] = None,
        asset_class: Optional[MarketV3] = None,
        order: Optional[OrderV3] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> CallEpisodesResponseV3:
        path, params = build.v3_call_episodes(
            from_time,
            to_time,
            episode_ids,
            handle,
            entity_ids,
            status,
            direction,
            asset_class,
            order,
            limit,
            cursor,
        )
        return parse_model(CallEpisodesResponseV3, await self._get(path, params))

    async def get_positioning(self, entity_id: str) -> PositioningResponseV3:
        path, params = build.v3_positioning(entity_id)
        return parse_model(PositioningResponseV3, await self._get(path, params))

    async def get_top_accounts(
        self,
        *,
        metric: Optional[AccountMetricV3] = None,
        order: Optional[OrderV3] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> TopAccountsResponseV3:
        path, params = build.v3_top_accounts(metric, order, limit, cursor)
        return parse_model(TopAccountsResponseV3, await self._get(path, params))

    async def get_key_status(self) -> KeyStatusV3:
        return parse_model(KeyStatusV3, await self._get("/v3/key-status"))
