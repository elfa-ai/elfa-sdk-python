"""
Aggregation and trending data models
"""

from typing import List, Literal

from pydantic import BaseModel, Field

from elfa.models.base import BaseResponse, PagePaginationMetadata


class TrendingToken(BaseModel):
    """Trending token information"""

    change_percent: float = Field(
        alias="change_percent", description="Percentage change"
    )
    previous_count: float = Field(
        alias="previous_count", description="Previous mention count"
    )
    current_count: float = Field(
        alias="current_count", description="Current mention count"
    )
    token: str = Field(..., description="Token symbol or name")


class TrendingTokensData(BaseModel):
    """Trending tokens response data"""

    page_size: float = Field(alias="pageSize", description="Number of items per page")
    page: float = Field(..., description="Current page number")
    total: float = Field(..., description="Total number of items")
    data: List[TrendingToken] = Field(..., description="List of trending tokens")


class TrendingTokensResponse(BaseResponse[TrendingTokensData]):
    """Response from the trending tokens endpoint"""

    success: bool = Field(..., description="Whether the request was successful")
    data: TrendingTokensData = Field(..., description="Trending tokens data")


class TrendingContractAddress(BaseModel):
    """Trending contract address information"""

    contract_address: str = Field(
        alias="contractAddress", description="Contract address"
    )
    chain: Literal["ethereum", "solana"] = Field(..., description="Blockchain chain")
    mention_count: float = Field(alias="mentionCount", description="Number of mentions")
    change_percent: float = Field(
        alias="changePercent", description="Percentage change"
    )


class TrendingCAsData(BaseModel):
    """Trending contract addresses response data"""

    page_size: float = Field(alias="pageSize", description="Number of items per page")
    page: float = Field(..., description="Current page number")
    total: float = Field(..., description="Total number of items")
    data: List[TrendingContractAddress] = Field(
        ..., description="List of trending contract addresses"
    )


class TrendingCAsV2Response(BaseResponse[TrendingCAsData]):
    """Response from the trending contract addresses endpoints"""

    success: bool = Field(..., description="Whether the request was successful")
    data: TrendingCAsData = Field(..., description="Trending contract addresses data")
