"""
HTTP transport built on httpx, with retries, error mapping, and SSE streaming.

Two thin transports — ``SyncTransport`` and ``AsyncTransport`` — share the pure
helpers below so behaviour stays identical across the sync and async clients.
"""

import asyncio
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncIterator, Dict, Iterator, Optional

import httpx

from elfa.exceptions.base import (
    ElfaAPIError,
    ElfaNetworkError,
    ElfaTimeoutError,
    is_retryable_error,
    raise_for_response,
)
from elfa.version import VERSION

DEFAULT_BASE_URL = "https://api.elfa.ai"


def default_headers(api_key: str) -> Dict[str, str]:
    return {
        "x-elfa-api-key": api_key,
        "User-Agent": f"elfa-sdk-python/{VERSION}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def clean_params(params: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """Drop ``None`` values and stringify the rest (bools lowercased like JS)."""
    if not params:
        return {}
    cleaned: Dict[str, str] = {}
    for key, value in params.items():
        if value is None:
            continue
        cleaned[key] = (
            "true" if value is True else "false" if value is False else str(value)
        )
    return cleaned


def backoff_delay(retry_delay: float, attempt: int) -> float:
    return float(retry_delay * (2**attempt))


def _parse_json(response: httpx.Response) -> Any:
    if not response.content:
        return None
    try:
        return response.json()
    except Exception as error:
        raise ElfaAPIError(f"Failed to parse response JSON: {error}")


class SyncTransport:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.retries = retries
        self.retry_delay = retry_delay
        self._client = httpx.Client(
            headers=default_headers(api_key),
            timeout=timeout,
            follow_redirects=True,
        )

    def __enter__(self) -> "SyncTransport":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def request_json(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        query = clean_params(params)
        retries = self.retries if method in ("GET", "HEAD") else 0
        last_error: Optional[Exception] = None

        for attempt in range(retries + 1):
            try:
                response = self._client.request(
                    method, url, params=query or None, content=content, headers=headers
                )
                if not response.is_success:
                    raise_for_response(response)
                return _parse_json(response)
            except ElfaAPIError as error:
                last_error = error
                if attempt >= retries or not is_retryable_error(error):
                    raise
            except httpx.TimeoutException as error:
                last_error = ElfaTimeoutError(f"Request timed out: {error}")
                if attempt >= retries:
                    raise last_error
            except httpx.HTTPError as error:
                last_error = ElfaNetworkError(f"Network error: {error}", error)
                if attempt >= retries:
                    raise last_error
            time.sleep(backoff_delay(self.retry_delay, attempt))

        raise last_error  # type: ignore[misc]

    @contextmanager
    def stream_lines(
        self, method: str, path: str, *, headers: Optional[Dict[str, str]] = None
    ) -> Iterator[Iterator[str]]:
        url = f"{self.base_url}{path}"
        with self._client.stream(method, url, headers=headers) as response:
            if not response.is_success:
                response.read()
                raise_for_response(response)
            yield response.iter_lines()


class AsyncTransport:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.retries = retries
        self.retry_delay = retry_delay
        self._client = httpx.AsyncClient(
            headers=default_headers(api_key),
            timeout=timeout,
            follow_redirects=True,
        )

    async def __aenter__(self) -> "AsyncTransport":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def request_json(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        query = clean_params(params)
        retries = self.retries if method in ("GET", "HEAD") else 0
        last_error: Optional[Exception] = None

        for attempt in range(retries + 1):
            try:
                response = await self._client.request(
                    method, url, params=query or None, content=content, headers=headers
                )
                if not response.is_success:
                    raise_for_response(response)
                return _parse_json(response)
            except ElfaAPIError as error:
                last_error = error
                if attempt >= retries or not is_retryable_error(error):
                    raise
            except httpx.TimeoutException as error:
                last_error = ElfaTimeoutError(f"Request timed out: {error}")
                if attempt >= retries:
                    raise last_error
            except httpx.HTTPError as error:
                last_error = ElfaNetworkError(f"Network error: {error}", error)
                if attempt >= retries:
                    raise last_error
            await asyncio.sleep(backoff_delay(self.retry_delay, attempt))

        raise last_error  # type: ignore[misc]

    @asynccontextmanager
    async def stream_lines(
        self, method: str, path: str, *, headers: Optional[Dict[str, str]] = None
    ) -> AsyncIterator[AsyncIterator[str]]:
        url = f"{self.base_url}{path}"
        async with self._client.stream(method, url, headers=headers) as response:
            if not response.is_success:
                await response.aread()
                raise_for_response(response)
            yield response.aiter_lines()
