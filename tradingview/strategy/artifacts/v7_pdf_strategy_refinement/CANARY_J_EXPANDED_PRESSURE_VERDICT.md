# Canary J Expanded Pressure Verdict

Date: 2026-06-15 ET / 2026-06-16 UTC

## Scope

Candidate:

`Unity UTM Strategy v7 QS3 PDF Filter Canary J`

This pass did not change Pine logic. It pressure-tested Canary J beyond the original ETH/SOL/DOGE/ZEC refinement basket.

Unity strategy anchors preserved:

- Reversal-zone entries only after liquidity sweep/reclaim.
- LTF structure/MSS confirmation.
- Oracle Strength as market sentiment/strength confirmation.
- 30m/1h-aligned execution and real invalidation stop floor from Canary E.
- No closed-source indicator rebuilds and no symbol-specific production ban.

## Harness Update

Updated:

`artifacts/v7_deep_backtest_date_window_proof/tv_deep_backtest_date_window_matrix.mjs`

Added a runtime `--symbols` override so pressure-test baskets can be run without mutating the baseline manifest symbol list.

Validation command shape:

```bash
node tradingview/strategy/artifacts/v7_deep_backtest_date_window_proof/tv_deep_backtest_date_window_matrix.mjs \
  --config tradingview/strategy/artifacts/v7_pdf_strategy_refinement/tv_pdf_strategy_refinement_runs.json \
  --run v7-qs3-pdf-filters-eth-install-canary \
  --symbols BINANCE:ADAUSDT.P,BINANCE:LINKUSDT.P,BINANCE:XRPUSDT.P
```

Parser added:

`artifacts/v7_pdf_strategy_refinement/analyze_canary_j_pressure_test.mjs`

Reason: TradingView again exported Excel workbooks with a `.csv` suffix. The parser reads workbook XML, pairs rows by `Trade number`, and parses encoded entry fields such as `C`, `S`, `SS`, `ATR`, and `RA`.

## Validation Runs

Prior four-symbol Canary J reference:

`artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T00-04-59-648Z-deep-date-window-matrix`

Admitted-control pressure batch:

`artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T01-49-46-255Z-deep-date-window-matrix`

Symbols:

- `BINANCE:ADAUSDT.P`
- `BINANCE:LINKUSDT.P`
- `BINANCE:XRPUSDT.P`

High-beta/reflexive pressure batch:

`artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T03-04-55-520Z-deep-date-window-matrix`

Symbols:

- `BINANCE:ARBUSDT.P`
- `BINANCE:PYTHUSDT.P`
- `BINANCE:SEIUSDT.P`

All runs passed the TradingView harness guards:

- Status: `ok`
- Layout: `Codex-Automation`
- Strategy title: `Unity UTM Strategy v7 QS3 PDF Filter Canary J`
- Sentinel: `CODEX_INSTALL_SENTINEL_QS3_PDF_CANARY_J`
- Mapped sources applied per symbol
- Strategy report date range selected as `Entire history`
- Visible date ranges start before `2024-01-01`
- Strategy exports completed

## Basket Comparison

| Basket | Symbols | Trades | Net USDT | PF | Win % |
| --- | --- | ---: | ---: | ---: | ---: |
| Original J | ETH, SOL, DOGE, ZEC | 82 | 1962.61 | 1.623 | 65.9 |
| Admitted controls | ADA, LINK, XRP | 43 | -614.94 | 0.725 | 39.5 |
| High-beta/reflexive | ARB, PYTH, SEI | 32 | 672.10 | 1.714 | 68.8 |
| Combined expanded read | all 9 symbols | 157 | 2019.77 | 1.319 | 59.2 |

## By Side

| Basket | Side | Trades | Net USDT | PF | Win % |
| --- | --- | ---: | ---: | ---: | ---: |
| Original J | Long | 66 | 1078.54 | 1.361 | 60.6 |
| Original J | Short | 16 | 884.07 | 6.413 | 87.5 |
| Admitted controls | Long | 32 | -824.21 | 0.570 | 31.3 |
| Admitted controls | Short | 11 | 209.27 | 1.655 | 63.6 |
| High-beta/reflexive | Long | 27 | 380.88 | 1.405 | 63.0 |
| High-beta/reflexive | Short | 5 | 291.22 | n/a | 100.0 |
| Combined | Long | 125 | 635.21 | 1.109 | 53.6 |
| Combined | Short | 32 | 1384.56 | 3.867 | 81.3 |

## By Symbol

| Symbol | Trades | Net USDT | PF | Win % | Read |
| --- | ---: | ---: | ---: | ---: | --- |
| ETH | 29 | 1348.21 | 2.576 | 75.9 | Strong original control |
| SOL | 20 | 142.84 | 1.149 | 55.0 | Marginal positive |
| DOGE | 15 | 345.03 | 1.636 | 66.7 | Improved versus E/G concern |
| ZEC | 18 | 126.53 | 1.160 | 61.1 | Marginal positive |
| ADA | 12 | 356.52 | 2.111 | 66.7 | Strong pressure pass |
| LINK | 16 | -744.05 | 0.269 | 18.8 | Clear fail |
| XRP | 15 | -227.41 | 0.747 | 40.0 | Fail |
| ARB | 12 | 466.09 | 2.466 | 75.0 | Strong pressure pass |
| PYTH | 9 | -171.38 | 0.583 | 44.4 | Fail |
| SEI | 11 | 377.39 | 2.778 | 81.8 | Strong pressure pass |

## Short C3 Read

| Basket | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| Original J short C3 | 12 | 689.15 | 12.768 | 91.7 |
| Admitted-control short C3 | 9 | 11.68 | 1.037 | 55.6 |
| High-beta/reflexive short C3 | 4 | 195.35 | n/a | 100.0 |
| Combined short C3 | 25 | 896.18 | 3.370 | 80.0 |

The original weak-short problem is no longer the primary defect. Canary J's short C3 rescue is not uniformly strong, but it remains positive across the expanded 9-symbol read.

The warning: the specific delayed-strength rescue threshold is still not proven. In the admitted-control batch, the `S3-6` delayed short C3 trades that passed `strengthSlope <= -0.70` were negative:

| Basket | Bucket | Trades | Net USDT | PF | Win % |
| --- | --- | ---: | ---: | ---: | ---: |
| Admitted controls | `S3-6 slope<=-0.70` | 3 | -106.85 | 0.312 | 33.3 |
| High-beta/reflexive | `S3-6 slope<=-0.70` | 2 | 98.57 | n/a | 100.0 |

That means the concept is still defensible, but the `-0.70` value should not be promoted as settled.

## Long-Side Defect

The pressure tests shifted the main defect from shorts to long admission:

- Admitted-control longs: 32 trades, `-824.21`, PF `0.570`.
- High-beta/reflexive longs: 27 trades, `+380.88`, PF `1.405`.
- Original J longs: 66 trades, `+1078.54`, PF `1.361`.

The tempting simple filter is long strength recency. In the admitted-control batch, delayed long strength was awful:

| Basket | Long `S7+` Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| Original J | 30 | 821.10 | 1.642 | 63.3 |
| Admitted controls | 16 | -1098.86 | 0.113 | 12.5 |
| High-beta/reflexive | 12 | 275.47 | 1.869 | 66.7 |
| Combined | 58 | -2.29 | 0.999 | 50.0 |

Do not implement a global `longStrengthAge <= 6` gate yet. It fixes LINK/XRP behavior but would remove a profitable part of the original J and high-beta baskets.

## Interpretation

Canary J is still the current best validated branch, but it is not a production candidate.

The broader read is mixed:

- Strong: ETH, ADA, ARB, SEI.
- Positive but marginal: SOL, DOGE, ZEC.
- Failed: LINK, XRP, PYTH.

This does not support another narrow short-side tune as the next edit. The short book is carrying the strategy in the expanded read. The open problem is whether long admission should be conditioned by symbol class or by a more general reaction-quality rule that does not destroy the profitable original/high-beta long buckets.

## Recommendation

Do not make a Pine logic change from this evidence alone.

Next validation should be a failure-control batch before editing:

- `BINANCE:SUIUSDT.P`
- `BINANCE:WIFUSDT.P`
- `BINANCE:ENAUSDT.P`
- optionally `BINANCE:OPUSDT.P` or `BINANCE:PENDLEUSDT.P`

Purpose:

1. Confirm whether the LINK/XRP/PYTH failure is a broader long-admission/symbol-class issue.
2. Check whether short C3 remains positive outside the favorable original/high-beta samples.
3. Only then test a narrow, Unity-themed rule such as a long reaction-quality gate, not a symbol ban.

Overfitting risk remains high. The expanded runs improved evidence quality, but they also show that simple global gates can look good in one basket and damage another.
