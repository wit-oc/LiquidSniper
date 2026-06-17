# Canary F Short Confluence Results

Date: 2026-06-15

## Candidate

`Unity UTM Strategy v7 QS3 PDF Filter Canary F`

Change tested:

- Preserve Canary E filters.
- Add a PDF-aligned short-side confluence gate:
  - `Require Strong Short Confluence = true`
  - `PDF Minimum Short Quality Score = 4`
- Practical effect: short entries now require `shortQualityScore >= 4`; long entries are unchanged.

Rationale: the Unity Trading Model emphasizes liquidity grabs, market structure shifts, delta strength, and time/volume confirmation. Canary E showed that weak short confluence was a major drag, especially SOL/DOGE shorts, so Canary F tests whether short reversals need fuller confirmation than long reversals.

## Validation Run

Automation report:

`artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-15T19-03-42-893Z-deep-date-window-matrix/pine-text-matrix-report.json`

Run proof:

- Status: `ok`
- Symbols: `BINANCE:ETHUSDT.P`, `BINANCE:SOLUSDT.P`, `BLOFIN:DOGEUSDT.P`, `BLOFIN:ZECUSDT.P`
- Layout: `Codex-Automation` on every item
- Strategy title: `Unity UTM Strategy v7 QS3 PDF Filter Canary F`
- Strategy report date range: `Entire history`
- Pine backtest window defaults: `2024-01-01` through `2026-12-31`
- Mapped sources applied per symbol:
  - `REQ AIO Internal Bullish MSS`
  - `REQ AIO Internal Bearish MSS`
  - `DIAG AIO Buy Trend Alert`
  - `DIAG AIO Sell Trend Alert`
  - `REQ Oracle Strength`
  - optional AIO BOS sources

Export directory:

`artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-15T19-03-42-893Z-deep-date-window-matrix`

## Basket Comparison

| Variant | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| Canary E | 142 | 1089.93 | 1.209 | 54.23 | 7.68 |
| Canary F | 70 | 1264.88 | 1.412 | 61.43 | 18.07 |
| Delta | -72 | +174.95 | +0.203 | +7.20 | +10.39 |

## Canary F By Symbol

| Symbol | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| ETH | 21 | 889.12 | 2.136 | 71.43 | 42.34 |
| SOL | 18 | 2.11 | 1.002 | 50.00 | 0.12 |
| DOGE | 14 | 295.16 | 1.546 | 64.29 | 21.08 |
| ZEC | 17 | 78.49 | 1.100 | 58.82 | 4.62 |

## Canary F By Side

| Side | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| Long | 66 | 1074.19 | 1.362 | 60.61 | 16.28 |
| Short | 4 | 190.69 | 2.820 | 75.00 | 47.67 |

## Confluence Result

Canary E short-side breakdown:

| Bucket | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| Short C3 | 72 | -187.12 | 0.912 | 47.22 |
| Short C4 | 4 | 194.23 | 2.879 | 75.00 |

Canary F short-side breakdown:

| Bucket | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| Short C4 | 4 | 190.69 | 2.820 | 75.00 |

Canary F successfully removes all C3 shorts. That improves the basket, but it also leaves only four short trades across the entire four-symbol set.

## Interpretation

Canary F is a valid improvement over Canary E on this validation basket, but it is not yet a final strategy recommendation. The improvement is real in the exported TradingView data, not just an offline slice, but it comes mostly from suppressing shorts rather than improving short selection.

The result supports this working theory:

- Canary E long logic is carrying most of the edge.
- Weak-confirmation shorts are the largest current drag.
- Short reversals likely need stronger confirmation than longs in this mapped-source version.

The main concern is strategic honesty: a reversal-zone strategy should not accidentally become mostly long-only unless the model explicitly accepts that asymmetry. Canary F should be kept as the new defensive benchmark, not promoted as final.

## Recommendation

Keep Canary F as the current best tested candidate and next pressure-test a narrower short-side rescue:

- Keep `shortQualityScore >= 4` as the default defensive gate.
- Add a controlled exception for C3 shorts only when an additional Unity-themed confirmation is present.
- The exception should be based on structure/regime confirmation, not symbol-specific suppression.

The next candidate should try to recover some profitable ETH/ZEC C3 short behavior without reopening the SOL/DOGE short bleed.
