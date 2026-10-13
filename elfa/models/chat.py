"""Models for the AI chat endpoints."""

from typing import List, Optional

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


class ChatSource(ElfaModel):
    """A link the research behind an answer read. ``kind`` is a plain string:
    treat a value you do not recognise as ``web``."""

    url: str
    kind: str
    title: Optional[str] = None


class ChatData(ElfaModel):
    message: str
    session_id: str = Field(alias="sessionId")
    credits_consumed: int = Field(alias="creditsConsumed")
    sources: Optional[List[ChatSource]] = None


class ChatResponse(ElfaModel):
    success: bool
    data: ChatData


class ChatStreamEvent(ElfaModel):
    """One ``data:`` frame from the chat stream; payload fields arrive as extras."""

    type: str
    sources: Optional[List[ChatSource]] = None
