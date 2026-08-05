"""Direct trading clients (`/v2/trade/*`), sync and async.

All writes are HMAC-signed when an ``hmac_secret`` is configured (required by the
server for order/position writes; previews are signed too, which is harmless).
Order inputs are dicts serialized verbatim as the signed body.
"""

from typing import Any, Dict, Optional

from elfa.client.base import SignedClient, parse_model
from elfa.exceptions import ElfaValidationError
from elfa.models.trade import (
    CancelOrderInput,
    ClosePositionInput,
    ModifyOrderInput,
    PlaceOrderInput,
    SetPositionTpslInput,
    TradePreviewResponse,
    TradeResultResponse,
)
from elfa.utils.http import DEFAULT_BASE_URL, AsyncTransport, SyncTransport

MOUNT = "/v2/trade"


class TradeClient(SignedClient):
    """Synchronous trading client. Access via ``ElfaClient.trade``,
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

    def _post(self, path: str, body: Any) -> Any:
        url, content, headers = self._post_args(path, body)
        return self._transport.request_json(
            "POST", url, content=content, headers=headers
        )

    def preview_order(self, order: PlaceOrderInput) -> TradePreviewResponse:
        return parse_model(TradePreviewResponse, self._post("/orders/preview", order))

    def place_order(self, order: PlaceOrderInput) -> TradeResultResponse:
        return parse_model(TradeResultResponse, self._post("/orders", order))

    def cancel_order(self, order: CancelOrderInput) -> TradeResultResponse:
        return parse_model(TradeResultResponse, self._post("/orders/cancel", order))

    def modify_order(self, order: ModifyOrderInput) -> TradeResultResponse:
        return parse_model(TradeResultResponse, self._post("/orders/modify", order))

    def preview_close_position(
        self, position: ClosePositionInput
    ) -> TradePreviewResponse:
        return parse_model(
            TradePreviewResponse, self._post("/positions/close/preview", position)
        )

    def close_position(self, position: ClosePositionInput) -> TradeResultResponse:
        return parse_model(
            TradeResultResponse, self._post("/positions/close", position)
        )

    def preview_set_position_tpsl(
        self, position: SetPositionTpslInput
    ) -> TradePreviewResponse:
        return parse_model(
            TradePreviewResponse, self._post("/positions/tpsl/preview", position)
        )

    def set_position_tpsl(self, position: SetPositionTpslInput) -> TradeResultResponse:
        return parse_model(TradeResultResponse, self._post("/positions/tpsl", position))


class AsyncTradeClient(SignedClient):
    """Asynchronous trading client. Access via ``AsyncElfaClient.trade``,
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

    async def _post(self, path: str, body: Any) -> Any:
        url, content, headers = self._post_args(path, body)
        return await self._transport.request_json(
            "POST", url, content=content, headers=headers
        )

    async def preview_order(self, order: PlaceOrderInput) -> TradePreviewResponse:
        return parse_model(
            TradePreviewResponse, await self._post("/orders/preview", order)
        )

    async def place_order(self, order: PlaceOrderInput) -> TradeResultResponse:
        return parse_model(TradeResultResponse, await self._post("/orders", order))

    async def cancel_order(self, order: CancelOrderInput) -> TradeResultResponse:
        return parse_model(
            TradeResultResponse, await self._post("/orders/cancel", order)
        )

    async def modify_order(self, order: ModifyOrderInput) -> TradeResultResponse:
        return parse_model(
            TradeResultResponse, await self._post("/orders/modify", order)
        )

    async def preview_close_position(
        self, position: ClosePositionInput
    ) -> TradePreviewResponse:
        return parse_model(
            TradePreviewResponse,
            await self._post("/positions/close/preview", position),
        )

    async def close_position(self, position: ClosePositionInput) -> TradeResultResponse:
        return parse_model(
            TradeResultResponse, await self._post("/positions/close", position)
        )

    async def preview_set_position_tpsl(
        self, position: SetPositionTpslInput
    ) -> TradePreviewResponse:
        return parse_model(
            TradePreviewResponse,
            await self._post("/positions/tpsl/preview", position),
        )

    async def set_position_tpsl(
        self, position: SetPositionTpslInput
    ) -> TradeResultResponse:
        return parse_model(
            TradeResultResponse, await self._post("/positions/tpsl", position)
        )
