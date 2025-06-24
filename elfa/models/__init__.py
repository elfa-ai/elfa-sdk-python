"""
Elfa SDK Pydantic Models

Type-safe models for all API request and response objects.
"""

from elfa.models.accounts import (
    Account,
    AccountInfo,
    AccountSmartStatsResponse,
    BasicAccount,
)
from elfa.models.aggregations import (
    TrendingCAsV2Response,
    TrendingContractAddress,
    TrendingTokensResponse,
)
from elfa.models.auth import ApiKeyStatus, ApiKeyStatusData, ApiKeyStatusResponse
from elfa.models.base import BaseResponse
from elfa.models.common import (
    BasicCoin,
    PingResponse,
)
from elfa.models.mentions import (
    GetMentionsByKeywordsResponse,
    GetTokenMentionsResponse,
    KeywordMentionsV2Response,
    Mention,
    MentionResponse,
    MentionWithAccountAndToken,
    SanitizedMention,
    SimpleMention,
    TokenNewsV2Response,
    TopMentionsResponse,
    TopMentionsV2Response,
    V2Mention,
)

__all__ = [
    # Base
    "BaseResponse",
    # Auth
    "ApiKeyStatus",
    "ApiKeyStatusData",
    "ApiKeyStatusResponse",
    # Mentions
    "V2Mention",
    "SanitizedMention",
    "KeywordMentionsV2Response",
    "TokenNewsV2Response",
    "TopMentionsV2Response",
    "Mention",
    "MentionResponse",
    "SimpleMention",
    "GetMentionsByKeywordsResponse",
    "MentionWithAccountAndToken",
    "GetTokenMentionsResponse",
    "TopMentionsResponse",
    # Aggregations
    "TrendingTokensResponse",
    "TrendingContractAddress",
    "TrendingCAsV2Response",
    # Accounts
    "Account",
    "BasicAccount",
    "AccountInfo",
    "AccountSmartStatsResponse",
    # Common
    "BasicCoin",
    "PingResponse",
]
