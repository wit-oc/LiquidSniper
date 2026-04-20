# Swing SR Zone Engine — Pass 1 + Pass 2 (TV Alpha)

## Files updated
- `tradingview/indicator/liquidsniper_swing_indicator_v1_alpha.pine`
- `tradingview/strategy/liquidsniper_swing_strategy_v1_alpha.pine`

## Pass 1 delivered (zone subsystem)
- Added horizontal SR zone engine using pivot-based clustering (array-backed):
  - zone fields: top/bottom/mid, type, touches, last_touch
  - merge logic (`sr_merge_bps`)
  - width control (`sr_zone_half_bps`)
  - aging + touch threshold filters (`sr_max_age_bars`, `sr_min_touches`)
  - max zone storage + weakest replacement (`sr_max_zones`)
- Added nearest active support/resistance discovery:
  - `nearest_res_dist_pct`, `nearest_sup_dist_pct`
  - `nearest_res_top/bot`, `nearest_sup_top/bot`
- Added first-retest state machine on real zones:
  - break -> separation -> consolidation -> first return
  - tunables: `sr_retest_sep_bps`, `sr_retest_cons_min`, `sr_retest_cons_max`, `retest_window_bars`

## Pass 2 delivered (wired into gates)
- Gate pipeline now uses SR zones directly:
  - Opposing-level hard block (`sr_opposing_block_pct`)
  - Optional hard first-retest gate (`require_first_retest`)
- Scoring now includes zone proximity confluence (`sr_confluence_dist_pct`) instead of EMA50 SR proxy.
- Strategy stop reference now prefers zone-based invalidation fallback.

## Diagnostics added
- Gate waterfall counters:
  - candidates
  - fail HG1..HG6
- Added zone/diagnostic telemetry to strategy label + indicator debug table.

## New key inputs
- `sr_zone_half_bps`
- `sr_merge_bps`
- `sr_min_touches`
- `sr_max_age_bars`
- `sr_max_zones`
- `sr_opposing_block_pct`
- `sr_confluence_dist_pct`
- `sr_retest_sep_bps`
- `sr_retest_cons_min`
- `sr_retest_cons_max`

## Notes
- This is still TV Alpha quality (scaffold + diagnostics). The core SR process is now real-zone based, but thresholds remain empirical.
- Next validation step: TradingView visual check that created zones align with meaningful rejections before performance interpretation.
