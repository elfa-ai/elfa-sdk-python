# Elfa AI Python SDK

[![PyPI version](https://badge.fury.io/py/elfa-sdk.svg)](https://badge.fury.io/py/elfa-sdk)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Python SDK for the Elfa API, v2 and v3 — social intelligence, AI chat, the Auto condition engine, and API v3 events, calls and market data. Sync and async clients, fully typed with Pydantic.

## Features

- **Social intelligence** — trending tokens, mentions, narratives, smart stats, event summaries
- **AI chat** — market analysis and conversational chat via `client.chat`, streamed via `client.chat_stream`
- **Auto condition engine** — build EQL queries that watch markets and notify via `client.auto`
- **API v3** — events, storylines and arcs; call books, mindshare and trending contracts; calls, call episodes and positioning; ranked accounts, via `client.v3`
- **Sync and async** — `ElfaClient` and `AsyncElfaClient`, same surface
- **Typed** — Pydantic v2 models, full type hints
- **Robust** — retries with backoff, typed errors

> The SDK returns processed metadata and tweet links only — never raw tweet content. For raw tweets, call the X (Twitter) API directly using the returned links/ids.

## Installation

```bash
pip install elfa-sdk
```

## Quick start

### Synchronous

```python
from elfa import ElfaClient

client = ElfaClient(api_key="your-api-key")

trending = client.get_trending_tokens(time_window="24h")
for token in trending.data.data:
    print(token.token, token.current_count, f"{token.change_percent:+.1f}%")

mentions = client.get_keyword_mentions(keywords="bitcoin,ethereum", time_window="1h")
for mention in mentions.data:
    print(mention.link, mention.like_count)

answer = client.chat("What's the sentiment on Bitcoin today?")
print(answer.data.message)
```

### Asynchronous

```python
import asyncio
from elfa import AsyncElfaClient

async def main():
    async with AsyncElfaClient(api_key="your-api-key") as client:
        stats = await client.get_account_smart_stats("elonmusk")
        print(stats.data.smart_following_count)

asyncio.run(main())
```

## Configuration

```python
client = ElfaClient(
    api_key="your-api-key",
    base_url="https://api.elfa.ai",  # default (production)
    timeout=30.0,                    # per-request timeout, seconds
    retries=3,                       # retries for idempotent (GET) requests
    retry_delay=1.0,                 # base delay for exponential backoff
    headers=None,                    # extra headers sent on every request
    app_name=None,                   # your product, appended to the User-Agent, e.g. "my-bot/1.2"
)

# Quick reachability/auth check
assert client.test_connection() is True
```

The Auto engine is also constructable standalone if that is all you need:

```python
from elfa import AutoClient

auto = AutoClient(api_key="your-api-key")
auto.close()
```

The API key is sent as the `x-elfa-api-key` header on every request. Read it from the environment in your app:

```python
import os
from elfa import ElfaClient

client = ElfaClient(api_key=os.environ["ELFA_API_KEY"])
```

## Core data & chat

All methods exist on both `ElfaClient` (sync) and `AsyncElfaClient` (async).

| Method | Endpoint |
| --- | --- |
| `ping()` | `/v2/ping` |
| `get_api_key_status()` | `/v2/key-status` |
| `get_trending_tokens(...)` | `/v2/aggregations/trending-tokens` |
| `get_account_smart_stats(username)` | `/v2/account/smart-stats` |
| `get_keyword_mentions(...)` | `/v2/data/keyword-mentions` |
| `get_token_news(...)` | `/v2/data/token-news` |
| `get_trending_cas_twitter(...)` | `/v2/aggregations/trending-cas/twitter` |
| `get_trending_cas_telegram(...)` | `/v2/aggregations/trending-cas/telegram` |
| `get_top_mentions(ticker, ...)` | `/v2/data/top-mentions` |
| `get_event_summary(keywords, ...)` | `/v2/data/event-summary` |
| `get_trending_narratives(...)` | `/v2/data/trending-narratives` |
| `chat(message, ...)` | `/v2/chat` |
| `chat_stream(message, ...)` | `/v2/chat/stream` |

Time-ranged endpoints accept either `time_window="24h"` or both `from_time` and `to_time` (unix seconds).

`get_account_smart_stats` is **legacy — it still works, but will be removed on 28 October 2026**. It returns raw metrics, not a reputation score, and is not being extended before then; use `get_keyword_mentions` instead, which returns the posting account alongside each mention's engagement metrics.

`get_token_news` returns X posts from accounts tagged as news sources, not articles published by news outlets.

### Streaming chat (SSE)

`chat_stream` takes the same arguments as `chat` and yields one event per `data:` frame, ending on the terminating `[DONE]` frame. Requires a PAYG or Enterprise API key.

```python
for event in client.chat_stream("What is the sentiment on SOL?"):
    if event.type == "text":
        print(event.content, end="")
    elif event.type == "complete":
        print("\ncredits:", event.creditsConsumed)

# async
async for event in async_client.chat_stream("What is the sentiment on SOL?"):
    print(event.type)
```

Event types are `session_info`, `title`, `text`, `text_complete`, `status`, `credits`, `complete`, `invalid_request` and `error`. Payload fields vary by type and are preserved as model extras.

### Chat sources

Pass `include_sources=True` to `chat` or `chat_stream` to receive the links the research behind the answer read. On `chat` they arrive as `data.sources`; on the stream they arrive as `sources` on the final `complete` event. Without the flag the response is unchanged.

```python
answer = client.chat("What moved SOL today?", include_sources=True)
for source in answer.data.sources or []:
    print(source.kind, source.url, source.title)
```

Each source has a `url`, a `kind` and an optional `title` naming the research step, such as "Searched X". These are links only: the content of a page or post is not returned. A source was read, not necessarily cited in `message`, and the list is empty when the answer used no linkable source. `kind` is a string (`x_post`, `x_account`, `telegram`, `dex`, `explorer`, `prediction_market`, `web`): treat a value you do not recognise as `web`.

## Auto condition engine (`client.auto`)

Build [EQL](https://docs.elfa.ai) queries that watch conditions and fire actions (`notify`, `webhook`, `telegram_bot`, `llm`). Every route authenticates with the API key alone.

```python
query = {
    "query": {
        "conditions": {
            "AND": [{
                "source": "price", "method": "current",
                "args": {"symbol": "BTC", "exchange": "hyperliquid"},
                "operator": ">", "value": 250000,
            }]
        },
        "actions": [{"stepId": "notify", "type": "notify", "params": {"message": "BTC > 250k"}}],
        "expiresIn": "24h",
    },
    "title": "btc breakout alert",
}

client.auto.validate_query(query)
created = client.auto.create_query(query)
query_id = created.id or created.query_id

status = client.auto.get_query(query_id)
client.auto.cancel_query(query_id)
client.auto.delete_query(query_id)
```

Also available: `chat`, `list_queries`, drafts (`list_drafts`/`get_draft`/`upsert_draft`/`delete_draft`/`validate_draft`/`convert_draft`), `list_sessions`/`get_session`, `list_executions`/`get_execution`, and `validate_symbol`.

Builder Chat is dynamically priced, so it reports what the turn cost:

```python
reply = client.auto.chat("Alert me when BTC breaks 100k")
print(reply.credits)  # e.g. 104 — same total as the x-elfa-credits header
```

### Response shapes are extensible

Every response model sets `extra="allow"`, so fields the API adds are kept as
model extras rather than raising. Do the same in your own code — pinning an Elfa
response with an exact-shape assertion (Pydantic `extra="forbid"`,
`z.strictObject`, `additionalProperties: false`) means the next additive field
breaks your client even though the API stayed backwards compatible.

### Streaming notifications (SSE)

```python
for event in client.auto.stream_query(query_id):
    print(event.event, event.data)

# async
async for event in async_client.auto.stream_all():
    print(event.event, event.data)
```

## API v3 (`client.v3`)

API v3 is the data stack that powers agent awareness: events, storylines and arcs; call books, mindshare and trending contracts; calls, call episodes and positioning; ranked accounts. Every method exists on `client.v3` (sync) and `async_client.v3` (async), and shares the client's API key, retries and headers.

Resolve Bitcoin, read its last day of events, then see how accounts are positioned on it:

```python
import time

entities = client.v3.get_entities("btc", entity_type=["token"], limit=1)
bitcoin = entities.entities[0]  # check bitcoin.name: the first match may not be the asset you meant

since = int(time.time()) - 86400  # unix seconds
events = client.v3.get_events(entity_ids=[bitcoin.id], from_time=since, limit=10)
for event in events.events:
    print(event.implication, event.alert_title)

positioning = client.v3.get_positioning(bitcoin.id)
print(positioning.open_long, positioning.open_short)
```

| Method | Endpoint |
| --- | --- |
| `get_entities(q, ...)` | `/v3/entities` |
| `get_events(...)` | `/v3/events` |
| `get_storylines(...)` | `/v3/events/storylines` |
| `get_arcs(...)` | `/v3/events/arcs` |
| `get_call_book(market, from_time=..., ...)` | `/v3/market/{crypto,equity}/call-book` |
| `get_mindshare(market, ...)` | `/v3/market/{crypto,equity}/mindshare` |
| `get_trending_contracts(from_time=..., ...)` | `/v3/market/crypto/trending-contracts` |
| `get_calls(...)` | `/v3/calls` |
| `get_call_episodes(...)` | `/v3/calls/episodes` |
| `get_positioning(entity_id)` | `/v3/calls/positioning` |
| `get_top_accounts(...)` | `/v3/people/accounts` |
| `get_key_status()` | `/v3/key-status` |

Rules every v3 endpoint follows:

- **Access.** PAYG, Grow and Enterprise keys can call every v3 endpoint. A Free key can call only `get_key_status()`; the rest raise `ElfaAPIError` with status `403`: `The v3 API is free on the Pay-as-you-go and Grow plans. Upgrade at …`.
- **Times** are unix seconds, UTC, in requests and responses. Milliseconds are a `400`: divide by 1000.
- **`from_time` is required**, except when fetching by id (`event_ids`, `storyline_ids`, `arc_ids`, `call_ids`, `episode_ids`, up to 30) or searching with `q`. `get_events(sort="relevant")` ranks the last 24 hours and refuses `from_time`. `to_time` defaults to now. Entities, arcs, positioning and top accounts take no range; mindshare takes a `period` and an optional `to_time`.
- **Entity filters take an id, never a name.** `get_entities` turns a ticker, name, handle, address, CoinGecko id, FIGI or CIK into that id. It matches exactly; it is not a search.
- **History** is 30 days, 60 days or 2 years back, by plan. `get_key_status().history_from` returns the start; an earlier `from_time` is cut, and `served_from` says where.
- **Top accounts by track record.** `get_top_accounts(metric=...)` ranks by `standing` (the default) or by a caller's track: `alphaScore`, `hitRate` or `avgReturn`. For the best callers use `alphaScore`; `avgReturn` is not adjusted for the market. Track metrics rank only accounts with at least 20 scored positions.
- **Paging.** Pass `next_cursor` back as `cursor`. `has_more=False` and `next_cursor=None` mark the last page. A cursor belongs to its query.
- **Lists.** List parameters (`entity_ids`, `entity_type`, `alert_action`, `relation` and the id lists) take Python lists and are sent comma-separated. At most 30 ids. An empty list raises `ElfaValidationError` rather than silently dropping the filter.
- **Unknown parameters are a `400`**, never ignored. The SDK sends only the parameters you set.
- No endpoint returns post text.

`V3Client` and `AsyncV3Client` are also constructable standalone, like `AutoClient`. See the [API v3 docs](https://docs.elfa.ai/v3/overview) for every parameter and field.

## Error handling

```python
from elfa import (
    ElfaAPIError,
    ElfaAuthenticationError,
    ElfaRateLimitError,
    ElfaValidationError,
    ElfaNetworkError,
)

try:
    client.get_trending_tokens(time_window="24h")
except ElfaAuthenticationError:
    ...  # bad/missing API key
except ElfaRateLimitError as e:
    print("retry after", e.retry_after, "reset", e.reset_time)
except ElfaValidationError as e:
    print("invalid params", e.validation_errors)
except ElfaNetworkError:
    ...  # connection problem
except ElfaAPIError as e:
    print("api error", e.status_code, e)
```

Idempotent (GET) requests are retried with exponential backoff on network errors, rate limits, and 5xx responses. Mutations are not retried automatically.

## Development

```bash
git clone https://github.com/elfa-ai/elfa-sdk-python.git
cd elfa-sdk-python
pip install -e ".[dev]"

make check   # flake8 + mypy + pytest
make format  # black + isort
```

Live integration tests run only when `ELFA_API_KEY` is set (optionally `ELFA_BASE_URL`); otherwise they skip. Set `ELFA_V3=1` as well to run the remaining v3 tests on a PAYG, Grow or Enterprise key.

## Support

- [Documentation](https://docs.elfa.ai)
- [Issues](https://github.com/elfa-ai/elfa-sdk-python/issues)

## License

MIT — see [LICENSE](LICENSE).
