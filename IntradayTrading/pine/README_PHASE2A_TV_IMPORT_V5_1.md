# Phase2A S/R Watcher V5.1 — Candidate Bypass Addendum

## File
- `IntradayTrading/pine/PHASE2A_SR_WATCHER_V5_1_TIME_NORMALIZED_REACTION_MODEL.pine`

V5.1 adds an escape hatch for candles that fail candidate prefilter but have strong expedition behavior.

## New inputs
- `Allow strong expedition bypass of candidate gate`
- `Bypass min move (ATR)`
- `Bypass min persistence bars`
- `Bypass requires no-revisit`

## Why
This captures the “small setup candle, major next-candle/multi-candle rejection” cases without globally relaxing candidate filters.

## Debug
Table row `Cand / passBase / kept / bp` shows bypass-used count (`bp`).

Inspect rows still show per-side fail code and metrics for a chosen candle.
