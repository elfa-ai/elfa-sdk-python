"""Models for the AI chat endpoints."""

from pydantic import Field
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


class ChatData(ElfaModel):
    message: str
    session_id: str = Field(alias="sessionId")
    credits_consumed: int = Field(alias="creditsConsumed")


class ChatResponse(ElfaModel):
    success: bool
    data: ChatData


class ChatStreamEvent(ElfaModel):
    """One ``data:`` frame from the chat stream; payload fields arrive as extras."""

    type: str
