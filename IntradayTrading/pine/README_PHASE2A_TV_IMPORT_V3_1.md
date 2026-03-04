# Phase2A S/R Watcher V3.1 (Reaction Cloud) — TradingView Import

## File
- `IntradayTrading/pine/PHASE2A_SR_WATCHER_V3_1_REACTION_CLOUD.pine`

## What this deliverable is
V3.1 is an all-in on **reaction-cloud** builder:
- historical pass (old → new)
- reaction corroboration
- clustered zone selection
- CERT/DIAG mode split

No entry/trigger logic. Watcher-only.

## Recommended first test
- Mode: `DIAG`
- Lookback: `1200`
- Pivot L/R: `8/8`
- Min pivot strength: `0.95`
- Seed wick bias: `0.70`
- Reaction wick bias: `0.75`
- Min qualified touches: `3`
- Require dual edge: `true`
- Merge overlap / spacing: `0.35 / 1.25`
- Max zones internal/displayed: `120 / 14`

If debugging a specific level (e.g., 72k):
- `Diagnostic target price = 72000`
- `Display focus price = 72000`
- Inspect `Nearest to target`, `Target dist %`, `Nearest Q/U/L`, `Nearest H/moveReq`

## Notes
- Uses `xloc.bar_time` drawing for deep-history stability.
- CERT mode disables diagnostic forcing behavior.
