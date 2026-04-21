# Pass 4, TradingView Relocation

Date: 2026-04-20  
Status: second real code-surface relocation after the Telegram ingestor move

This pass relocates the TradingView surface into an explicit legacy home while
preserving existing file-path-based entrypoints.

---

## What changed

Moved canonical home from:
- `tradingview/`

Moved canonical home to:
- `legacy/tradingview/`

Compatibility kept via:
- repo-root symlink `tradingview -> legacy/tradingview`

Why this shape was chosen:
- the TradingView surface is used primarily through file paths, not Python imports
- docs, scripts, and operator steps still reference paths like:
  - `tradingview/scripts/score_runs.py`
  - `tradingview/results/run_log.csv`
  - `tradingview/tests/TEST_PLAN.md`
- a symlink preserves those paths without pretending the folder is still core

---

## What remains true after this pass

- old file paths under `tradingview/` still resolve
- the legacy implementation/artifact home is now explicit
- Surveyor / Arbiter core paths were not touched

---

## Still pending after this pass

1. decide whether `tools/strategy_sweep/` should also move under `legacy/`
2. sort paper-runtime code into retain vs legacy vs delete buckets
3. only consider repo rename once the code tree tells the truth more fully
