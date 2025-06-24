"""
Mention and search result models
"""

from datetime import datetime
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field

from elfa.models.accounts import Account, AccountInfo, BasicAccount
from elfa.models.base import (
    BaseResponse,
    CursorPaginationMetadata,
    JsonValue,
    OffsetPaginationMetadata,
    PagePaginationMetadata,
)
from elfa.models.common import BasicCoin, MentionedByType, SentimentType


class MentionAccount(BaseModel):
    """Account information in mentions"""

    is_verified: bool = Field(
        alias="isVerified", description="Whether account is verified"
    )
    username: str = Field(..., description="Username")


class SanitizedMention(BaseModel):
    """Sanitized mention data from V2 API without raw content"""

    tweet_id: str = Field(alias="tweetId", description="Tweet ID")
    link: str = Field(..., description="Link to the tweet")
    like_count: Optional[float] = Field(
        alias="likeCount", description="Number of likes"
    )
    repost_count: Optional[float] = Field(
        alias="repostCount", description="Number of reposts"
    )
    view_count: Optional[float] = Field(
        alias="viewCount", description="Number of views"
    )
    quote_count: Optional[float] = Field(
        alias="quoteCount", description="Number of quotes"
    )
    reply_count: Optional[float] = Field(
        alias="replyCount", description="Number of replies"
    )
    bookmark_count: Optional[float] = Field(
        alias="bookmarkCount", description="Number of bookmarks"
    )
    mentioned_at: str = Field(
        alias="mentionedAt", description="When the mention occurred"
    )
    account: Optional[MentionAccount] = Field(None, description="Account information")


# Keep V2Mention as alias for backward compatibility
V2Mention = SanitizedMention


class KeywordMentionsV2Response(BaseResponse[List[SanitizedMention]]):
    """Response from the V2 keyword mentions endpoint"""

    success: bool = Field(..., description="Whether the request was successful")
    data: List[SanitizedMention] = Field(..., description="List of mentions")
    metadata: CursorPaginationMetadata = Field(..., description="Pagination metadata")


class TokenNewsV2Response(BaseResponse[List[SanitizedMention]]):
    """Response from the V2 token news endpoint"""

    success: bool = Field(..., description="Whether the request was successful")
    data: List[SanitizedMention] = Field(..., description="List of news mentions")
    metadata: PagePaginationMetadata = Field(..., description="Pagination metadata")


class Mention(BaseModel):
    """Full mention data from V1 API"""

    id: Union[float, str] = Field(..., description="Mention ID")
    type: str = Field(..., description="Mention type")
    content: Optional[str] = Field(None, description="Tweet content")
    original_url: str = Field(alias="originalUrl", description="Original tweet URL")
    data: JsonValue = Field(..., description="Additional mention data")
    like_count: Optional[float] = Field(
        alias="likeCount", description="Number of likes"
    )
    quote_count: Optional[float] = Field(
        alias="quoteCount", description="Number of quotes"
    )
    reply_count: Optional[float] = Field(
        alias="replyCount", description="Number of replies"
    )
    repost_count: Optional[float] = Field(
        alias="repostCount", description="Number of reposts"
    )
    view_count: Optional[float] = Field(
        alias="viewCount", description="Number of views"
    )
    mentioned_at: datetime = Field(alias="mentionedAt", description="When mentioned")
    bookmark_count: Optional[float] = Field(
        alias="bookmarkCount", description="Number of bookmarks"
    )
    account: Optional[Account] = Field(None, description="Account information")


class MentionResponse(BaseResponse[List[Mention]]):
    """Response from the V1 mentions endpoint"""

    success: bool = Field(..., description="Whether the request was successful")
    data: List[Mention] = Field(..., description="List of mentions")
    metadata: OffsetPaginationMetadata = Field(..., description="Pagination metadata")


class Metrics(BaseModel):
    """Tweet metrics"""

    view_count: float = Field(alias="view_count", description="Number of views")
    repost_count: float = Field(alias="repost_count", description="Number of reposts")
    reply_count: float = Field(alias="reply_count", description="Number of replies")
    like_count: float = Field(alias="like_count", description="Number of likes")


class SimpleMention(BaseModel):
    """Simple mention format"""

    id: float = Field(..., description="Mention ID")
    twitter_id: str = Field(alias="twitter_id", description="Twitter ID")
    twitter_user_id: str = Field(alias="twitter_user_id", description="Twitter user ID")
    parent_tweet_id: str = Field(alias="parent_tweet_id", description="Parent tweet ID")
    content: str = Field(..., description="Tweet content")
    mentioned_at: str = Field(alias="mentioned_at", description="When mentioned")
    type: str = Field(..., description="Mention type")
    twitter_account_info: Optional[AccountInfo] = Field(
        None, alias="twitter_account_info", description="Account information"
    )
    metrics: Optional[Metrics] = Field(None, description="Tweet metrics")


class GetMentionsByKeywordsResponse(BaseResponse[List[SimpleMention]]):
    """Response from keyword search endpoint"""

    success: bool = Field(..., description="Whether the request was successful")
    data: List[SimpleMention] = Field(..., description="List of mentions")
    metadata: CursorPaginationMetadata = Field(..., description="Pagination metadata")


class MentionWithAccountAndToken(BaseModel):
    """Mention with full account and token information"""

    mention_id: float = Field(alias="mentionId", description="Mention ID")
    content: str = Field(..., description="Tweet content")
    type: str = Field(..., description="Mention type")
    original_url: str = Field(alias="originalUrl", description="Original tweet URL")
    mentioned_at: str = Field(alias="mentionedAt", description="When mentioned")
    mentioned_by_type: MentionedByType = Field(
        alias="mentionedByType", description="Type of mention source"
    )
    sentiment: SentimentType = Field(..., description="Sentiment analysis result")
    account: BasicAccount = Field(..., description="Account information")
    coins: List[BasicCoin] = Field(..., description="Associated coins")


class TokenMentionsData(BaseModel):
    """Token mentions data wrapper"""

    data: List[MentionWithAccountAndToken] = Field(
        ..., description="List of token mentions"
    )


class GetTokenMentionsResponse(BaseResponse[TokenMentionsData]):
    """Response from token mentions endpoint"""

    success: bool = Field(..., description="Whether the request was successful")
    data: TokenMentionsData = Field(..., description="Token mentions data")


class TopMentionData(BaseModel):
    """Single top mention data"""

    metrics: Metrics = Field(..., description="Tweet metrics")
    mentioned_at: str = Field(alias="mentioned_at", description="When mentioned")
    content: str = Field(..., description="Tweet content")
    id: float = Field(..., description="Mention ID")


class TopMentionsData(BaseModel):
    """Top mentions response data"""

    page_size: float = Field(alias="pageSize", description="Number of items per page")
    page: float = Field(..., description="Current page number")
    total: float = Field(..., description="Total number of items")
    data: List[TopMentionData] = Field(..., description="List of top mentions")


class TopMentionsV2Response(BaseResponse[List[SanitizedMention]]):
    """Response from the V2 top mentions endpoint"""

    success: bool = Field(..., description="Whether the request was successful")
    data: List[SanitizedMention] = Field(..., description="List of top mentions")
    metadata: PagePaginationMetadata = Field(..., description="Pagination metadata")


class TopMentionsResponse(BaseResponse[TopMentionsData]):
    """Response from V1 top mentions endpoint"""

    success: bool = Field(..., description="Whether the request was successful")
    data: TopMentionsData = Field(..., description="Top mentions data")
