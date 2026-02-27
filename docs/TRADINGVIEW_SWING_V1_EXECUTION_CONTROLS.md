# TradingView Swing v1 — Execution Controls, Hysteresis, and Toggle Semantics

Applies to:
- `tradingview/strategy/liquidsniper_swing_strategy_v1_alpha.pine`
- Current logic version line: `tv-swing-strategy-v1.3.0-alpha`

## 1) What "hysteresis" means here

In this strategy context, **hysteresis** means adding a small amount of "memory" so the system does not immediately re-trigger/flip on noisy persistence.

### Practical forms used now

1. **Temporal hysteresis (entry edge mode)**
   - We only treat a signal as new on a `false -> true` transition (`trigger_edge`), not every bar where condition remains true.
   - Effect: removes repeated bar-level re-firing from persistent conditions.

2. **Directional hysteresis (flip on opposite edge)**
   - Reversal is allowed only on an **opposite edge event** (not on every opposite trigger bar).
   - Effect: avoids churn from condition persistence while still allowing regime changes.

### Why this matters
- Lower churn and duplicate attempts.
- Cleaner diagnostics (unique opportunities vs repeated bars).
- Better slot utilization without blindly loosening quality gates.

---

## 2) Surface toggles and what they change

## 2.1 Entry/flip behavior toggles (primary)

| Toggle | Options / Default | Behavior change |
|---|---|---|
| `entry_signal_mode` | `edge` (default), `bar` | `edge`: entry attempts only on false->true events. `bar`: attempt every trigger bar. |
| `allow_flip_on_opposite_edge` | `true` (default), `false` | If `true`, opposite edge can reverse an open position; if `false`, open position blocks opposite-side entry. |
| `cooldown_bars` | int, default `3` | Throttles re-entry attempts for N bars after a trade action. |

## 2.2 Risk/lock controls affecting entry availability

| Toggle | Default | Behavior change |
|---|---:|---|
| `enable_daily_loss_cb` | `true` | Blocks new entries when daily realized-R loss threshold is exceeded. |
| `max_daily_loss_r` | `2.0` | Daily loss lock threshold (R units). |
| `enable_daily_trade_cap` | `false` | Optional max trades/day lock. |
| `max_daily_trades` | `3` | Trades/day when daily cap is enabled. |

## 2.3 Signal strictness controls (major throughput drivers)

| Toggle | Default | Behavior change |
|---|---:|---|
| `trigger_score` | `6.0` in active test runs (input-driven) | Higher = fewer entries, usually better selectivity. |
| `require_first_retest` | `false` | If `true`, first retest becomes hard gate (strongly reduces count). |
| `enforce_opposing_zone_block` | `false` | If `true`, opposing zone proximity is hard reject; if `false`, scored/penalized context. |
| `sr_opposing_block_mode` | `ATR-relative` | Opposing block threshold scales by ATR (or fixed % if switched). |
| `sr_opposing_block_atr_mult` | `1.0` | Sensitivity of ATR-based opposing threshold. |

---

## 3) Diagnostics rows (bottom-right box)

The strategy diagnostics table is the source of truth for entry starvation analysis.

Key rows:
- `WF C/H1/H2/H3/H4/H5/H6`: global first-fail waterfall.
- `L C/P/...` and `S C/P/...`: per-side pass/fail decomposition.
- `PostHG ... trigBars/trigEdges/entrySig/rgBlk/qtyFail/entry`: post-gate execution funnel.
- `Block ... open/cooldown/dLoss/dCap`: explicit blocker reasons.

Interpretation rule:
- Prefer `trigEdges`/`entrySig` for unique opportunity count.
- Treat `trigBars` as condition persistence volume.

---

## 4) Recommended default operating posture (current)

- `entry_signal_mode = edge`
- `allow_flip_on_opposite_edge = true`
- `enforce_opposing_zone_block = false`
- Keep daily loss lock on
- Keep diagnostics box on during tuning

This favors controlled throughput and stable drawdown behavior while avoiding duplicate re-fire noise.

---

## 5) Next optional hysteresis hardening (not yet implemented)

Potential additional control:
- `flip_min_score_delta` (float): require opposite-side score to exceed current-side score by a margin before flip.

Why:
- Adds amplitude hysteresis on top of edge hysteresis.
- Reduces flip churn in marginal/choppy regimes.
