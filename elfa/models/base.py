"""
Base Pydantic models for Elfa API
"""

from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """Base response model for all Elfa API responses"""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    success: bool = Field(..., description="Whether the request was successful")
    data: T = Field(..., description="The response data")


class PaginationMetadata(BaseModel):
    """Base pagination metadata"""

    total: int = Field(..., description="Total number of items")


class OffsetPaginationMetadata(PaginationMetadata):
    """Offset-based pagination metadata"""

    offset: int = Field(..., description="Current offset")
    limit: int = Field(..., description="Number of items per page")


class PagePaginationMetadata(PaginationMetadata):
    """Page-based pagination metadata"""

    page: int = Field(..., description="Current page number")
    page_size: int = Field(alias="pageSize", description="Number of items per page")


class CursorPaginationMetadata(PaginationMetadata):
    """Cursor-based pagination metadata"""

    cursor: Optional[str] = Field(None, description="Cursor for next page")


class JsonValue(BaseModel):
    """Represents a generic JSON value"""

    model_config = ConfigDict(extra="allow")

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)
