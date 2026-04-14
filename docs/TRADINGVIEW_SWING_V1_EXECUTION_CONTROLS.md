# TradingView Swing v1 — Execution Controls, Hysteresis, and Toggle Semantics

Applies to:
- `tradingview/strategy/liquidsniper_swing_strategy_v1_alpha.pine`
- Current logic version line: `tv-swing-strategy-v1.6.0-alpha`

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
| `flip_min_score_delta` | float, default `0.5` | **Amplitude hysteresis**: opposite edge must exceed current-side score by this margin before flip is allowed. |
| `cooldown_bars` | int, default `3` | Throttles re-entry attempts for N bars after a trade action. |

## 2.2 TP / realization controls (capital velocity)

| Toggle | Default | Behavior change |
|---|---:|---|
| `tp1_qty_pct` | `40` | Nominal TP1 allocation (auto-normalized with TP2/TP3). |
| `tp2_qty_pct` | `30` | Nominal TP2 allocation (auto-normalized with TP1/TP3). |
| `tp3_qty_pct` | `30` | Nominal TP3 allocation (auto-normalized with TP1/TP2). |
| `enforce_tp3_rr_floor` | `false` | If `true`, TP3 uses `max(rr_target, tp3_rr_floor)`; if `false`, TP3 uses `rr_target` directly. |
| `tp3_rr_floor` | `3.0` | Floor value used only when TP3 floor enforcement is enabled. |

## 2.3 Lifecycle governor controls (slot/funding hygiene)

| Toggle | Default | Behavior change |
|---|---:|---|
| `enable_lifecycle_governor` | `true` | Master toggle for stale-trade cleanup and trend-invalidation exits. |
| `be_stale_reduce_bars` | `12` | If BE is active and TP2 not reached by this many bars, reduce position size. |
| `be_stale_reduce_pct` | `50` | Percent reduced on stale BE reduce action. |
| `be_stale_full_exit_bars` | `24` | If still stale after this many bars (BE active, TP2 not reached), close remainder. |
| `enable_trend_invalidation_exit` | `true` | Exits when HTF trend flips against position and profit cushion is insufficient. |
| `trend_invalidation_max_r` | `0.5` | Maximum unrealized R at which trend-invalidation exit is allowed. |

## 2.4 Risk/lock controls affecting entry availability

| Toggle | Default | Behavior change |
|---|---:|---|
| `enable_daily_loss_cb` | `true` | Blocks new entries when daily realized-R loss threshold is exceeded. |
| `max_daily_loss_r` | `2.0` | Daily loss lock threshold (R units). |
| `enable_daily_trade_cap` | `false` | Optional max trades/day lock. |
| `max_daily_trades` | `3` | Trades/day when daily cap is enabled. |

## 2.5 Signal strictness controls (major throughput drivers)

| Toggle | Default | Behavior change |
|---|---:|---|
| `trend_gate_mode` | `strict_dual` (default), `htf_primary` | `strict_dual`: require ITF+HTF alignment. `htf_primary`: require HTF alignment plus non-opposing structure state; usually increases throughput. |
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
- `LCycle ... reduce/full/trend`: lifecycle-governor action counts.
- Mode row now includes effective TP split (`TP=...`) and effective TP3 target R (`TP3R=...`).

Interpretation rule:
- Prefer `trigEdges`/`entrySig` for unique opportunity count.
- Treat `trigBars` as condition persistence volume.

---

## 4) Recommended default operating posture (current)

- `entry_signal_mode = edge`
- `allow_flip_on_opposite_edge = true`
- `flip_min_score_delta = 0.5`
- `enable_lifecycle_governor = true`
- TP split defaults: `40/30/30`
- `enforce_tp3_rr_floor = false` (TP3 follows `rr_target`)
- stale windows default: `12/24` bars (`reduce/full`)
- `enforce_opposing_zone_block = false`
- Keep daily loss lock on
- Keep diagnostics box on during tuning

This favors controlled throughput and stable drawdown behavior while avoiding duplicate re-fire noise.

---

## 5) Next optional hardening (post v1.6.0)

Potential additions:
- `flip_min_time_in_trade_bars`: require minimum hold time before opposite-edge flip.
- `flip_be_required`: only permit flips after BE is active on incumbent position.
- `be_stale_reduce_tier2`: second staged reduce before full stale exit.

Why:
- Further suppresses churn in chop.
- Keeps PF/DD protection explicit and measurable.
- Improves slot turnover control without lowering entry-quality gates.

---

## 6) Input audit status (swing-specific)

### 6.1 Removed as unnecessary
- `retest_bps` was removed in `v1.4.1-alpha` (legacy from EMA-anchor retest model; not used by SR zone engine).

### 6.2 Kept (necessary for swing intent)
- Structure / SR: `structure_swing_len`, `retest_window_bars`, `sr_*` zone/retest controls.
- Throughput/quality: `trend_gate_mode`, `trigger_score`, `require_first_retest`, chop controls.
- Execution cadence: `entry_signal_mode`, `allow_flip_on_opposite_edge`, `flip_min_score_delta`, `cooldown_bars`.
- Risk/slot hygiene: lifecycle governor set (`be_stale_*`, `enable_trend_invalidation_exit`, `trend_invalidation_max_r`), daily locks, stop floors.
- Position sizing: `sizing_mode`, risk percentages, high-conf threshold.

### 6.3 Candidate deprecations (not removed yet; awaiting explicit go-ahead)
These are still functional, but not obviously required for a pure swing-only strategy:
- `profile`, `enable_profile_risk_cap`, `enable_manual_profile_risk_caps`, `profile_cap_c/i/s`
  - Rationale: profile model came from mixed C/I/S flow; swing-only path may prefer a single risk-cap contract.
- `enable_time_block`, `blocked_session`, `blocked_tz`
  - Rationale: mostly intraday/session tooling; less relevant on strict 1D execution.
- `enable_short_adx_bump`, `short_adx_bump`
  - Rationale: asymmetry control; useful only if we intentionally keep short-side bias tuning.
- `enable_short_stop_mult`, `short_stop_mult_factor`
  - Rationale: asymmetry stop tuning; optional for swing baseline.

### 6.4 Metadata-only
- `ls_version` is intentionally metadata-only and used for operator traceability.

### 6.5 Audit rule for future cleanup
When considering removals, only drop an input if all are true:
1. It is not used in code path **or** its behavior is redundant with another control.
2. Removing it does not reduce ability to enforce PF/DD guardrails.
3. The behavior is either hard-coded or represented by a clearer single control.
4. Change is documented and version-bumped in strategy + guide.

