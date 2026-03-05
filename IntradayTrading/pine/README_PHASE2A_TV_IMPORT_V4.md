# Phase2A S/R Watcher V4 (Reaction Anchor Audit) — TradingView Import

## File
- `IntradayTrading/pine/PHASE2A_SR_WATCHER_V4_REACTION_ANCHOR_AUDIT.pine`

## Model shift
V4 is anchor-first:
1. Detect raw reaction anchors (high/low candidates)
2. Deterministically filter anchors by:
   - move-away magnitude
   - no-revisit behavior
   - persistence
3. Cluster passed anchors into zones
4. Render zones + optional diagnostic anchor dots

## Dot colors (DIAG)
- **Aqua**: passed anchor
- **Purple**: failed candidate prefilter (not local-extrema and/or low-range bar)
- **Red**: failed move-away gate
- **Orange**: failed no-revisit gate
- **Yellow**: failed persistence gate
- **Fuchsia**: failed score gate (`Min anchor score`)

If dots are hard to see:
- set `DIAG anchor dot size` to `large` or `huge`
- increase `Zone fill alpha` (more transparent zone fills)

Anchor dots are plotted at anchor price extreme (high/low). You can choose x-position via `DIAG anchor x-position`:
- `wick-center` (recommended for visual wick alignment)
- `candle-end` (right edge of bar)

To avoid hitting dot cap too early:
- enable `DIAG: limit dots to date window`
- set `DIAG start time` / `DIAG end time` to the period you are investigating
- keep `DIAG: show failed anchors` OFF unless actively diagnosing gate misses

## Suggested first DIAG run
- Mode: `DIAG`
- Lookback: `3500`
- Anchor candidate mode: `local-extrema`
- Candidate local-extrema len: `2`
- Min candidate bar range (ATR): `0.80`
- Min anchor move (ATR): `1.75`
- Move window bars: `36`
- No-revisit bars: `10`
- Min persistence bars: `3`
- Use anchor score gate: `ON`
- Min anchor score: `3.60`
- Min bars between same-side anchors: `3`
- Min bars between opposite-side anchors: `1`
- Cluster tolerance %: `1.5`
- Min cluster points: `3`
- Min cluster score: `5.0`
- Zone width multiplier: `1.2`

## Strict noise-drop profile (if too many dots)
- Min candidate bar range (ATR): `1.20`
- Min anchor move (ATR): `2.50`
- Move window bars: `20`
- No-revisit bars: `20`
- Min persistence bars: `8`
- Persistence threshold (ATR): `0.70`
- Min bars between same-side anchors: `5`
- Min bars between opposite-side anchors: `1`
- Min anchor score: `4.50`
- Show failed anchors: `OFF`

## Notes
- This version intentionally prioritizes deterministic anchor quality over broad point inclusiveness.
- Use failed-anchor dots + debug counters to decide whether to relax or tighten gates.
