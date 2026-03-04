# Phase2A S/R Watcher V2 (Reaction-Zone Qualified) — TradingView Import

## File
- `IntradayTrading/pine/PHASE2A_SR_WATCHER_V2_REACTION_ZONES.pine`

## Why V2
V2 refactors zone logic to better match Foxian constraints:
- reaction-first zone boundaries (wick/body touch envelope)
- qualification gate: minimum 3 reaction-confirmed touches
- candidate/qualified state split (zones are not immediately trusted)
- historical pool retention via weakest-drop (not strict FIFO)
- separate display cap for chart clarity

## Import
1. Open TradingView chart.
2. Open **Pine Editor**.
3. Paste contents of `PHASE2A_SR_WATCHER_V2_REACTION_ZONES.pine`.
4. Save and Add to chart.

## Recommended Daily defaults
- Pivot Left/Right: `8 / 8`
- Min pivot strength: `0.95`
- Min qualified touches: `3`
- Reaction move K: `0.25`
- Reaction window bars: `8`
- Merge overlap: `0.35`
- Min zone spacing: `1.25`
- Max zone height % of level: `0.08`
- Max zones internal: `140`
- Max displayed zones: `12`
- Show candidates: `false` (fallback-on when none qualified)
- Show reason labels: `false`
- Color by support/resistance side: `false` (side-neutral)
- Support solid / Resistance dashed: `false`

## Notes
- This remains watcher-only (no entries/triggers).
- EXPIRED remains out of default flow.
- Drawing now uses `xloc.bar_time` for long-history stability on lower timeframes.
- If chart gets busy, reduce `Max displayed zones` first (not internal pool).
- Use `Diagnostic target price` (e.g., `72000`) to inspect nearest computed zone in the debug table.
