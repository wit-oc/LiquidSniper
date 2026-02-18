# Data Feed Strategy v1 (LiquidSniper)

Status: Proposed canonical strategy feed architecture (2026-02-18)  
Owner: Redact + Wit  
Scope: Paper-MVP feed architecture for strategy-grade analysis (Blofin + on-chain roadmap compatible)

---

## 1) Problem we are solving

The current system can ingest liquidity-alert triggers (Mobchart via Telegram), but your strategy depends on deterministic candlestick structure/POI analysis.

Therefore:
- trigger streams alone are not sufficient,
- canonical OHLCV must become the strategy decision baseline,
- optional context sources (TradingView screenshots/webhooks, order-book overlays) must not be mistaken for canonical market data.

---

## 2) Decision summary

### Canonical decision feed

- **Use direct exchange OHLCV as the canonical strategy feed.**
- **CCXT-first integration** for breadth and speed.
- **Native adapter fallback** for Blofin if/when CCXT coverage is insufficient.

### Secondary/optional feeds

- Mobchart Telegram alerts -> trigger/context overlay only.
- TradingView screenshots/webhooks -> qualitative/context artifacts only.
- Optional real-time microstructure stream (Cryptofeed/direct WS) -> later uplift, not required for paper-MVP strategy correctness.

---

## 3) Option posture (free feed paths)

## Option A — CCXT-first OHLCV

- Why for:
  - fastest path to multi-venue OHLCV with one interface,
  - fits existing Python + deterministic replay architecture,
  - easiest way to unblock HTF-anchor and score-engine implementation.
- Why against:
  - exchange abstraction leaks and venue quirks,
  - potential metadata gaps for niche derivatives fields,
  - REST-only polling can be less ideal for sub-minute sensitivity.

## Option B — Cryptofeed-first real-time stream

- Why for:
  - normalized websocket market data with broad channel support,
  - better real-time event coverage for future latency-sensitive layers,
  - strong long-term event-bus posture.
- Why against:
  - higher architecture/ops complexity now,
  - heavier lift than needed for immediate HTF/POI strategy baseline,
  - venue support fit must be verified against target exchanges.

## Option C — Direct exchange APIs only

- Why for:
  - maximum control and venue-specific correctness,
  - explicit handling of exchange-specific risk/rate semantics,
  - best when one venue is primary and policy constraints are strict.
- Why against:
  - highest maintenance burden,
  - repeated normalization work for each venue,
  - slower MVP velocity.

## Recommended hybrid for LiquidSniper

1. **CCXT-first canonical OHLCV**
2. **Native Blofin adapter fallback (conditional, behind provider interface)**
3. **Cryptofeed/direct WS optional uplift layer later**

---

## 4) Source roles (Now / Next / Later / Blocked)

## Now (required for strategy correctness)

- Canonical OHLCV feed for strategy timeframes (`1m`, `5m`, `15m`, `1H`, `4H`, `1D`, `1W`)
- Existing Telegram/Mobchart trigger feed retained as context overlay

## Next (high-value hardening)

- Funding + OI snapshots for futures context
- Feed quality gates (gap detection, stale detection, dedupe)

## Later (performance uplift)

- Real-time book/trade stream overlay for execution-quality modifiers
- Cross-source reconciliation (REST candles vs stream-derived candles)

## Blocked / explicitly out of scope for current paper-MVP

- TradingView scraping as canonical candle source
- Any feed path that bypasses deterministic replay/audit requirements

---

## 5) Integration architecture contract

## 5.1 Provider interface

Introduce a `MarketDataProvider` abstraction with deterministic semantics:

- `fetch_ohlcv(symbol, timeframe, since, limit) -> candles[]`
- `fetch_funding(symbol, since, limit) -> funding[]` (optional)
- `fetch_open_interest(symbol, since, limit) -> oi[]` (optional)
- `provider_health() -> {status, reason_codes, rate_state}`

Implementation set:
- `CcxtMarketDataProvider` (default)
- `BlofinNativeMarketDataProvider` (conditional fallback)

## 5.2 Storage contract

Canonical persisted domains:
- `market_candles`
- `market_funding_snapshots` (optional)
- `market_open_interest_snapshots` (optional)
- `feed_health_events`

All rows must carry:
- `provider_id`
- `venue`
- `symbol`
- `timeframe`
- `ts_open`
- `ts_close`
- `ingest_ts`
- `trace_id` / `dataset_version`

## 5.3 Strategy-decider contract

- Strategy score path consumes canonical candle store, not Telegram payload directly.
- Telegram/Mobchart contributes optional trigger/priority context only.
- If canonical candles for required windows are stale/missing -> fail closed (`watch_only`/`reject`).

---

## 6) Rate-limiting and reliability policy

## Polling policy

- Poll on candle-close cadence, not continuous hot-loop polling.
- Stagger symbols/timeframes by schedule buckets.
- Prefer deriving higher TF candles locally from lower TF when quality thresholds pass.

## Guardrails

- Per-provider token-budget manager.
- Exponential backoff + jitter on 429/5xx.
- Circuit breaker per venue/provider after repeated quota or integrity failures.
- Health state surfaced to decision engine; degraded state blocks promotion.

## SLO targets (paper-MVP)

- Candle freshness within configured tolerance per timeframe.
- Missing-candle gap rate below threshold.
- Deterministic replay parity from frozen candle snapshots.

---

## 7) Feature cuts / reprioritization for this lane

Deprioritize until canonical feed baseline is complete:
- New TradingView automation features beyond current artifact-linking contract.
- Additional discretionary signal enrichments that do not improve deterministic OHLCV/POI correctness.
- New UI polish features not required for feed-health and decision traceability.

Keep:
- Existing Mobchart ingestion path (as trigger overlay).
- Existing replay harness and decision persistence path.

---

## 8) Work packages (anchored tasks)

This strategy introduces/anchors the following implementation tasks:

- Task 19 — Market data provider contract + canonical candle schema
- Task 20 — CCXT OHLCV backfill + incremental scheduler
- Task 21 — Candle quality gates + timeframe aggregation policy
- Task 22 — Strategy feed integration (canonical candles as decision baseline)
- Task 23 — Rate-limit/circuit-breaker controls + feed health events
- Task 24 — Trigger feed decoupling (Mobchart as context, not core)
- Task 25 — Native Blofin adapter fallback (conditional)
- Task 26 — Feed benchmark + paper-MVP gate evidence

---

## 9) Go/No-Go linkage

Paper-MVP progression requires:
- canonical OHLCV coverage for required symbols/timeframes,
- deterministic feed-health gates in place,
- replay parity for strategy outputs,
- unresolved operator dependency stubs still enforcing fail-closed boundaries.

No progression beyond paper mode is allowed solely from trigger-feed availability.
