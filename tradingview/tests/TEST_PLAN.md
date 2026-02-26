# TradingView Strategy Test Plan (Manual Fast Loop)

Use this plan with `tradingview/results/run_log.csv`.

## Objective
Evaluate incremental strategy changes against baseline with minimal manual overhead.

## Ground Rules
1. One run = one row in CSV.
2. Do not stack changes unless the row says cumulative.
3. Keep symbol/TF/window fixed for this batch (`BTCUSDT`, `4H`, `2022-01-01 -> now`).
4. Always keep a control row (`B0`) populated.

## What to edit manually in TradingView each run
Use row values from CSV for these fields:
- Allow Longs / Allow Shorts
- Trigger Score
- Score Gate Min
- HTF Chop Hard Max
- HTF Chop Penalty Max
- ATR Stop Mult
- TP (R)
- Cooldown Bars

## What to copy back into CSV after each run
From Strategy Tester:
- `net_pnl_pct`
- `net_pnl_usdt`
- `profit_factor`
- `max_dd_pct`
- `max_dd_usdt`
- `total_trades`
- `win_rate_pct`
- `avg_trade_pct`
- `commission_usdt`

## Required columns for change tracking
- `baseline_id`: anchors comparison target (`B0`)
- `is_control`: true only for baseline/control rows
- `delta_summary`: human-readable experiment intent
- `value_changes`: explicit "old -> new" value change statement

## Current run order
1. `B0` (control)
2. `P1-LONG`
3. `A2-LONG`
4. `B2-LONG`
5. `C2-LONG`

## Decision gate (quick)
A run is a candidate improvement if:
- `profit_factor` improves vs baseline, and
- `max_dd_pct` does not materially worsen (> +25% relative), and
- `total_trades` remains non-trivial (>= 30 for this window).

Use scorer script after each batch:

```bash
python3 tradingview/scripts/score_runs.py tradingview/results/run_log.csv
```
