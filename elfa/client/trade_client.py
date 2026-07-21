"""Direct trading clients (`/v2/trade/*`), sync and async.

All writes are HMAC-signed when an ``hmac_secret`` is configured (required by the
server for order/position writes; previews are signed too, which is harmless).
Order inputs are dicts serialized verbatim as the signed body.
"""

from typing import Any, Optional

from elfa.client.base import SignedClient, parse_model
from elfa.models.trade import (
    CancelOrderInput,
    ClosePositionInput,
    ModifyOrderInput,
    PlaceOrderInput,
    SetPositionTpslInput,
    TradePreviewResponse,
    TradeResultResponse,
)

MOUNT = "/v2/trade"


class TradeClient(SignedClient):
    """Synchronous trading client. Access via ``ElfaClient.trade``."""

    def __init__(self, transport: Any, hmac_secret: Optional[str] = None):
        super().__init__(transport, MOUNT, hmac_secret)

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
    """Asynchronous trading client. Access via ``AsyncElfaClient.trade``."""

    def __init__(self, transport: Any, hmac_secret: Optional[str] = None):
        super().__init__(transport, MOUNT, hmac_secret)

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
