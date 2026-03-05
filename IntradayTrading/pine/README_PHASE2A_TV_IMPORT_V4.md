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

If dots are hard to see:
- set `DIAG anchor dot size` to `large` or `huge`
- increase `Zone fill alpha` (more transparent zone fills)

Anchor dots are plotted at the **candle-end timestamp** (`time_close`) and at the anchor price extreme (high/low), so they sit on the reaction candle endpoint.

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
- Min bars between accepted anchors: `5`
- Show failed anchors: `OFF`

## Notes
- This version intentionally prioritizes deterministic anchor quality over broad point inclusiveness.
- Use failed-anchor dots + debug counters to decide whether to relax or tighten gates.
