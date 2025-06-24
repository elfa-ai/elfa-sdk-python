"""
Account and user-related models
"""

from typing import Optional

from pydantic import BaseModel, Field

from elfa.models.base import BaseResponse


class AccountData(BaseModel):
    """Detailed account profile data"""

    profile_banner_url: str = Field(
        alias="profileBannerUrl", description="Profile banner URL"
    )
    profile_image_url: str = Field(
        alias="profileImageUrl", description="Profile image URL"
    )
    description: str = Field(..., description="Account description")
    user_since: str = Field(alias="userSince", description="Account creation date")
    location: str = Field(..., description="Account location")
    name: str = Field(..., description="Display name")


class Account(BaseModel):
    """Full account information"""

    id: float = Field(..., description="Account ID")
    username: str = Field(..., description="Username")
    data: AccountData = Field(..., description="Account profile data")
    follower_count: Optional[float] = Field(
        None, alias="followerCount", description="Number of followers"
    )
    following_count: Optional[float] = Field(
        None, alias="followingCount", description="Number of following"
    )
    is_verified: bool = Field(
        alias="isVerified", description="Whether account is verified"
    )


class BasicAccountData(BaseModel):
    """Basic account profile data"""

    description: str = Field(..., description="Account description")
    user_since: str = Field(alias="userSince", description="Account creation date")
    location: str = Field(..., description="Account location")
    name: str = Field(..., description="Display name")


class BasicAccount(BaseModel):
    """Basic account information"""

    twitter_id: float = Field(alias="twitterId", description="Twitter ID")
    username: str = Field(..., description="Username")
    follower_count: float = Field(
        alias="followerCount", description="Number of followers"
    )
    following_count: float = Field(
        alias="followingCount", description="Number of following"
    )
    is_verified: bool = Field(
        alias="isVerified", description="Whether account is verified"
    )
    data: BasicAccountData = Field(..., description="Account profile data")


class AccountInfo(BaseModel):
    """Simple account information"""

    username: str = Field(..., description="Username")
    description: Optional[str] = Field(None, description="Account description")
    profile_image_url: Optional[str] = Field(
        None, alias="profileImageUrl", description="Profile image URL"
    )


class AccountSmartStats(BaseModel):
    """Smart account statistics"""

    smart_follower_count: Optional[float] = Field(
        None, alias="smartFollowerCount", description="Number of smart followers"
    )
    follower_engagement_ratio: float = Field(
        alias="followerEngagementRatio", description="Follower engagement ratio"
    )
    average_engagement: float = Field(
        alias="averageEngagement", description="Average engagement score"
    )
    smart_following_count: float = Field(
        alias="smartFollowingCount", description="Number of smart accounts following"
    )


class AccountSmartStatsResponse(BaseResponse[AccountSmartStats]):
    """Response from the account smart stats endpoint"""

    success: bool = Field(..., description="Whether the request was successful")
    data: AccountSmartStats = Field(..., description="Smart account statistics")
