"""Shared helpers for the SDK clients."""

import json
from typing import Any, Dict, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel, ValidationError

from elfa.exceptions import ElfaAPIError
from elfa.models.auto import AutoStreamEvent
from elfa.utils.hmac import sign_request
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


class SignedClient:
    """Base for routers whose mutations are HMAC-signed (Auto, Trade).

    ``_post_args`` / ``_delete_args`` build the compact-JSON body and signature
    headers; the sync and async subclasses only differ in how they call the
    transport with those values.
    """

    def __init__(self, transport: Any, mount: str, hmac_secret: Optional[str] = None):
        self._transport = transport
        self._mount = mount
        self._hmac_secret = hmac_secret

    def _sign(self, method: str, path: str, body: str) -> Optional[Dict[str, str]]:
        if not self._hmac_secret:
            return None
        return sign_request(self._hmac_secret, method, path, body)

    def _post_args(
        self, path: str, body: Any = None
    ) -> Tuple[str, Optional[str], Optional[Dict[str, str]]]:
        body_str = "" if body is None else to_compact_json(body)
        headers = self._sign("POST", path, body_str)
        content = None if body is None else body_str
        return f"{self._mount}{path}", content, headers

    def _delete_args(self, path: str) -> Tuple[str, Optional[Dict[str, str]]]:
        headers = self._sign("DELETE", path, "")
        return f"{self._mount}{path}", headers
