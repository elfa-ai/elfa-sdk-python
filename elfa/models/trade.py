"""Models for direct trading (`/v2/trade/*`).

Order inputs are plain dicts sent verbatim as the (signed) request body, so their
keys are the camelCase field names the API expects. Sizes and prices are decimal
**strings** — never floats — to preserve precision and keep the signature stable.
"""

from typing import Optional

from pydantic import Field
from typing_extensions import Literal, NotRequired, TypedDict

from elfa.models.base import ElfaModel

TradeExchange = Literal["hyperliquid", "gmx"]
TradeOrderType = Literal["market", "limit"]
TradeSide = Literal["buy", "sell"]
MarginType = Literal["cross", "isolated"]


class PlaceOrderInput(TypedDict):
    exchange: TradeExchange
    symbol: str
    side: TradeSide
    orderType: TradeOrderType
    size: NotRequired[str]
    amount: NotRequired[str]
    positionSizePercent: NotRequired[float]
    price: NotRequired[str]
    leverage: NotRequired[float]
    marginType: NotRequired[MarginType]
    tp: NotRequired[str]
    sl: NotRequired[str]
    reduceOnly: NotRequired[bool]


class CancelOrderInput(TypedDict):
    exchange: TradeExchange
    symbol: str
    orderId: str


class ModifyOrderInput(TypedDict):
    exchange: TradeExchange
    symbol: str
    orderId: str
    size: NotRequired[str]
    price: NotRequired[str]
    triggerPrice: NotRequired[str]


class ClosePositionInput(TypedDict):
    exchange: TradeExchange
    symbol: str
    orderType: TradeOrderType
    size: NotRequired[str]
    amount: NotRequired[str]
    closePercent: NotRequired[float]
    price: NotRequired[str]


class SetPositionTpslInput(TypedDict):
    exchange: TradeExchange
    symbol: str
    tp: NotRequired[str]
    sl: NotRequired[str]
    size: NotRequired[str]


class TradeErrorDetail(ElfaModel):
    code: str
    message: str


class TradeResultResponse(ElfaModel):
    success: bool
    order_id: Optional[str] = Field(None, alias="orderId")
    filled_size: Optional[str] = Field(None, alias="filledSize")
    avg_fill_price: Optional[str] = Field(None, alias="avgFillPrice")
    error: Optional[TradeErrorDetail] = None


class TradePreviewResponse(ElfaModel):
    success: bool
    would_execute: bool = Field(alias="wouldExecute")
    error: Optional[TradeErrorDetail] = None
