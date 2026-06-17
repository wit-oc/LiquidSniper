# Canary G C3 Short Rescue Results

Date: 2026-06-15

## Candidate

`Unity UTM Strategy v7 QS3 PDF Filter Canary G`

Change tested:

- Preserve Canary F's defensive short-side confluence gate.
- Keep C4+ shorts fully allowed.
- Allow a C3 short only when:
  - `shortQualityScore >= 3`
  - `shortChochAge <= 2`
  - `strengthSlope <= 0`
  - `strengthSlope >= -1.0`

Rationale: Canary F improved the basket by removing all C3 shorts, but it almost turned the strategy long-only. Canary G tests a narrower Unity-themed exception: C3 shorts are only allowed when the MSS is fresh and the negative strength shift is controlled rather than overextended. This keeps the focus on liquidity reversal evidence, market structure shift, and not chasing exhausted downside momentum.

## Implementation

Pine source:

`artifacts/v7_generalization_independent_variables/generated/v7-generalization-quality-score-3.pine`

Added PDF inputs:

- `Allow Fresh C3 Short Rescue = true`
- `C3 Short Rescue Minimum Quality = 3`
- `C3 Short Rescue Max MSS Age = 2`
- `C3 Short Rescue Min Strength Slope = -1.0`

The confluence gate now passes shorts when either:

- `shortQualityScore >= 4`, or
- the C3 rescue exception is true.

## Validation Run

Automation report:

`artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-15T19-31-39-829Z-deep-date-window-matrix/pine-text-matrix-report.json`

Run proof:

- Status: `ok`
- Symbols: `BINANCE:ETHUSDT.P`, `BINANCE:SOLUSDT.P`, `BLOFIN:DOGEUSDT.P`, `BLOFIN:ZECUSDT.P`
- Layout: `Codex-Automation` on every item
- Strategy title: `Unity UTM Strategy v7 QS3 PDF Filter Canary G`
- Sentinel: `CODEX_INSTALL_SENTINEL_QS3_PDF_CANARY_G`
- Compile: `ok`
- Strategy report date range: `Entire history`
- Pine backtest window defaults: `2024-01-01` through `2026-12-31`
- Source mappings applied per symbol, including:
  - AIO MSS
  - AIO trend alerts
  - Oracle Strength
  - AIO BOS
  - Phase1 Bus Regime Direction
  - Phase1 Bus CHoCH Direction
  - Phase1 Bus BoS Direction

Export directory:

`artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-15T19-31-39-829Z-deep-date-window-matrix`

## Basket Comparison

| Variant | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| Canary E | 142 | 1089.93 | 1.209 | 54.23 | 7.68 |
| Canary F | 70 | 1264.88 | 1.412 | 61.43 | 18.07 |
| Canary G | 98 | 1552.15 | 1.411 | 60.20 | 15.84 |

Delta:

| Comparison | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| G - E | -44 | +462.22 | +0.202 | +5.97 | +8.16 |
| G - F | +28 | +287.27 | -0.001 | -1.23 | -2.23 |

## Canary G By Symbol

| Symbol | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| ETH | 33 | 1163.76 | 2.089 | 69.70 | 35.27 |
| SOL | 22 | 139.57 | 1.138 | 54.55 | 6.34 |
| DOGE | 19 | 131.02 | 1.174 | 52.63 | 6.90 |
| ZEC | 24 | 117.80 | 1.124 | 58.33 | 4.91 |

## Canary G By Side

| Side | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| Long | 66 | 1073.48 | 1.361 | 60.61 | 16.26 |
| Short | 32 | 478.67 | 1.592 | 59.38 | 14.96 |

## Canary G By Symbol And Side

| Symbol/Side | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| ETH long | 19 | 690.88 | 1.877 | 68.42 | 36.36 |
| ETH short | 14 | 472.88 | 2.680 | 71.43 | 33.78 |
| SOL long | 17 | 106.89 | 1.125 | 52.94 | 6.29 |
| SOL short | 5 | 32.68 | 1.208 | 60.00 | 6.54 |
| DOGE long | 13 | 197.07 | 1.365 | 61.54 | 15.16 |
| DOGE short | 6 | -66.05 | 0.691 | 33.33 | -11.01 |
| ZEC long | 17 | 78.64 | 1.099 | 58.82 | 4.63 |
| ZEC short | 7 | 39.16 | 1.251 | 57.14 | 5.59 |

## Short Confluence Breakdown

| Bucket | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| Short C3 | 28 | 286.92 | 1.408 | 57.14 | 10.25 |
| Short C4 | 4 | 191.75 | 2.831 | 75.00 | 47.94 |

C3 rescue by symbol:

| Symbol | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| ETH | 12 | 274.97 | 1.977 | 66.67 | 22.91 |
| SOL | 4 | 137.40 | 3.605 | 75.00 | 34.35 |
| DOGE | 5 | -164.61 | 0.229 | 20.00 | -32.92 |
| ZEC | 7 | 39.16 | 1.251 | 57.14 | 5.59 |

## Interpretation

Canary G is the strongest validated candidate so far on this four-symbol basket. It beats Canary E materially and beats Canary F on net profit while restoring meaningful short participation.

The key improvement is that the C3 rescue rule recovered profitable ETH, SOL, and ZEC shorts without reopening the broad C3 short bleed seen in Canary E.

The remaining defect is concentrated:

- DOGE short remains negative.
- DOGE C3 rescue shorts are particularly poor: 5 trades, -164.61 USDT, PF 0.229.

That makes Canary G better than F as a strategy candidate, but not final. The next refinement should target whether the DOGE failure is a symbol-class/meme-perp behavior problem or whether a more general condition can identify those failed C3 shorts without naming DOGE.

## Overfitting Risk

Medium.

The rule is defensible because it maps to fresh structure shift and avoiding overextended strength, but the exact `2 bars` and `-1.0 slope` thresholds come from this basket. It needs pressure testing on more symbols before promotion.

Avoid the tempting next step of simply disabling DOGE shorts unless broader meme/perp behavior or an independent symbol-class test supports it.

## Recommendation

Use Canary G as the current best validated candidate branch.

Next candidate should keep Canary G intact and test one of these, in order:

1. A general C3 rescue exclusion for weak short structures that resemble the DOGE failures.
2. A symbol-class side filter only if a broader meme/high-beta basket confirms DOGE-like short behavior.
3. A management/risk adjustment for C3 rescue shorts rather than a new entry filter, if the failed DOGE shorts show acceptable MFE but poor hold/exit behavior.
