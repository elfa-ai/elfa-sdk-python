"""Shared helpers for the SDK clients."""

import json
from typing import Any, Dict, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel, ValidationError

from elfa.exceptions import ElfaAPIError
from elfa.models.auto import AutoStreamEvent
from elfa.models.chat import ChatStreamEvent
from elfa.utils.serialize import to_compact_json
from elfa.utils.sse import SSEMessage

TModel = TypeVar("TModel", bound=BaseModel)


def parse_model(model: Type[TModel], data: Any) -> TModel:
    try:
        return model.model_validate(data)
    except ValidationError as error:
        raise ElfaAPIError(f"Invalid response format: {error}")


def drop_none(params: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in params.items() if value is not None}


def stream_event(message: SSEMessage) -> AutoStreamEvent:
    try:
        data = json.loads(message.data) if message.data else {}
    except json.JSONDecodeError:
        data = {"raw": message.data}
    return AutoStreamEvent(event=message.event, data=data, id=message.id)


def chat_stream_event(message: SSEMessage) -> Optional[ChatStreamEvent]:
    """Parse one chat SSE frame, or ``None`` for frames without a usable type."""
    if not message.data:
        return None
    try:
        payload = json.loads(message.data)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("type"), str):
        return None
    return ChatStreamEvent.model_validate(payload)


class MountedClient:
    """Base for routers mounted under a path prefix (Auto).

    ``_post_args`` / ``_delete_args`` build the mounted URL and the compact-JSON
    body; the sync and async subclasses only differ in how they call the
    transport with those values.
    """

    def __init__(self, transport: Any, mount: str):
        self._transport = transport
        self._mount = mount

    def _post_args(self, path: str, body: Any = None) -> Tuple[str, Optional[str]]:
        content = None if body is None else to_compact_json(body)
        return f"{self._mount}{path}", content

    def _delete_args(self, path: str) -> str:
        return f"{self._mount}{path}"
