"""Models for the Auto condition engine (`/v2/auto/*`).

Many Auto responses are intentionally loose server-side; the models below capture
the documented fields and keep any extras (``extra="allow"`` on the base).
"""

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Literal

from elfa.models.base import ElfaModel

TradableExchange = Literal["hyperliquid", "gmx", "binance", "pacifica"]
AutoSpeed = Literal["fast", "expert", "adaptive"]


class AutoChatResponse(ElfaModel):
    session_id: str = Field(alias="sessionId")
    response: str
    title: Optional[str] = None
    reasoning: Optional[str] = None
    plan_ids: List[str] = Field(default_factory=list, alias="planIds")


class AutoEstimatedCost(ElfaModel):
    credits: float
    price: str


class AutoValidateResponse(ElfaModel):
    valid: bool
    errors: List[Any] = Field(default_factory=list)
    warnings: List[Any] = Field(default_factory=list)
    estimated_credits: Optional[float] = Field(None, alias="estimatedCredits")
    estimated_cost: Optional[AutoEstimatedCost] = Field(None, alias="estimatedCost")


class AutoQuery(ElfaModel):
    """Create/convert/cancel/delete result. Exposes ``id`` and/or ``queryId``."""

    id: Optional[str] = None
    query_id: Optional[str] = Field(None, alias="queryId")
    status: Optional[str] = None
    estimated_credits: Optional[float] = Field(None, alias="estimatedCredits")


class AutoListQueriesResponse(ElfaModel):
    queries: Optional[List[AutoQuery]] = None
    data: Optional[List[AutoQuery]] = None
    total: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class AutoLatestEvaluation(ElfaModel):
    evaluated_at: Optional[str] = Field(None, alias="evaluatedAt")
    would_trigger_now: Optional[bool] = Field(None, alias="wouldTriggerNow")


class AutoQueryExecution(ElfaModel):
    id: str
    query_id: str = Field(alias="queryId")
    type: str
    status: str
    created_at: str = Field(alias="createdAt")
    error: Optional[Any] = None


class AutoPollQueryResponse(ElfaModel):
    query_id: str = Field(alias="queryId")
    status: str
    latest_evaluation: Optional[AutoLatestEvaluation] = Field(
        None, alias="latestEvaluation"
    )
    executions: List[AutoQueryExecution] = Field(default_factory=list)
    credits: Optional[float] = None


class AutoDraft(ElfaModel):
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    query: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    valid: Optional[bool] = None
    visibility: Optional[Literal["public", "private"]] = None


class AutoConvertDraftResponse(ElfaModel):
    draft_id: str = Field(alias="draftId")
    converted_at: str = Field(alias="convertedAt")
    query: AutoQuery


class AutoListDraftsResponse(ElfaModel):
    drafts: Optional[List[AutoDraft]] = None
    data: Optional[List[AutoDraft]] = None
    total: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class AutoSessionSummary(ElfaModel):
    session_id: str = Field(alias="sessionId")
    status: Optional[str] = None
    executed_at: str = Field(alias="executedAt")


class AutoListSessionsResponse(ElfaModel):
    query_id: Optional[str] = Field(None, alias="queryId")
    sessions: List[AutoSessionSummary] = Field(default_factory=list)


class AutoSessionMessage(ElfaModel):
    query: Optional[str] = None
    response: Optional[str] = None
    status: Optional[str] = None
    analysis_type: Optional[str] = Field(None, alias="analysisType")
    timestamp: Optional[str] = None
    trades: List[Any] = Field(default_factory=list)
    highlighted_text: Optional[str] = Field(None, alias="highlightedText")


class AutoSession(ElfaModel):
    session_id: str = Field(alias="sessionId")
    query_id: str = Field(alias="queryId")
    title: Optional[str] = None
    analysis_type: Optional[str] = Field(None, alias="analysisType")
    created_at: str = Field(alias="createdAt")
    messages: List[AutoSessionMessage] = Field(default_factory=list)


class AutoExecution(ElfaModel):
    id: Optional[str] = None
    query_id: Optional[str] = Field(None, alias="queryId")
    type: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = Field(None, alias="createdAt")
    error: Optional[Any] = None


class AutoListExecutionsResponse(ElfaModel):
    data: List[AutoExecution] = Field(default_factory=list)


class AutoValidateSymbolResponse(ElfaModel):
    supported: Literal["true", "false"]


class AutoSuccessResponse(ElfaModel):
    success: bool


class AutoStreamEvent(ElfaModel):
    event: str
    data: Dict[str, Any] = Field(default_factory=dict)
    id: Optional[str] = None
