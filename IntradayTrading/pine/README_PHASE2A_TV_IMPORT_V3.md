# Phase2A S/R Watcher V3 (Historical Builder) — TradingView Import

## File
- `IntradayTrading/pine/PHASE2A_SR_WATCHER_V3_HISTORICAL_BUILDER.pine`

## What is new in V3
V3 refactors zone discovery into a historical builder pipeline:
1. **Pass A (seed extraction):** scans old → new candles in lookback and creates/merges reaction seeds.
2. **Pass B (corroboration):** replays touches/reactions historically, updates boundaries, and qualifies zones.
3. **Pass C (display):** selects visible zones (CERT/DIAG mode aware).

This is closer to the mentorship intent of corroborating levels over full history rather than only forward-counting from creation time.

## Mode toggle
- `CERT`: strict/fidelity mode (diagnostic forcing disabled)
- `DIAG`: target/focus diagnostics enabled for troubleshooting missing levels

## Recommended starter settings (Daily/Weekly)
- Operating mode: `CERT`
- Historical build lookback bars: `1200`
- Pivot Left/Right: `8 / 8`
- Min pivot strength: `0.95`
- Seed boundary wick bias: `0.70`
- Reaction boundary wick bias: `0.75`
- Min qualified touches: `3`
- Require both edge types: `true`
- Reaction move K: `0.20`
- Reaction window bars: `12`
- Merge overlap: `0.35`
- Min zone spacing: `1.25`
- Max zone height %: `0.04`
- Max zone height in ATRs: `6.0`
- Max zones internal/displayed: `120 / 14`

## DIAG workflow (72k investigation)
- Switch mode to `DIAG`
- Set `Diagnostic target price` and optional `Display focus price` to `72000`
- Inspect debug rows:
  - Nearest to target
  - Target dist %
  - Nearest Q/U/L
  - Nearest H/moveReq

## Notes
- Watcher-only indicator (no entries/triggers/execution).
- HTF markers are visual hints only.
