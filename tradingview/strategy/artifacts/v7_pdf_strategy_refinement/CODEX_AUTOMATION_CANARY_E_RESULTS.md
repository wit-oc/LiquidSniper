# Codex-Automation Canary E Results

Date: 2026-06-15

## Scope

This run used only the `Codex-Automation` TradingView layout.

Strategy title:

`Unity UTM Strategy v7 QS3 PDF Filter Canary E`

Harness proof:

- Active layout matched `Codex-Automation` for every exported symbol.
- Pine source top/tail proof matched the Canary E strategy title and EOF sentinel.
- Pine save succeeded before add. ETH used the visible Pine save button; SOL/DOGE/ZEC used the keyboard save fallback.
- The newly added active Strategy Tester title matched Canary E before source mapping and export.
- Source mappings were applied per symbol from `Close` to the intended Oracle/Unity sources.
- Strategy Report date range was set to Entire history and verified before export.
- Exports used the active Strategy Report context-menu path.

## Export Artifacts

| Symbol | Run Directory | Visible Range |
|---|---|---|
| BINANCE:ETHUSDT.P | `artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-15T15-51-22-874Z-deep-date-window-matrix` | Nov 27, 2019 - Jun 15, 2026 |
| BINANCE:SOLUSDT.P | `artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-15T15-56-06-370Z-deep-date-window-matrix` | Sep 14, 2020 - Jun 15, 2026 |
| BLOFIN:DOGEUSDT.P | `artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-15T15-56-06-370Z-deep-date-window-matrix` | Jan 12, 2023 - Jun 15, 2026 |
| BLOFIN:ZECUSDT.P | `artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-15T15-56-06-370Z-deep-date-window-matrix` | Oct 18, 2023 - Jun 15, 2026 |

## Basket Comparison

Manual hydrated baseline from `artifacts/v7_artifacts/MANUAL_HYDRATED_EXPORT_REVIEW.md`:

| Version | Trades | Net PnL | Gross Profit | Gross Loss | PF | Win Rate |
|---|---:|---:|---:|---:|---:|---:|
| Baseline QS3 | 285 | -555.84 | 11832.60 | -12388.44 | 0.955 | 51.93% |
| Canary E | 142 | 1089.93 | 6293.88 | -5203.95 | 1.209 | 54.23% |

## Per-Symbol Metrics

| Symbol | Trades | Net PnL | PF | Win Rate | Avg Trade | Long Net / PF | Short Net / PF |
|---|---:|---:|---:|---:|---:|---:|---:|
| ETHUSDT.P | 42 | 1137.90 | 1.838 | 64.29% | 27.09 | 697.21 / 1.882 | 440.69 / 1.777 |
| SOLUSDT.P | 38 | -209.91 | 0.869 | 44.74% | -5.52 | 110.08 / 1.129 | -319.99 / 0.573 |
| DOGEUSDT.P | 32 | -48.00 | 0.959 | 46.88% | -1.50 | 197.80 / 1.366 | -245.80 / 0.615 |
| ZECUSDT.P | 30 | 209.94 | 1.197 | 60.00% | 7.00 | 77.73 / 1.097 | 132.21 / 1.500 |

## Read

Canary E is a valid improvement at the basket level, but it is not uniformly better.

The PDF-guided filters reduce trade count by roughly half and improve the group from unprofitable to positive. That supports the idea that the strategy should require cleaner reaction timing and truer invalidation geometry before treating a liquidity-zone reversal as tradable.

SOL is the main objection. Canary E removes enough SOL winners, or retains enough bad SOL shorts, that SOL moves from positive baseline to negative Canary E. DOGE remains below break-even, although the drawdown source appears narrower than before. ETH and ZEC respond well.

## Next Pressure Tests

1. Side/regime gating should be the next optimization axis.
2. Specifically test short-side suppression or stricter short-side sentiment confirmation on SOL and DOGE.
3. Keep the Canary E execution filters as the current reference branch, but do not promote it without a SOL/DOGE side filter study.
4. Prefer one-symbol TradingView automation units for reliability, then aggregate exported artifacts. The basket run now works, but split runs are easier to recover and audit.
