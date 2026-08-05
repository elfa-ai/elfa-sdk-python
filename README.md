# Elfa AI Python SDK

[![PyPI version](https://badge.fury.io/py/elfa-sdk.svg)](https://badge.fury.io/py/elfa-sdk)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Python SDK for the Elfa API v2 — social intelligence, AI chat, and the Auto/Trade engines for crypto. Sync and async clients, fully typed with Pydantic.

## Features

- **Social intelligence** — trending tokens, mentions, narratives, smart stats, event summaries
- **AI chat** — market analysis and conversational chat via `client.chat`
- **Auto condition engine** — build EQL queries that notify or trade via `client.auto`
- **Direct trading** — place orders and manage positions via `client.trade`
- **Sync and async** — `ElfaClient` and `AsyncElfaClient`, same surface
- **Typed** — Pydantic v2 models, full type hints
- **Robust** — retries with backoff, typed errors, HMAC request signing

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
    hmac_secret=None,                # required for Auto/Trade mutations (see below)
    headers=None,                    # extra headers sent on every request
)

# Quick reachability/auth check
assert client.test_connection() is True
```

The Auto and Trade engines are also constructable standalone if you only need one:

```python
from elfa import TradeClient

trade = TradeClient(api_key="your-api-key", hmac_secret="your-hmac-secret")
# ... use trade.place_order(...) etc.
trade.close()
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

Time-ranged endpoints accept either `time_window="24h"` or both `from_time` and `to_time` (unix seconds).

## Auto condition engine (`client.auto`)

Build [EQL](https://docs.elfa.ai) queries that watch conditions and fire actions (notify, webhook, or trade). Notification-only queries need no secret; trade-action queries require an `hmac_secret`.

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

Also available: `chat`, `list_queries`, drafts (`list_drafts`/`get_draft`/`upsert_draft`/`delete_draft`/`validate_draft`/`convert_draft`), `list_sessions`/`get_session`, `list_executions`/`get_execution`, exchanges (`list_exchanges`/`connect_exchange`/`disconnect_exchange`), and `validate_symbol`.

### Streaming notifications (SSE)

```python
for event in client.auto.stream_query(query_id):
    print(event.event, event.data)

# async
async for event in async_client.auto.stream_all():
    print(event.event, event.data)
```

## Direct trading (`client.trade`)

Trade a Privy-linked exchange account. All writes require an `hmac_secret`; previews do not execute and are free. **Sizes and prices are decimal strings.**

```python
client = ElfaClient(api_key="your-api-key", hmac_secret="your-hmac-secret")

preview = client.trade.preview_order({
    "exchange": "hyperliquid", "symbol": "BTC",
    "side": "buy", "orderType": "market", "size": "0.001",
})

if preview.would_execute:
    result = client.trade.place_order({
        "exchange": "hyperliquid", "symbol": "BTC",
        "side": "buy", "orderType": "market", "size": "0.001",
    })
    print(result.order_id, result.filled_size, result.avg_fill_price)
```

Methods: `preview_order`, `place_order`, `cancel_order`, `modify_order`, `preview_close_position`, `close_position`, `preview_set_position_tpsl`, `set_position_tpsl`.

## HMAC signing

Auto trade-action queries and all `client.trade` writes are signed when `hmac_secret` is set. The SDK builds the signature over `timestamp + METHOD + mounted_path + body` and sends `x-elfa-timestamp` and `x-elfa-signature` headers. Signing every mutation is safe, so passing `hmac_secret` is always fine. Generate a secret in the [dev portal](https://docs.elfa.ai).

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

Live integration tests run only when `ELFA_API_KEY` is set (optionally `ELFA_BASE_URL`, `ELFA_HMAC_SECRET`); otherwise they skip.

## Support

- [Documentation](https://docs.elfa.ai)
- [Issues](https://github.com/elfa-ai/elfa-sdk-python/issues)

## License

MIT — see [LICENSE](LICENSE).
