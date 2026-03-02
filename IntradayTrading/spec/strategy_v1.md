# Intraday Revisit Strategy v1 (Canonical Spec)

## Scope
- Symbols: BTC, ETH
- Venue model: Blofin Perps
- Timeframes: 4H structure context, 1H execution
- Session: 24/7
- Sides: Long + Short

## Core Principles
1. Structure-first: entries must align with 4H structure bias or explicit 4H transition.
2. Clean SR: zones derived from deterministic pivot/swing logic, persistent (no decay).
3. Retest discipline: break-retest confirmation preferred over raw breakout entries.
4. Risk-first: risk-based sizing (1% to 5%), TP1 then stop to BE, strict daily/weekly breakers.

## Zone Lifecycle
A zone has: `id`, `kind` (support/resistance), `low`, `high`, `created_at`, `state`.

States:
- `ACTIVE`: tradable zone.
- `FLIPPED`: support->resistance or resistance->support after validated break+retest.
- `INVALIDATED`: decisively broken beyond invalidation threshold.

Rules:
- Birth: from confirmed pivot cluster with minimum separation from existing zone.
- Merge: overlapping zones of same kind merge into envelope [min(low), max(high)].
- Persistence: no time-based expiration.
- Invalidation: close beyond zone boundary by configured threshold (ATR or percent) and no reclaim window.

## Structure Bias (4H)
- `BULLISH`: higher-high/higher-low regime.
- `BEARISH`: lower-low/lower-high regime.
- `NEUTRAL`: no clear directional structure.

Execution alignment:
- Longs allowed in BULLISH or on explicit bullish transition trigger.
- Shorts allowed in BEARISH or on explicit bearish transition trigger.

## Entry Contract (1H)
Long setup (short is symmetric inverse):
1. Price interacts with support zone (touch/penetration tolerance).
2. Reclaim/confirmation close back above zone threshold.
3. Optional filters pass (EMA/VWAP/ATR regime) if enabled.
4. Risk breaker state is `OPEN`.
5. At-risk slots available (`< 2`).

## Exit Contract
- Initial SL: structural invalidation reference + buffer.
- TP1: fixed R multiple (`tp1_r`, default 1.0R).
- On TP1 fill:
  - Move stop to break-even (`entry +/- costs_buffer`).
  - Position is no longer counted as "at-risk".
- TP2/final: fixed R multiple (`tp2_r`, default 2.5R) or opposing zone hit.

## Risk / Portfolio Rules
- Risk per trade configurable: 1% to 5% (default profile 1%).
- Max concurrent at-risk positions: 2.
- A position that has reached TP1 and moved SL->BE no longer consumes at-risk slot.
- Leverage default 3x (symbol/profile override allowed).

## Breakers
- Daily loss breaker: -6% of start-of-day equity -> lock new entries until next day.
- Weekly drawdown breaker: -20% of start-of-week equity -> lock new entries until next week.

## Cooldown (proposed)
- 3 consecutive losses per symbol+side => 6h soft cooldown for that lane.

## Determinism Requirements
- Bar-close semantics only.
- No lookahead in pivots/structure labeling.
- Full state transitions logged per bar.
- Same inputs + config => identical outputs.
