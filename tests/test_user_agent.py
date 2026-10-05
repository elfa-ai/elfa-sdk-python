"""User-Agent: the SDK product token, the integrator's ``app_name``, overrides."""

import re
from pathlib import Path

import httpx
import pytest
import respx

from elfa import AsyncElfaClient, ElfaClient
from elfa.client.auto_client import AsyncAutoClient, AutoClient
from elfa.exceptions import ElfaValidationError
from elfa.utils.http import (
    APP_NAME_MAX_LENGTH,
    default_headers,
    normalize_app_name,
    user_agent,
)
from elfa.version import VERSION
from tests.conftest import BASE_URL

_PONG = {"success": True, "data": {"message": "pong"}}


def _user_agents(headers):
    return [name for name in headers if name.lower() == "user-agent"]


def test_user_agent_without_app_name():
    assert user_agent() == f"elfa-sdk-python/{VERSION}"


def test_user_agent_appends_trimmed_app_name():
    assert (
        user_agent("  my-bot/1.2 (prod)  ")
        == f"elfa-sdk-python/{VERSION} my-bot/1.2 (prod)"
    )


def test_app_name_of_maximum_length_is_accepted():
    name = "a" * APP_NAME_MAX_LENGTH
    assert normalize_app_name(name) == name


@pytest.mark.parametrize(
    "app_name",
    [
        "",
        "   ",
        "a" * (APP_NAME_MAX_LENGTH + 1),
        "bot\r\nx-injected: 1",
        "bot\t1",
        "bøt/1",
    ],
    ids=["empty", "blank", "too-long", "line-break", "tab", "non-ascii"],
)
def test_invalid_app_name_raises(app_name):
    with pytest.raises(ElfaValidationError):
        user_agent(app_name)


def test_default_headers_sets_the_sdk_user_agent():
    headers = default_headers("k", app_name="my-bot/1.2")
    assert _user_agents(headers) == ["User-Agent"]
    assert headers["User-Agent"] == f"elfa-sdk-python/{VERSION} my-bot/1.2"


@pytest.mark.parametrize("name", ["User-Agent", "user-agent", "USER-AGENT"])
def test_caller_user_agent_replaces_the_sdk_one_in_any_casing(name):
    headers = default_headers("k", {name: "custom/1"}, app_name="my-bot/1.2")
    assert _user_agents(headers) == [name]
    assert headers[name] == "custom/1"


def test_app_name_is_validated_even_when_the_caller_sets_a_user_agent():
    with pytest.raises(ElfaValidationError):
        default_headers("k", {"user-agent": "custom/1"}, app_name="bot\nx")


@respx.mock
def test_sync_client_sends_app_name():
    route = respx.get(f"{BASE_URL}/v2/ping").mock(
        return_value=httpx.Response(200, json=_PONG)
    )
    client = ElfaClient(api_key="k", base_url=BASE_URL, app_name="my-bot/1.2")
    client.ping()
    agent = route.calls[-1].request.headers["user-agent"]
    assert agent == f"elfa-sdk-python/{VERSION} my-bot/1.2"
    client.close()


@respx.mock
async def test_async_client_sends_app_name():
    route = respx.get(f"{BASE_URL}/v2/ping").mock(
        return_value=httpx.Response(200, json=_PONG)
    )
    async with AsyncElfaClient(
        api_key="k", base_url=BASE_URL, app_name="my-bot/1.2"
    ) as client:
        await client.ping()
    agent = route.calls[-1].request.headers["user-agent"]
    assert agent == f"elfa-sdk-python/{VERSION} my-bot/1.2"


@respx.mock
def test_chat_stream_sends_app_name():
    route = respx.post(f"{BASE_URL}/v2/chat/stream").mock(
        return_value=httpx.Response(200, text="data: [DONE]\n\n")
    )
    client = ElfaClient(api_key="k", base_url=BASE_URL, app_name="my-bot/1.2")
    list(client.chat_stream("hello"))
    agent = route.calls[-1].request.headers["user-agent"]
    assert agent == f"elfa-sdk-python/{VERSION} my-bot/1.2"
    client.close()


@respx.mock
def test_caller_header_replaces_the_user_agent_on_the_wire():
    route = respx.get(f"{BASE_URL}/v2/ping").mock(
        return_value=httpx.Response(200, json=_PONG)
    )
    client = ElfaClient(
        api_key="k",
        base_url=BASE_URL,
        headers={"user-agent": "custom/1"},
        app_name="my-bot/1.2",
    )
    client.ping()
    assert route.calls[-1].request.headers.get_list("user-agent") == ["custom/1"]
    client.close()


def test_composed_auto_client_shares_the_parent_transport():
    client = ElfaClient(api_key="k", base_url=BASE_URL, app_name="my-bot/1.2")
    assert client.auto._transport is client._transport
    client.close()


def test_standalone_auto_client_sends_app_name():
    client = AutoClient("k", base_url=BASE_URL, app_name="my-bot/1.2")
    agent = client._transport._client.headers["user-agent"]
    assert agent == f"elfa-sdk-python/{VERSION} my-bot/1.2"
    client.close()


async def test_standalone_async_auto_client_sends_app_name():
    client = AsyncAutoClient("k", base_url=BASE_URL, app_name="my-bot/1.2")
    agent = client._transport._client.headers["user-agent"]
    assert agent == f"elfa-sdk-python/{VERSION} my-bot/1.2"
    await client.close()


@pytest.mark.parametrize("cls", [ElfaClient, AsyncElfaClient])
def test_app_name_is_keyword_only(cls):
    with pytest.raises(TypeError):
        cls("k", BASE_URL, 30.0, 3, 1.0, None, "my-bot/1.2")


@pytest.mark.parametrize("cls", [ElfaClient, AsyncElfaClient])
def test_clients_reject_an_invalid_app_name(cls):
    with pytest.raises(ElfaValidationError):
        cls(api_key="k", app_name=" ")


def test_version_matches_pyproject():
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    match = re.search(
        r'^version\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8"), re.M
    )
    assert match, "no version in pyproject.toml"
    assert match.group(1) == VERSION
