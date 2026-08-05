"""Response models for the core data endpoints."""

from typing import List, Optional, Union

from pydantic import Field

from elfa.models.base import ElfaModel


class PingData(ElfaModel):
    message: str


class PingResponse(ElfaModel):
    success: bool
    data: PingData


class ApiKeyStatus(ElfaModel):
    """API key status. Fields vary by key tier, so most are optional."""

    name: Optional[str] = None
    status: Optional[str] = None
    tier: Optional[str] = None
    daily_request_limit: Optional[int] = Field(None, alias="dailyRequestLimit")
    monthly_request_limit: Optional[int] = Field(None, alias="monthlyRequestLimit")
    daily_limit: Optional[int] = Field(None, alias="dailyLimit")
    monthly_limit: Optional[int] = Field(None, alias="monthlyLimit")
    expires_at: Optional[str] = Field(None, alias="expiresAt")
    is_expired: Optional[bool] = Field(None, alias="isExpired")
    scopes: Optional[List[str]] = None
    usage: Optional[dict] = None
    limits: Optional[dict] = None
    remaining_requests: Optional[dict] = Field(None, alias="remainingRequests")
    subscription: Optional[dict] = None
    allow_overage: Optional[bool] = Field(None, alias="allowOverage")
    max_overage: Optional[int] = Field(None, alias="maxOverage")


class ApiKeyStatusResponse(ElfaModel):
    success: bool
    data: ApiKeyStatus


class TrendingToken(ElfaModel):
    token: str
    current_count: int
    previous_count: int
    change_percent: float


class TrendingTokensData(ElfaModel):
    total: int
    page: int
    page_size: int = Field(alias="pageSize")
    data: List[TrendingToken]


class TrendingTokensResponse(ElfaModel):
    success: bool
    data: TrendingTokensData


class AccountSmartStats(ElfaModel):
    smart_following_count: int = Field(alias="smartFollowingCount")
    average_engagement: float = Field(alias="averageEngagement")
    average_reach: float = Field(alias="averageReach")
    smart_follower_count: Optional[int] = Field(None, alias="smartFollowerCount")
    follower_count: Optional[int] = Field(None, alias="followerCount")


class AccountSmartStatsResponse(ElfaModel):
    success: bool
    data: AccountSmartStats


class MentionAccount(ElfaModel):
    username: str
    is_verified: bool = Field(alias="isVerified")


class RepostBreakdown(ElfaModel):
    smart: int
    ct: int


class ProcessedMention(ElfaModel):
    tweet_id: str = Field(alias="tweetId")
    link: str
    like_count: Optional[int] = Field(None, alias="likeCount")
    repost_count: Optional[int] = Field(None, alias="repostCount")
    view_count: Optional[int] = Field(None, alias="viewCount")
    quote_count: Optional[int] = Field(None, alias="quoteCount")
    reply_count: Optional[int] = Field(None, alias="replyCount")
    bookmark_count: Optional[int] = Field(None, alias="bookmarkCount")
    mentioned_at: str = Field(alias="mentionedAt")
    type: str
    account: Optional[MentionAccount] = None
    repost_breakdown: Optional[RepostBreakdown] = Field(None, alias="repostBreakdown")


class KeywordMentionsMetadata(ElfaModel):
    total: int
    cursor: Optional[Union[int, str]] = None


class KeywordMentionsV2Response(ElfaModel):
    success: bool
    data: List[ProcessedMention]
    metadata: KeywordMentionsMetadata


class PageMetadata(ElfaModel):
    total: int
    page: int
    page_size: int = Field(alias="pageSize")


class TokenNewsV2Response(ElfaModel):
    success: bool
    data: List[ProcessedMention]
    metadata: PageMetadata


class TrendingContractAddress(ElfaModel):
    contract_address: str = Field(alias="contractAddress")
    chain: str
    mention_count: int = Field(alias="mentionCount")


class TrendingCAsData(ElfaModel):
    total: int
    page: int
    page_size: int = Field(alias="pageSize")
    data: List[TrendingContractAddress]


class TrendingCAsV2Response(ElfaModel):
    success: bool
    data: TrendingCAsData


class TopMention(ElfaModel):
    tweet_id: str = Field(alias="tweetId")
    link: str
    like_count: int = Field(alias="likeCount")
    repost_count: int = Field(alias="repostCount")
    view_count: int = Field(alias="viewCount")
    quote_count: int = Field(alias="quoteCount")
    reply_count: int = Field(alias="replyCount")
    bookmark_count: int = Field(alias="bookmarkCount")
    mentioned_at: str = Field(alias="mentionedAt")
    type: str
    account: Optional[MentionAccount] = None
    repost_breakdown: Optional[RepostBreakdown] = Field(None, alias="repostBreakdown")


class TopMentionsV2Response(ElfaModel):
    success: bool
    data: List[TopMention]
    metadata: PageMetadata


class EventSummaryItem(ElfaModel):
    summary: str
    source_links: List[str] = Field(alias="sourceLinks")
    tweet_ids: List[str] = Field(alias="tweetIds")


class EventSummaryMetadata(ElfaModel):
    summaries: Optional[int] = None
    total_summarized: Optional[int] = None
    total: Optional[int] = None


class EventSummaryV2Response(ElfaModel):
    success: bool
    data: List[EventSummaryItem]
    metadata: Optional[EventSummaryMetadata] = None


class TrendingNarrative(ElfaModel):
    narrative: str
    source_links: List[str]
    tweet_ids: List[str]


class TrendingNarrativesMetadata(ElfaModel):
    total_narratives: Optional[int] = None
    total_tweets: Optional[int] = None
    error: Optional[str] = None


class TrendingNarrativesData(ElfaModel):
    trending_narratives: List[TrendingNarrative]
    metadata: TrendingNarrativesMetadata


class TrendingNarrativesResponse(ElfaModel):
    success: bool
    data: TrendingNarrativesData
