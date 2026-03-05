# Phase2A S/R Watcher V5 (Time-Normalized Reaction) — TradingView Import

## File
- `IntradayTrading/pine/PHASE2A_SR_WATCHER_V5_TIME_NORMALIZED_REACTION_MODEL.pine`

## Why V5
V5 removes bar-count bias by defining reaction windows in **hours** (converted to bars per timeframe):
- move window
- no-revisit window
- persistence window

Then it:
1) builds candidate anchors,
2) computes deterministic reaction score,
3) prunes anchors by score + retention,
4) clusters selected anchors into zones.

## Dot colors (DIAG)
- **Aqua**: selected anchor (kept after retention)
- **Purple**: failed candidate prefilter
- **Red**: failed move-away
- **Orange**: failed no-revisit
- **Yellow**: failed persistence
- **Fuchsia**: failed score gate
- **Gray**: failed side-aware gap gate

## Suggested first run (DIAG)
- Candidate mode: `local-extrema`
- Candidate len/range: `3 / 1.0 ATR`
- Move/NoRevisit/Persist hours: `96 / 96 / 72`
- Min anchor move ATR: `2.75`
- Min persistence bars: `5`
- Persist threshold ATR: `0.60`
- Use anchor score gate: ON
- Min anchor score: `6.0`
- Gap gate (hours): same `120`, opposite `24`
- Anchor retention percent: `25%`
- Max anchors kept: `180`
- Cluster tol/points/score: `1.8% / 4 / 7.0`

## Notes
- To compare windows fairly across timeframes, keep hour-based windows fixed.
- Tune noise mostly via: `Min anchor score` and `Anchor retention percent`.
- Keep `showFailedAnchors` OFF by default; turn ON only when diagnosing misses.
