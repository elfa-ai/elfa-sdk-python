"""
Authentication and API key related models
"""

from datetime import datetime
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

from elfa.models.base import BaseResponse


class Usage(BaseModel):
    """API usage statistics"""

    monthly: float = Field(..., description="Monthly usage count")
    daily: float = Field(..., description="Daily usage count")


class Limits(BaseModel):
    """API rate limits"""

    monthly: float = Field(..., description="Monthly limit")
    daily: float = Field(..., description="Daily limit")


class RemainingRequests(BaseModel):
    """Remaining API requests"""

    monthly: float = Field(..., description="Remaining monthly requests")
    daily: float = Field(..., description="Remaining daily requests")


class Subscription(BaseModel):
    """Subscription information"""

    status: str = Field(..., description="Subscription status")
    billing_interval: Optional[str] = Field(
        None, alias="billingInterval", description="Billing interval"
    )
    overage_usage: Optional[float] = Field(
        None, alias="overageUsage", description="Overage usage"
    )
    cancel_at_period_end: Optional[bool] = Field(
        None, alias="cancelAtPeriodEnd", description="Cancel at period end"
    )
    current_period_end: Optional[str] = Field(
        None, alias="currentPeriodEnd", description="Current period end date"
    )


class ApiKeyStatus(BaseModel):
    """Detailed API key status information"""

    id: float = Field(..., description="API key ID")
    name: str = Field(..., description="API key name")
    status: Literal["active", "revoked", "expired", "payment_required"] = Field(
        ..., description="API key status"
    )
    daily_request_limit: float = Field(
        alias="dailyRequestLimit", description="Daily request limit"
    )
    monthly_request_limit: float = Field(
        alias="monthlyRequestLimit", description="Monthly request limit"
    )
    expires_at: Union[str, datetime] = Field(
        alias="expiresAt", description="API key expiration date"
    )
    created_at: Union[str, datetime] = Field(
        alias="createdAt", description="API key creation date"
    )
    usage: Usage = Field(..., description="Current usage statistics")
    limits: Limits = Field(..., description="Rate limits")
    is_expired: bool = Field(alias="isExpired", description="Whether key is expired")
    remaining_requests: RemainingRequests = Field(
        alias="remainingRequests", description="Remaining requests"
    )


class SimpleUsage(BaseModel):
    """Simplified usage statistics"""

    remaining_monthly: float = Field(
        alias="remainingMonthly", description="Remaining monthly requests"
    )
    remaining_daily: float = Field(
        alias="remainingDaily", description="Remaining daily requests"
    )
    month: float = Field(..., description="Monthly usage")
    today: float = Field(..., description="Daily usage")


class ApiKeyStatusData(BaseModel):
    """Alternative API key status format"""

    name: str = Field(..., description="API key name")
    daily_limit: float = Field(alias="dailyLimit", description="Daily limit")
    monthly_limit: float = Field(alias="monthlyLimit", description="Monthly limit")
    tier: str = Field(..., description="API tier")
    usage: SimpleUsage = Field(..., description="Usage statistics")
    subscription: Optional[Subscription] = Field(None, description="Subscription info")
    allow_overage: bool = Field(alias="allowOverage", description="Allow overage usage")
    max_overage: Optional[float] = Field(
        None, alias="maxOverage", description="Maximum overage allowed"
    )


class ApiKeyStatusResponse(BaseResponse[Union[ApiKeyStatus, ApiKeyStatusData]]):
    """Response from the API key status endpoint"""

    success: bool = Field(..., description="Whether the request was successful")
    data: Union[ApiKeyStatus, ApiKeyStatusData] = Field(
        ..., description="API key status data"
    )
