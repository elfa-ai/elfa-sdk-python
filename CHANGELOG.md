# Changelog

All notable changes to `elfa-sdk` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versions track the [JavaScript SDK](https://github.com/elfa-ai/elfa-sdk-js) where
the two cover the same API surface, so a breaking change to the API bumps both.
They are not lockstep: an SDK-only fix ships in one without the other.

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
