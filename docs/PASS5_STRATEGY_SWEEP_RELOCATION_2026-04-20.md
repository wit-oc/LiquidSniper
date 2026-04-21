# Pass 5, Strategy Sweep Relocation

Date: 2026-04-20  
Status: third real legacy-surface relocation after the Telegram ingestor and TradingView moves

This pass relocates the historical strategy-sweep tooling into an explicit legacy
home while preserving the original `tools/strategy_sweep/` path for existing
tests, scripts, and sample commands.

---

## What changed

Moved canonical home from:
- `tools/strategy_sweep/`

Moved canonical home to:
- `legacy/strategy_sweep/`

Compatibility kept via:
- symlink `tools/strategy_sweep -> ../legacy/strategy_sweep`

Why this shape was chosen:
- tests import the sweep engine by inserting `tools/strategy_sweep` into `sys.path`
- scripts and sample commands still point directly at the old path
- moving without a compatibility path would have been churn for no gain

---

## What remains true after this pass

- old file paths under `tools/strategy_sweep/` still resolve
- the legacy home is now explicit
- historical generated outputs remain archived under `artifacts/archive/2026-04-20-second-pass/strategy-sweep-outputs/`

---

## Still pending after this pass

1. classify paper-runtime code into retain vs legacy vs delete buckets
2. decide whether any paper-runtime primitives should stay in-place as reusable shared code
3. only consider repo rename once the paper-runtime knot is untangled enough that the code tree matches reality
