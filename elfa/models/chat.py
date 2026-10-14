"""Models for the AI chat endpoints."""

from typing import Any, List, Optional

from pydantic import (
    Field,
    ValidationError,
    ValidatorFunctionWrapHandler,
    field_validator,
)
from typing_extensions import Literal, TypedDict

from elfa.models.base import ElfaModel

ChatAnalysisType = Literal[
    "chat", "macro", "summary", "tokenIntro", "tokenAnalysis", "accountAnalysis"
]
ChatSpeed = Literal["fast", "expert", "adaptive"]


class ChatAssetMetadata(TypedDict, total=False):
    symbol: str
    chain: str
    contractAddress: str
    username: str


class ChatSource(ElfaModel):
    url: str
    kind: str
    title: Optional[str] = None


def _sources_or_none(value: Any, handler: ValidatorFunctionWrapHandler) -> Any:
    try:
        return handler(value)
    except ValidationError:
        return None


class ChatData(ElfaModel):
    message: str
    session_id: str = Field(alias="sessionId")
    credits_consumed: int = Field(alias="creditsConsumed")
    sources: Optional[List[ChatSource]] = None

    _drop_malformed_sources = field_validator("sources", mode="wrap")(_sources_or_none)


class ChatResponse(ElfaModel):
    success: bool
    data: ChatData


class ChatStreamEvent(ElfaModel):
    """One ``data:`` frame from the chat stream; payload fields arrive as extras."""

    type: str
    sources: Optional[List[ChatSource]] = None

    _drop_malformed_sources = field_validator("sources", mode="wrap")(_sources_or_none)
