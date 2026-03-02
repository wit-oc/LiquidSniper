# Phase 1 — HTF Structure / Bias (Deterministic)

Scope: **structure only**. No entries, triggers, risk, or execution logic.

## Regime model

Persistent regime state has no neutral trading state:

- `regime_direction`: `bullish | bearish`
- `regime_confidence`: `confirmed | transitional`
- `transition_reason`: `choch_detected | bos_confirmed`

Behavior:

1. A CHoCH against the currently protected level flips direction into `transitional`.
2. Transitional regime becomes `confirmed` only on BoS confirmation in that same direction.
3. CHoCH is one-shot per protected level and only re-arms after a new protected level is locked.

## Anchoring rules

- Swing pivots are detected with `(left, right)` lookback/lookforward.
- Swing event is anchored to the **confirmation candle index** (`pivot_index + right`).
- CHoCH/BoS/Reversion events are anchored to the candle whose close triggered the break.

## Python implementation

- Engine module: `intraday_revisit/engine/htf_phase1.py`
- Main entrypoint: `run_phase1_htf_structure(highs, lows, closes, left, right, initial_direction)`
- Output:
  - per-bar log (`bars_log`)
  - event log (`events_log`)
  - swing log (`swings_log`)

## TradingView implementation

- Indicator: `intraday_revisit/pine/HTF_Phase1_Structure.pine`
- Displays:
  - optional pivot labels (`SH`, `SL`)
  - CHoCH, BoS, and SFP markers
  - active swing high + active swing low lines
  - regime direction + confidence table
- Markers are plotted on event bars; SFP uses a circle at the SFP candle extreme.

## Validation steps (reproducible)

### Python

```bash
cd /Users/wit/.openclaw/workspace
pytest -q intraday_revisit/tests/test_htf_phase1.py
```

Expected:
- Tests pass
- Deterministic output test (`a == b`) passes
- Transition semantics pass:
  - CHoCH => transitional
  - BoS => confirmed
  - CHoCH one-shot per protected level

### Artifact generation check

```bash
cd /Users/wit/.openclaw/workspace
python - <<'PY'
import json
from intraday_revisit.engine.htf_phase1 import run_phase1_htf_structure

highs = [10,11,12,11,12,13,12,11,10,9,8]
lows  = [9.0,9.5,10.0,9.2,9.7,10.4,9.6,9.0,8.8,8.5,8.0]
closes= [9.5,10.6,11.4,9.6,11.3,12.5,10.0,9.1,8.7,8.3,7.9]

bars, events, swings = run_phase1_htf_structure(highs, lows, closes, left=1, right=1, initial_direction='bullish')
print(json.dumps({'events': events, 'last_bar': bars[-1], 'swing_count': len(swings)}, indent=2))
PY
```

Expected:
- A CHoCH event appears first (bearish transitional)
- A later BoS event confirms bearish regime

### TradingView visual cross-check

1. Open TradingView chart (HTF pair/timeframe).
2. Paste `HTF_Phase1_Structure.pine` into Pine Editor and add to chart.
3. Confirm:
   - Optional SH/SL pivots appear only after pivot confirmation lag.
   - CHoCH marker appears on break candle and shifts table to transitional.
   - BoS marker appears on follow-through break candle and table returns to confirmed.
   - SFP marker (circle) is plotted at the sweep candle extreme.
   - BoS line starts from prior validated swing level and ends at break candle.
   - CHoCH line starts from protected level and ends at break candle.
