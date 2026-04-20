# TradingView ↔ Paper Bot Parity Matrix (v1)

## Scope
This document tracks execution-model alignment between:
- TradingView Pine strategy (`tradingview/strategy/liquidsniper_confluence_strategy.pine`)
- Paper bot runner (`liquidsniper/ops/paper_daemon.py`)

## Canonical posture
Current decision: **Pine strategy is canonical for performance validation**.
Paper bot should align where practical.

## Alignment status

### Signal/Gating
- Profile defaults (C/I/S): aligned.
- Score formula shape (`6 + 0.7*secondary - chop_term - penalties`): aligned.
- SR source: **not aligned** (Pine uses EMA proxy; paper uses SR zone engine).

### Exits/Trade lifecycle
- Long TP/SL directionality: aligned.
- Short TP directionality: **fixed in v1** (TP levels now below entry for shorts).
- Break-even behavior:
  - Pine: configurable (`be_enabled`, `be_trigger_r`, `be_offset_pct`).
  - Paper: now promotes to BE on TP1 price touch (not cycle-age based).

### Throttles
- Paper: cooldown seconds, daily caps, daily loss, active risk caps.
- Pine: bar cooldown only.
- Status: partially aligned by intent, not by full mechanics.

### PnL semantics
- Paper proposal seeded pnl is now explicitly diagnostic (`diagnostic_pnl_seed_usd`).
- Proposal `pnl_usd` set to `0.0`; realized close PnL remains canonical performance metric.

## Remaining known divergences
1. SR context source differences (engine vs proxy).
2. Full throttle model parity not implemented in Pine.
3. Fill semantics differ (TV backtester vs cycle mark-price simulation).

## Validation checklist
- [ ] Long TP/SL behavior sanity checks
- [ ] Short TP/SL behavior sanity checks
- [ ] BE transition sanity checks
- [ ] Trade-count + DD shifts after short-TP fix
