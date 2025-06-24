"""
Common models used across multiple endpoints
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from elfa.models.base import BaseResponse


class PingResponse(BaseResponse[dict]):
    """Response from the ping endpoint"""

    success: Literal[True] = Field(True, description="Always true for ping")
    data: dict = Field(..., description="Ping response data")

    class Data(BaseModel):
        message: str = Field(..., description="Ping message")


class BasicCoin(BaseModel):
    """Basic coin information"""

    name: str = Field(..., description="Coin name")
    symbol: str = Field(..., description="Coin symbol")
    coin_id: str = Field(alias="coinId", description="Coin ID")


class Chain(str, Enum):
    """Supported blockchain chains"""

    ETHEREUM = "ethereum"
    SOLANA = "solana"


class MentionedByType(str, Enum):
    """Types of mention sources"""

    GENERAL = "general"
    CT = "ct"
    SMART = "smart"


class SentimentType(str, Enum):
    """Sentiment analysis results"""

    VERY_BULLISH = "very-bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    VERY_BEARISH = "very-bearish"
