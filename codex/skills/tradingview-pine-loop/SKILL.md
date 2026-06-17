---
name: tradingview-pine-loop
description: Automate a data-first TradingView Pine Script development loop through a logged-in Chrome browser profile. Use when installing, compiling, backtesting, exporting, or validating Pine indicators or strategies in TradingView from Codex.
---

# TradingView Pine Loop

Use this skill when the user wants Codex to update Pine Script locally, install it into TradingView Web, collect TradingView compile/backtest/export artifacts, and iterate from structured results.

## Prerequisites

- TradingView Web is the target, not TradingView Desktop.
- `TV_CHROME_PROFILE_DIR` points to a dedicated Chrome profile directory.
- The user has logged into TradingView through `tv-login` using that profile.
- The project has a run manifest, usually `tradingview/config/tv_automation_runs.json`.
- Playwright is available to Node (`npm install playwright` in the repo or an equivalent local setup).
- Default browser channel is Playwright Chromium/Chrome-for-Testing (`TV_CHROME_CHANNEL=chromium`). Set `TV_CHROME_CHANNEL=chrome` only after login persistence is proven with local Google Chrome.
- External `input.source()` mappings are saved manually in a TradingView layout. Do not remap Unity/Oracle/vendor sources in v1 automation unless the user explicitly asks.

## Workflow

1. Inspect the manifest and Pine file.
2. Run `tv-login` once to create or refresh the durable TradingView login/layout state.
3. Run `tv-doctor` to confirm the cached session and UI surfaces.
4. Run `tv-install-pine` to paste/save/add the Pine script.
5. Run `tv-run-matrix` to load configured symbols/timeframes and export data.
6. Run `tv-validate` to evaluate exported CSVs and JSON reports.
7. Use failures to make the next Pine edit.

## Commands

From the repo root, use the installed skill path:

```bash
node ~/.codex/skills/tradingview-pine-loop/scripts/tv-doctor.mjs \
  --config tradingview/config/tv_automation_runs.json \
  --run liquidsniper-confluence-strategy-v1

node ~/.codex/skills/tradingview-pine-loop/scripts/tv-login.mjs \
  --config tradingview/config/tv_automation_runs.json \
  --run liquidsniper-confluence-strategy-v1

node ~/.codex/skills/tradingview-pine-loop/scripts/tv-install-pine.mjs \
  --config tradingview/config/tv_automation_runs.json \
  --run liquidsniper-confluence-strategy-v1

node ~/.codex/skills/tradingview-pine-loop/scripts/tv-run-matrix.mjs \
  --config tradingview/config/tv_automation_runs.json \
  --run liquidsniper-confluence-strategy-v1

node ~/.codex/skills/tradingview-pine-loop/scripts/tv-validate.mjs \
  --config tradingview/config/tv_automation_runs.json \
  --run liquidsniper-confluence-strategy-v1
```

## Manifest Contract

The skill is generic. Project-specific behavior belongs in the manifest:

- `scriptPath`: local `.pine` file to install.
- `kind`: `indicator` or `strategy`.
- `chartUrl`: saved TradingView chart/layout URL.
- `symbols`: TradingView symbols such as `BINANCE:BTCUSDT`.
- `timeframes`: objects with `label` and TradingView `interval` values.
- `validation`: required columns, minimum rows, non-constant diagnostics, and optional numeric checks.

Diagnostic plots are recommended but not hardcoded. A LiquidSniper script can export `LS_*` columns, while another project can use its own names.

## Reliability Rules

- Prefer structured CSV exports and JSON reports over screenshot interpretation.
- Keep screenshots for debugging only.
- Treat source mapping, settings dialogs, and export menus as brittle UI surfaces.
- If install/compile/export cannot pass at least 18/20 times on a stable saved layout, stop deepening the automation and report the reliability failure.

For selector assumptions and recovery steps, read `references/tradingview-ui.md` when debugging UI failures.
