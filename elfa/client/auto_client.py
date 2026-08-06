"""Auto condition engine clients (`/v2/auto/*`), sync and async.

Mutations are HMAC-signed when an ``hmac_secret`` is configured (required for
trade-action queries and all exchange writes; harmless for notification-only
queries). Notification streams are exposed as generators over SSE.
"""

from typing import Any, AsyncIterator, Dict, Iterator, Optional
from urllib.parse import quote

from elfa.client.base import SignedClient, drop_none, parse_model, stream_event
from elfa.exceptions import ElfaValidationError
from elfa.models.auto import (
    AutoChatResponse,
    AutoConvertDraftResponse,
    AutoDraft,
    AutoExchangeConnection,
    AutoExecution,
    AutoListDraftsResponse,
    AutoListExchangesResponse,
    AutoListExecutionsResponse,
    AutoListQueriesResponse,
    AutoListSessionsResponse,
    AutoPollQueryResponse,
    AutoQuery,
    AutoSession,
    AutoSpeed,
    AutoStreamEvent,
    AutoSuccessResponse,
    AutoValidateResponse,
    AutoValidateSymbolResponse,
    TradableExchange,
)
from elfa.utils.http import DEFAULT_BASE_URL, AsyncTransport, SyncTransport
from elfa.utils.sse import SSE_HEADERS, aiter_sse, iter_sse

MOUNT = "/v2/auto"


class AutoClient(SignedClient):
    """Synchronous Auto engine client. Access via ``ElfaClient.auto``,
    or construct standalone with an ``api_key``."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        retries: int = 3,
        retry_delay: float = 1.0,
        hmac_secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        transport: Optional[SyncTransport] = None,
    ):
        self._owns_transport = transport is None
        if transport is None:
            if not api_key:
                raise ElfaValidationError("api_key is required")
            transport = SyncTransport(
                api_key, base_url, timeout, retries, retry_delay, headers
            )
        super().__init__(transport, MOUNT, hmac_secret)

    def close(self) -> None:
        """Close the connection pool if this client owns it (standalone use)."""
        if self._owns_transport:
            self._transport.close()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._transport.request_json("GET", f"{MOUNT}{path}", params=params)

    def _post(self, path: str, body: Any = None) -> Any:
        url, content, headers = self._post_args(path, body)
        return self._transport.request_json(
            "POST", url, content=content, headers=headers
        )

    def _delete(self, path: str) -> Any:
        url, headers = self._delete_args(path)
        return self._transport.request_json("DELETE", url, headers=headers)

    def chat(
        self,
        message: str,
        *,
        speed: Optional[AutoSpeed] = None,
        session_id: Optional[str] = None,
    ) -> AutoChatResponse:
        body = drop_none({"message": message, "speed": speed, "sessionId": session_id})
        return parse_model(AutoChatResponse, self._post("/chat", body))

    def validate_query(self, query_input: Dict[str, Any]) -> AutoValidateResponse:
        return parse_model(
            AutoValidateResponse, self._post("/queries/validate", query_input)
        )

    def create_query(self, query_input: Dict[str, Any]) -> AutoQuery:
        return parse_model(AutoQuery, self._post("/queries", query_input))

    def list_queries(
        self,
        *,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> AutoListQueriesResponse:
        params = drop_none(
            {"status": status, "search": search, "limit": limit, "offset": offset}
        )
        return parse_model(AutoListQueriesResponse, self._get("/queries", params))

    def get_query(self, query_id: str) -> AutoPollQueryResponse:
        return parse_model(AutoPollQueryResponse, self._get(f"/queries/{query_id}"))

    def cancel_query(self, query_id: str) -> AutoQuery:
        return parse_model(AutoQuery, self._post(f"/queries/{query_id}/cancel"))

    def delete_query(self, query_id: str) -> AutoQuery:
        return parse_model(AutoQuery, self._delete(f"/queries/{query_id}"))

    def list_drafts(
        self,
        *,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> AutoListDraftsResponse:
        params = drop_none(
            {"status": status, "search": search, "limit": limit, "offset": offset}
        )
        return parse_model(AutoListDraftsResponse, self._get("/queries/drafts", params))

    def get_draft(self, draft_id: str) -> AutoDraft:
        return parse_model(AutoDraft, self._get(f"/queries/drafts/{draft_id}"))

    def upsert_draft(self, draft_input: Dict[str, Any]) -> AutoDraft:
        return parse_model(AutoDraft, self._post("/queries/drafts", draft_input))

    def delete_draft(self, draft_id: str) -> Any:
        return self._delete(f"/queries/drafts/{draft_id}")

    def validate_draft(self, draft_id: str) -> AutoValidateResponse:
        return parse_model(
            AutoValidateResponse, self._post(f"/queries/drafts/{draft_id}/validate")
        )

    def convert_draft(self, draft_id: str) -> AutoConvertDraftResponse:
        return parse_model(
            AutoConvertDraftResponse,
            self._post(f"/queries/drafts/{draft_id}/convert"),
        )

    def list_sessions(self, query_id: str) -> AutoListSessionsResponse:
        return parse_model(
            AutoListSessionsResponse, self._get(f"/queries/{query_id}/sessions")
        )

    def get_session(self, query_id: str, session_id: str) -> AutoSession:
        return parse_model(
            AutoSession, self._get(f"/queries/{query_id}/sessions/{session_id}")
        )

    def list_executions(
        self,
        *,
        query_id: Optional[str] = None,
        status: Optional[str] = None,
        execution_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> AutoListExecutionsResponse:
        params = drop_none(
            {
                "queryId": query_id,
                "status": status,
                "type": execution_type,
                "limit": limit,
                "offset": offset,
            }
        )
        return parse_model(AutoListExecutionsResponse, self._get("/executions", params))

    def get_execution(self, execution_id: str) -> AutoExecution:
        return parse_model(AutoExecution, self._get(f"/executions/{execution_id}"))

    def list_exchanges(self) -> AutoListExchangesResponse:
        return parse_model(AutoListExchangesResponse, self._get("/exchanges"))

    def connect_exchange(
        self, exchange_input: Dict[str, Any]
    ) -> AutoExchangeConnection:
        return parse_model(
            AutoExchangeConnection, self._post("/exchanges", exchange_input)
        )

    def disconnect_exchange(self, exchange: TradableExchange) -> AutoSuccessResponse:
        return parse_model(AutoSuccessResponse, self._delete(f"/exchanges/{exchange}"))

    def validate_symbol(
        self, exchange: TradableExchange, symbol: str
    ) -> AutoValidateSymbolResponse:
        path = f"/validate-symbol/{exchange}/{quote(symbol, safe='')}"
        return parse_model(AutoValidateSymbolResponse, self._get(path))

    def stream_query(self, query_id: str) -> Iterator[AutoStreamEvent]:
        return self._stream(f"/queries/{query_id}/stream")

    def stream_all(self) -> Iterator[AutoStreamEvent]:
        return self._stream("/queries/stream")

    def _stream(self, path: str) -> Iterator[AutoStreamEvent]:
        with self._transport.stream_lines(
            "GET", f"{MOUNT}{path}", headers=SSE_HEADERS
        ) as lines:
            for message in iter_sse(lines):
                yield stream_event(message)
                if message.event == "end":
                    return


class AsyncAutoClient(SignedClient):
    """Asynchronous Auto engine client. Access via ``AsyncElfaClient.auto``,
    or construct standalone with an ``api_key``."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        retries: int = 3,
        retry_delay: float = 1.0,
        hmac_secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        transport: Optional[AsyncTransport] = None,
    ):
        self._owns_transport = transport is None
        if transport is None:
            if not api_key:
                raise ElfaValidationError("api_key is required")
            transport = AsyncTransport(
                api_key, base_url, timeout, retries, retry_delay, headers
            )
        super().__init__(transport, MOUNT, hmac_secret)

    async def close(self) -> None:
        """Close the connection pool if this client owns it (standalone use)."""
        if self._owns_transport:
            await self._transport.close()

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return await self._transport.request_json(
            "GET", f"{MOUNT}{path}", params=params
        )

    async def _post(self, path: str, body: Any = None) -> Any:
        url, content, headers = self._post_args(path, body)
        return await self._transport.request_json(
            "POST", url, content=content, headers=headers
        )

    async def _delete(self, path: str) -> Any:
        url, headers = self._delete_args(path)
        return await self._transport.request_json("DELETE", url, headers=headers)

    async def chat(
        self,
        message: str,
        *,
        speed: Optional[AutoSpeed] = None,
        session_id: Optional[str] = None,
    ) -> AutoChatResponse:
        body = drop_none({"message": message, "speed": speed, "sessionId": session_id})
        return parse_model(AutoChatResponse, await self._post("/chat", body))

    async def validate_query(self, query_input: Dict[str, Any]) -> AutoValidateResponse:
        return parse_model(
            AutoValidateResponse, await self._post("/queries/validate", query_input)
        )

    async def create_query(self, query_input: Dict[str, Any]) -> AutoQuery:
        return parse_model(AutoQuery, await self._post("/queries", query_input))

    async def list_queries(
        self,
        *,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> AutoListQueriesResponse:
        params = drop_none(
            {"status": status, "search": search, "limit": limit, "offset": offset}
        )
        return parse_model(AutoListQueriesResponse, await self._get("/queries", params))

    async def get_query(self, query_id: str) -> AutoPollQueryResponse:
        return parse_model(
            AutoPollQueryResponse, await self._get(f"/queries/{query_id}")
        )

    async def cancel_query(self, query_id: str) -> AutoQuery:
        return parse_model(AutoQuery, await self._post(f"/queries/{query_id}/cancel"))

    async def delete_query(self, query_id: str) -> AutoQuery:
        return parse_model(AutoQuery, await self._delete(f"/queries/{query_id}"))

    async def list_drafts(
        self,
        *,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> AutoListDraftsResponse:
        params = drop_none(
            {"status": status, "search": search, "limit": limit, "offset": offset}
        )
        return parse_model(
            AutoListDraftsResponse, await self._get("/queries/drafts", params)
        )

    async def get_draft(self, draft_id: str) -> AutoDraft:
        return parse_model(AutoDraft, await self._get(f"/queries/drafts/{draft_id}"))

    async def upsert_draft(self, draft_input: Dict[str, Any]) -> AutoDraft:
        return parse_model(AutoDraft, await self._post("/queries/drafts", draft_input))

    async def delete_draft(self, draft_id: str) -> Any:
        return await self._delete(f"/queries/drafts/{draft_id}")

    async def validate_draft(self, draft_id: str) -> AutoValidateResponse:
        return parse_model(
            AutoValidateResponse,
            await self._post(f"/queries/drafts/{draft_id}/validate"),
        )

    async def convert_draft(self, draft_id: str) -> AutoConvertDraftResponse:
        return parse_model(
            AutoConvertDraftResponse,
            await self._post(f"/queries/drafts/{draft_id}/convert"),
        )

    async def list_sessions(self, query_id: str) -> AutoListSessionsResponse:
        return parse_model(
            AutoListSessionsResponse, await self._get(f"/queries/{query_id}/sessions")
        )

    async def get_session(self, query_id: str, session_id: str) -> AutoSession:
        return parse_model(
            AutoSession, await self._get(f"/queries/{query_id}/sessions/{session_id}")
        )

    async def list_executions(
        self,
        *,
        query_id: Optional[str] = None,
        status: Optional[str] = None,
        execution_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> AutoListExecutionsResponse:
        params = drop_none(
            {
                "queryId": query_id,
                "status": status,
                "type": execution_type,
                "limit": limit,
                "offset": offset,
            }
        )
        return parse_model(
            AutoListExecutionsResponse, await self._get("/executions", params)
        )

    async def get_execution(self, execution_id: str) -> AutoExecution:
        return parse_model(
            AutoExecution, await self._get(f"/executions/{execution_id}")
        )

    async def list_exchanges(self) -> AutoListExchangesResponse:
        return parse_model(AutoListExchangesResponse, await self._get("/exchanges"))

    async def connect_exchange(
        self, exchange_input: Dict[str, Any]
    ) -> AutoExchangeConnection:
        return parse_model(
            AutoExchangeConnection, await self._post("/exchanges", exchange_input)
        )

    async def disconnect_exchange(
        self, exchange: TradableExchange
    ) -> AutoSuccessResponse:
        return parse_model(
            AutoSuccessResponse, await self._delete(f"/exchanges/{exchange}")
        )

    async def validate_symbol(
        self, exchange: TradableExchange, symbol: str
    ) -> AutoValidateSymbolResponse:
        path = f"/validate-symbol/{exchange}/{quote(symbol, safe='')}"
        return parse_model(AutoValidateSymbolResponse, await self._get(path))

    def stream_query(self, query_id: str) -> AsyncIterator[AutoStreamEvent]:
        return self._stream(f"/queries/{query_id}/stream")

    def stream_all(self) -> AsyncIterator[AutoStreamEvent]:
        return self._stream("/queries/stream")

    async def _stream(self, path: str) -> AsyncIterator[AutoStreamEvent]:
        async with self._transport.stream_lines(
            "GET", f"{MOUNT}{path}", headers=SSE_HEADERS
        ) as lines:
            async for message in aiter_sse(lines):
                yield stream_event(message)
                if message.event == "end":
                    return
