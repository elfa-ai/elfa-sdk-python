# Changelog

All notable changes to `elfa-sdk` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versions track the [JavaScript SDK](https://github.com/elfa-ai/elfa-sdk-js) where
the two cover the same API surface, so a breaking change to the API bumps both.
They are not lockstep: an SDK-only fix ships in one without the other.

## 6.2.0

### Added

- **Rank top accounts by track record.** `AccountMetricV3` now takes
  `alphaScore`, `hitRate` and `avgReturn` beside `standing` (API 2.11.0), so
  `client.v3.get_top_accounts(metric="alphaScore")` type-checks. Track metrics
  rank only accounts with at least 20 scored positions, and a `next_cursor`
  works only with the `metric` and `order` it came from.

### Changed

- `swagger.json` refreshed from API `2.10.0` to the published `2.11.0`.
- The empty-list `ElfaValidationError` names the parameter, e.g.
  `entity_ids is empty, which would drop the filter.`

### Fixed

- `chat()` drops a malformed `sources` list instead of raising, as `chat_stream()`
  already did, so a bad source entry never costs you the answer.

## 6.1.0

### Added

- **API v3 on `client.v3`.** `ElfaClient.v3` (`V3Client`) and
  `AsyncElfaClient.v3` (`AsyncV3Client`) cover the fourteen `/v3` endpoints,
  sharing the parent's transport, retries, timeout, headers and `app_name`.
  Both are also exported for standalone use, like `AutoClient`:
  `get_entities`, `get_events`, `get_storylines`, `get_arcs`,
  `get_call_book(market, ...)`, `get_mindshare(market, ...)`,
  `get_trending_contracts`, `get_calls`, `get_call_episodes`,
  `get_positioning(entity_id)`, `get_top_accounts` and `get_key_status`.
  Parameters are snake_case (`from_time`/`to_time` for `from`/`to`), list
  parameters take Python lists and are sent comma-separated (an empty list
  raises `ElfaValidationError` instead of dropping the filter), and only the
  parameters you set are sent. Responses are typed in `elfa.models.v3`. PAYG,
  Grow and Enterprise keys can call every v3 endpoint; a Free key can call only
  `get_key_status`.
- **`include_sources` on `chat` and `chat_stream`.** Sends `includeSources`;
  the links the research read come back as `ChatResponse.data.sources` and as
  `sources` on the stream's final `complete` event (`ChatSource`: `url`,
  `kind`, optional `title`). `kind` is a plain string: treat a value you do not
  recognise as `web`.

### Removed

- **`"gmx"` is no longer a `TradableExchange`.** The published
  `GET /v2/auto/validate-symbol/{exchange}/{symbol}` enum is now
  `hyperliquid | binance`. Passing `"gmx"` to `validate_symbol` now fails type
  checking; the API already rejected it, so no working call changes.

### Changed

- `swagger.json` refreshed from API `2.7.0` to the published `2.10.0`: adds
  the `/v3` endpoints and chat `includeSources`, drops `gmx` from the exchange
  enums and `/v2/data/market-events` from the spec. The SDK never wrapped
  market events, so no method changes.

### Fixed

- **`ElfaValidationError.validation_errors` now carries the API's `details`.**
  A `400` names the failing field in `details` (for example `query.from`,
  `from is required`), and `message` alone often reads `Invalid parameters`.
  The SDK only read an `errors` key, so `validation_errors` was always `None`.
  The field and reason are now also appended to the error message, so
  `str(error)` says what to fix.

## 6.0.0

### Removed

- **HMAC request signing has been removed.** The `hmac_secret` argument is gone
  from `ElfaClient`, `AsyncElfaClient`, `AutoClient` and `AsyncAutoClient`, and
  `elfa.utils.sign_request` no longer exists. `/v2/auto/*` routes are no longer
  documented as taking `x-elfa-timestamp` or `x-elfa-signature`; the API key
  alone authenticates every route, including mutations.

  **Migration:** drop `hmac_secret=` from your client construction. Nothing
  replaces it. Passing it now raises `TypeError`, and the header was already
  redundant on every documented action type.

  Request bodies are unchanged: Auto mutations still send compact JSON through
  httpx `content=`, so the bytes on the wire are the same minus the two headers.

- **`"pacifica"` is no longer a `TradableExchange`.** The published
  `GET /v2/auto/validate-symbol/{exchange}/{symbol}` enum is now
  `hyperliquid | gmx | binance`. Passing `"pacifica"` to `validate_symbol` now
  fails type checking; it would have been rejected by the API regardless.

### Added

- **`app_name` adds your product to the `User-Agent`.** Pass
  `app_name="my-bot/1.2"` to `ElfaClient`, `AsyncElfaClient`, `AutoClient` or
  `AsyncAutoClient` and every request carries
  `User-Agent: elfa-sdk-python/6.0.0 my-bot/1.2`. A composed `client.auto`
  shares the parent's value. It must be 1-100 printable ASCII characters;
  anything else raises `ElfaValidationError` at construction.

### Changed

- A `User-Agent` passed in `headers` now replaces the SDK's own in any casing.
  Before, `headers={"user-agent": ...}` sat next to the SDK's `User-Agent`
  instead of replacing it.
- Internal: `SignedClient` is now `MountedClient`, since all it does is join the
  mount prefix to the path. It was never exported from `elfa`.
- `swagger.json` refreshed to API `2.6.3`. A credit is now $0.0145, so the x402
  reference prices in the spec move to $0.0145 (1 credit), $0.0725 (5 credits)
  and $0.261 (18 credits). Accounts already on PAYG keep $0.009 per credit until
  28 September 2026, 16:00 UTC. Pricing affects documentation strings only — no
  signature changes.

## 5.1.0

### Added

- **`AutoChatResponse.credits`** — `POST /v2/auto/chat` returns the credits the
  call cost, and the model now declares it. Optional, so responses from older
  API deployments still parse. The same total is on the `x-elfa-credits`
  response header that every v2 route now sends. Builder Chat is dynamically
  priced, so read this instead of assuming a flat per-call cost.

  Nothing broke before this: the models are `extra="allow"`, so `credits`
  already arrived — it just landed in `model_extra` instead of being a declared
  field. Code reading `response.credits` worked then and works now. Code
  reaching into `response.model_extra["credits"]` explicitly will now raise
  `KeyError`, since a declared field is no longer an extra.

### Note on response shapes

The SDK does not reject unknown response fields — `ElfaModel` sets
`extra="allow"`, so fields the API adds are kept and reachable via
`model_extra`. Treat v2 response bodies as extensible: do not re-validate them
with `extra="forbid"` or an exact-shape assertion, or an additive field like
`credits` will break your client even though the API did not.

## 5.0.0

### Removed

- **Auto exchange connections have been removed.** `client.auto.list_exchanges`,
  `connect_exchange` and `disconnect_exchange` are gone from both the sync and
  async clients, along with the `AutoExchangeConnection` and
  `AutoListExchangesResponse` models. Exchange connections are no longer part of
  the documented Auto surface.

### Kept

- `client.auto.validate_symbol` and `TradableExchange`. The symbol check is
  still documented as a pre-flight for `price` / `ta` conditions and still
  accepts all four venues.

## 4.0.0

### Removed

- **`client.trade` and the `TradeClient` / `AsyncTradeClient` pair have been
  removed.** The `/v2/trade/*` paths are not part of the published Elfa API
  surface, so every method on them — `preview_order`, `place_order`,
  `cancel_order`, `modify_order`, `preview_close_position`, `close_position`,
  `preview_set_position_tpsl`, `set_position_tpsl` — called an endpoint that is
  no longer documented. The `elfa.models.trade` models (`TradeExchange`,
  `TradeOrderType`, `TradeSide`, `PlaceOrderInput`, `CancelOrderInput`,
  `ModifyOrderInput`, `ClosePositionInput`, `SetPositionTpslInput`,
  `TradeErrorDetail`, `TradeResultResponse`, `TradePreviewResponse`) are gone
  too. Place orders through Auto trade actions via `client.auto` instead.

### Added

- **`chat_stream`** — AI chat delivered incrementally over Server-Sent Events
  (`POST /v2/chat/stream`), on both `ElfaClient` (a generator) and
  `AsyncElfaClient` (an async generator). Yields `ChatStreamEvent`, the parsed
  `data:` frame carrying `type` plus the payload as extras. Keep-alive comments
  and unparsable frames are skipped, and iteration ends on the terminating
  `[DONE]` frame. Requires a PAYG or Enterprise key.

### Changed

- `hmac_secret` now signs Auto mutations only — there are no trade writes left
  to sign.

## 3.0.0

First published release. The SDK starts at 3.0.0 to line up with the JavaScript
SDK's major, which had already dropped V1; there is no 1.x or 2.x on PyPI.

### Added

- Sync `ElfaClient` and async `AsyncElfaClient` over the V2 API: keyword and top
  mentions, account smart stats, trending tokens, trending contract addresses
  (X and Telegram), token news, trending narratives, event summaries, key status
  and AI chat.
- `client.auto` — the Auto condition engine (`/v2/auto/*`): builder chat, query
  validate/create/list/get/cancel/delete, drafts, sessions, executions, exchange
  connections, symbol validation, and SSE notification streams.
- `client.trade` — direct trading (`/v2/trade/*`): orders and positions with
  previews. Removed in 4.0.0.
- HMAC request signing via the `hmac_secret` option.
- Typed responses via Pydantic models that accept unknown fields, retries with
  backoff, and typed exceptions (`ElfaAPIError`, `ElfaAuthenticationError`,
  `ElfaRateLimitError`, `ElfaValidationError`, `ElfaNotFoundError`,
  `ElfaNetworkError`, `ElfaTimeoutError`).
