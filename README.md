# Elfa AI Python SDK

[![PyPI version](https://badge.fury.io/py/elfa-sdk.svg)](https://badge.fury.io/py/elfa-sdk)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Python SDK for [Elfa](https://docs.elfa.ai). Get events, answers, verdicts and alerts from social and web data. Sync and async clients, fully typed with Pydantic.

Elfa indexes social media and web pages, and turns them into high-intent events and entities. Your agent can query them, ask about them, or get an alert when they happen.

## Features

- **Data** — events, storylines and arcs, the prediction markets they bear on, and a calendar of what is scheduled; call books, mindshare and trending contracts; calls, call episodes and positioning; ranked accounts, via `client.v3`
- **Explain** — written, sourced answers to market questions via `client.chat`, streamed via `client.chat_stream`
- **Verify and Monitors** — check a claim against X posts, public Telegram channels and web pages with `client.v3.verify`, and get a signed webhook for each new match of a plain-words query with `client.v3.create_monitor`
- **Auto** — alert rules, written as EQL queries, that watch markets and notify via `client.auto`
- **Social data (v2)** — trending tokens, mentions, narratives and event summaries from the older endpoints, which Elfa will deprecate
- **Sync and async** — `ElfaClient` and `AsyncElfaClient`, same surface
- **Typed** — Pydantic v2 models, full type hints
- **Robust** — retries with backoff, typed errors

> The SDK returns processed metadata and tweet links only — never raw tweet content. For raw tweets, call the X (Twitter) API directly using the returned links/ids.

## Installation

```bash
pip install elfa-sdk
```

## Quick start

Read the events Elfa judged most important in the last 24 hours. `from_time` is in unix seconds.

### Synchronous

```python
import time

from elfa import ElfaClient

client = ElfaClient(api_key="your-api-key")

since = int(time.time()) - 86400
events = client.v3.get_events(from_time=since, alert_action=["alert"])
for event in events.events:
    print(event.alert_title)
```

### Asynchronous

```python
import asyncio
import time

from elfa import AsyncElfaClient

async def main():
    async with AsyncElfaClient(api_key="your-api-key") as client:
        since = int(time.time()) - 86400
        events = await client.v3.get_events(from_time=since, alert_action=["alert"])
        print(len(events.events))

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

The Auto client is also constructable standalone if that is all you need:

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

## Social data (v2) and Explain

Apart from `ping`, `get_api_key_status`, `chat` and `chat_stream` (Explain), these methods call the older Social data (v2) endpoints. Elfa will deprecate them; they still work, but build new work on [Data](#data-verify-and-monitors-clientv3).

All methods exist on both `ElfaClient` (sync) and `AsyncElfaClient` (async).

| Method | Endpoint |
| --- | --- |
| `ping()` | `/v2/ping` |
| `get_api_key_status()` | `/v2/key-status` |
| `get_trending_tokens(...)` | `/v2/aggregations/trending-tokens` |
| `get_account_smart_stats(username)` | `/v2/account/smart-stats` (deprecated) |
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

`get_account_smart_stats` is **deprecated and not maintained**. It returns raw metrics, not a reputation score; use `get_keyword_mentions` instead, which returns the posting account alongside each mention's engagement metrics, and `v3.get_top_accounts` to rank accounts.

`get_token_news` returns X posts from accounts tagged as news sources, not articles published by news outlets.

### Streaming chat (SSE)

`chat_stream` takes the same arguments as `chat` and yields one event per `data:` frame, ending on the terminating `[DONE]` frame. Requires a PAYG, Grow or Enterprise API key.

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

Pass `use_memory=True` to let the request use the saved memory of the Elfa account that owns the API key: the answer can draw on notes from that account's earlier chats, and the chat can add to them. Without it the request neither reads nor writes memory. Leave it off when one key serves many end users, so one user's notes never shape another's answer; pass `session_id` to carry context within a conversation instead.

Each source has a `url`, a `kind` and an optional `title` naming the research step, such as "Searched X". These are links only: the content of a page or post is not returned. A source was read, not necessarily cited in `message`, and the list is empty when the answer used no linkable source. `kind` is a string (`x_post`, `x_account`, `telegram`, `dex`, `explorer`, `prediction_market`, `web`): treat a value you do not recognise as `web`.

## Auto (`client.auto`)

[Auto](https://docs.elfa.ai/auto/overview) runs an alert rule that you write and tells you when it matches. Build EQL queries that watch conditions and fire actions (`notify`, `webhook`, `telegram_bot`, `llm`). Every route authenticates with the API key alone.

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

A `tweet` condition can watch any public X account; one outside Elfa's real-time set needs a paid API key, and Builder Chat drafts only real-time accounts. `validate_query` and `create_query` return `tweet_accounts`, saying how each is billed: `included` costs nothing extra, `per_post` costs `credits_per_post` for each post (not replies or reposts) while the query runs. Those charges are not in `estimated_credits` or `x-elfa-credits`; `get_api_key_status()` shows them. An account that can't be watched comes back as a validation error with `details.reason`. When a query fails with a recorded reason, `get_query` carries it in `failure`. See [X Accounts and Per-Post Billing](https://docs.elfa.ai/auto/sources/social-posts#x-accounts-and-per-post-billing).

`x_follow_made` and `x_follow_overlap` conditions return `follow_accounts` the same way: `included` costs nothing extra, `per_day` costs `credits_per_day` for each UTC day its follows are read, on top of `estimated_credits`. See [Follows](https://docs.elfa.ai/auto/sources/social-posts#follows).

Also available: `chat`, `list_queries`, drafts (`list_drafts`/`get_draft`/`upsert_draft`/`delete_draft`/`validate_draft`/`convert_draft`), `list_sessions`/`get_session`, `list_executions`/`get_execution`, and `validate_symbol`.

To read every execution exactly once, oldest first, pass `after="start"` to `list_executions`, then pass back `pagination.next_cursor` as `after`. `has_more=False` means no more executions are ready yet, not the end: poll again later. `after` cannot be combined with `offset` or `status`, and a cursor works only with the `query_id` and `execution_type` it was issued for. An execution can still be `pending` when read; `get_execution` returns its final status. See [Read every time a query fired](https://docs.elfa.ai/auto/manage#read-every-time-a-query-fired).

Builder Chat is dynamically priced, so it reports what the turn cost:

```python
reply = client.auto.chat("Alert me when BTC breaks 100k")
print(reply.credits)  # e.g. 104 — same total as the x-elfa-credits header
```

A turn that fails raises instead of returning an empty `response`: a message the safety checks reject raises `ElfaValidationError` with `status_code` `400`, and a turn that ends with no answer raises `ElfaAPIError` with `status_code` `502` and the `sessionId` in `response_data`. Neither is retried automatically. See [Builder Chat](https://docs.elfa.ai/auto/describe-in-words#builder-chat).

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

## Data, Verify and Monitors (`client.v3`)

`client.v3` covers [Data](https://docs.elfa.ai/enrich/overview): events, storylines and arcs, the prediction markets they bear on, and a calendar of what is scheduled; call books, mindshare and trending contracts; calls, call episodes and positioning; ranked accounts. Every method exists on `client.v3` (sync) and `async_client.v3` (async), and shares the client's API key, retries and headers.

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
| `get_prediction_markets(ids, ...)` | `/v3/events/prediction-markets` |
| `get_calendar(...)` | `/v3/events/calendar` |
| `get_call_book(market, from_time=..., ...)` | `/v3/market/{crypto,equity}/call-book` |
| `get_mindshare(market, ...)` | `/v3/market/{crypto,equity}/mindshare` |
| `get_trending_contracts(from_time=..., ...)` | `/v3/market/crypto/trending-contracts` |
| `get_calls(...)` | `/v3/calls` |
| `get_call_episodes(...)` | `/v3/calls/episodes` |
| `get_positioning(entity_id)` | `/v3/calls/positioning` |
| `get_top_accounts(...)` | `/v3/people/accounts` |
| `get_key_status()` | `/v3/key-status` |

Rules every endpoint in the table follows:

- **Access.** Every plan, Free included, can call every v3 data endpoint, and `get_key_status().plan` can be `"free"`. Each call but `get_key_status()` costs credits on Free, PAYG and Grow, priced per endpoint on the [pricing page](https://docs.elfa.ai/platform/pricing#api-v3).
- **Times** are unix seconds, UTC, in requests and responses. Milliseconds are a `400`: divide by 1000.
- **`from_time` is required**, except when fetching by id (`event_ids`, `storyline_ids`, `arc_ids`, `call_ids`, `episode_ids`, up to 30) or searching with `q`. `get_events(sort="relevant")` ranks the last 24 hours and refuses `from_time`. `to_time` defaults to now. `get_calendar()` reads ahead instead, soonest first: `from_time` defaults to 00:00 UTC today and `to_time` to 30 days after `from_time`. Entities, arcs, prediction markets, positioning and top accounts take no range; mindshare takes a `period` and an optional `to_time`.
- **Entity filters take an id, never a name.** `get_entities` turns a ticker, name, handle, address, CoinGecko id, FIGI or CIK into that id. It matches exactly; it is not a search.
- **History** is 30 days, 60 days or 2 years back, by plan. `get_key_status().history_from` returns the start; an earlier `from_time` is cut, and `served_from` says where.
- **Top accounts by track record.** `get_top_accounts(metric=...)` ranks by `standing` (the default) or by a caller's track: `alphaScore`, `hitRate` or `avgReturn`. For the best callers use `alphaScore`; `avgReturn` is not adjusted for the market. Track metrics rank only accounts with at least 20 scored positions.
- **Paging.** Pass `next_cursor` back as `cursor`. `has_more=False` and `next_cursor=None` mark the last page. A cursor belongs to its query. `get_prediction_markets` has no cursor: every id comes back at once, in `related`.
- **Lists.** List parameters (`entity_ids`, `entity_type`, `alert_action`, `relation` and the id lists) take Python lists and are sent comma-separated. At most 30 ids. An empty list raises `ElfaValidationError` rather than silently dropping the filter.
- **Unknown parameters are a `400`**, never ignored. The SDK sends only the parameters you set.
- No endpoint returns post text.

`V3Client` and `AsyncV3Client` are also constructable standalone, like `AutoClient`. See the [Data docs](https://docs.elfa.ai/enrich/overview) for every parameter and field.

### Verify

`verify(statement, ...)` calls `POST /v3/verify`. It checks one statement against X posts, public Telegram channels and web pages, and returns a `verdict` (`supported`, `contradicted` or `notEnoughEvidence`), its `probabilities`, links to the `evidence` it judged, one list per source, and `coverage`.

```python
result = client.v3.verify(
    "Binance will list HYPE for spot trading.",
    decision={"type": "yesNo"},
)
print(result.verdict, result.probabilities.supported)
if result.decision is not None:
    print(result.decision.yes)
```

- **Plans and cost.** Every plan, Free included. A call costs 1 credit, whatever the verdict. Errors cost nothing.
- **Inputs.** `statement` is up to 500 characters. `context` is up to 4,000 characters of background, such as how a market resolves, and is never treated as evidence. `as_of` (unix seconds) judges the statement as of that moment, at most 30 days ago.
- **Decision.** `decision` asks a question from the same evidence: `{"type": "yesNo"}`, `{"type": "choice", "options": [{"label": ..., "definition": ...}, ...]}` (2 to 20 options) or `{"type": "score", "levels": [...]}` (2 to 10 levels, lowest first). The answer is `result.decision`, with `yes`, `choice` and `probabilities`, or `score` and `level_probabilities`; it is `None` when none was asked or nothing was found.
- **Reading it.** `notEnoughEvidence` does not mean false. `coverage.complete=False` means a source did not answer in time, so the verdict may have missed something. No item holds the text of a post or page: open its `link`.
- Like every write, it is not retried automatically.

See [Verify](https://docs.elfa.ai/verify/overview).

### Monitors

A monitor checks each new Elfa event, and the open web every hour, against a query written in plain words, and sends each match to your webhook, signed with [Standard Webhooks](https://www.standardwebhooks.com/). It reports only items that appear after you create it.

```python
monitor = client.v3.create_monitor(
    "OpenAI, Google or Anthropic launches a new AI model",
    "https://example.com/elfa-webhook",
)

page = client.v3.get_monitor_matches(monitor.id, limit=100)
for match in page.data:
    for item in match.items:
        print(item.source, item.alert_title or item.title)

client.v3.delete_monitor(monitor.id)
```

| Method | Endpoint |
| --- | --- |
| `create_monitor(query, webhook_url)` | `POST /v3/monitors` |
| `get_monitors()` | `GET /v3/monitors` |
| `get_monitor(monitor_id)` | `GET /v3/monitors/{id}` |
| `update_monitor(monitor_id, query=..., webhook_url=...)` | `PATCH /v3/monitors/{id}` |
| `delete_monitor(monitor_id)` | `DELETE /v3/monitors/{id}` |
| `get_monitor_matches(monitor_id, limit=..., cursor=...)` | `GET /v3/monitors/{id}/events` |

- **Plans and cost.** Every plan, Free included. A live monitor costs 2 credits for each started hour, the first when you create it. Every other monitor call is free, and a failed create is never charged.
- **Limits.** Up to 20 live monitors per key. `query` is 3 to 500 characters. `webhook_url` is HTTPS on a public host, up to 2,048 characters.
- **Webhooks.** `webhook_secret` (`whsec_...`) verifies the signature on each webhook from the monitor. It never changes, and `get_monitor` returns it again, so keep it out of logs. Skip a `webhook-id` you already handled.
- **Status.** `status` is `"active"`, or `"ended"` when Elfa stopped the monitor, for example when the key could not pay for an hour. An ended monitor cannot be changed: create a new one.
- **Changes.** `update_monitor` takes `query`, `webhook_url` or both, and keeps the monitor's id and secret. A change sent while an earlier one is still being applied raises `ElfaAPIError` with `status_code` `409`: wait a minute and send it again.
- **Reading back.** `get_monitors()` returns your newest 100 monitors, with no paging. `get_monitor_matches` returns matches newest first, up to 100 a page (20 by default): pass `next_cursor` back as `cursor`; it is `None` on the last page. Each item is an Elfa event (`source="event"`) or a web page (`source="web"`), and any field but `source` and `id` can be `None`.

See [Monitors](https://docs.elfa.ai/monitors/overview).

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

Idempotent (GET) requests are retried with exponential backoff on network errors, rate limits, and 5xx responses. Mutations are not retried automatically. A `429` whose code is `ERR_RATE_LIMITED` means the key is out of credits, not over the per-minute limit, so it is never retried: upgrade, turn on overage, or raise the spend cap.

## Development

```bash
git clone https://github.com/elfa-ai/elfa-sdk-python.git
cd elfa-sdk-python
pip install -e ".[dev]"

make check   # flake8 + mypy + pytest
make format  # black + isort
```

Live integration tests run only when `ELFA_API_KEY` is set (optionally `ELFA_BASE_URL`); otherwise they skip. Set `ELFA_V3=1` as well to run the remaining v3 tests.

## Support

- [Documentation](https://docs.elfa.ai)
- [Issues](https://github.com/elfa-ai/elfa-sdk-python/issues)

## License

MIT — see [LICENSE](LICENSE).
