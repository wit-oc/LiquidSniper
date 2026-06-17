# Canary J Decisive Delayed Strength Results

Date: 2026-06-15 ET / 2026-06-16 UTC

## Candidate

`Unity UTM Strategy v7 QS3 PDF Filter Canary J`

Change tested:

- Preserve Canary H.
- Keep C4+ shorts fully allowed.
- Keep H's C3 short rescue ATR cap at `entryAtrBps <= 60`.
- Keep C3 short rescue available only for fresh MSS and controlled negative strength slope.
- Add a delayed-strength refinement for lower-confluence C3 shorts:
  - If `shortStrengthAge` is between `3` and `6`, require `strengthSlope <= -0.70`.

Rationale: Canary H fixed most weak C3 shorts but left DOGE C3 rescue negative. A blunt Canary I delayed-strength veto removed DOGE losers, but also removed profitable SOL C3 shorts. Canary J keeps the theme tighter: delayed C3 short confirmation can still pass, but only when the strength shift is decisive enough to support the reversal thesis.

## Implementation

Pine source:

`artifacts/v7_generalization_independent_variables/generated/v7-generalization-quality-score-3.pine`

Added PDF controls:

- `Require Decisive Delayed C3 Short Strength = true`
- `C3 Short Delayed Strength Min Age = 3`
- `C3 Short Delayed Strength Max Age = 6`
- `C3 Short Delayed Strength Max Slope = -0.70`

The C3 short rescue gate now requires delayed strength age to be either outside the 3-6 bar window or backed by `strengthSlope <= -0.70`.

## Validation Runs

DOGE-only small batch:

`artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-15T21-43-34-822Z-deep-date-window-matrix/pine-text-matrix-report.json`

Full basket:

`artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T00-04-59-648Z-deep-date-window-matrix/pine-text-matrix-report.json`

Proof summary:

- Status: `ok`
- Layout: `Codex-Automation`
- Strategy title: `Unity UTM Strategy v7 QS3 PDF Filter Canary J`
- Sentinel: `CODEX_INSTALL_SENTINEL_QS3_PDF_CANARY_J`
- Compile: `ok`
- Strategy report date range: `Entire history`
- Source mappings applied per symbol
- Strategy exports: `ok`

## Basket Comparison

| Variant | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| Canary E | 142 | 1089.93 | 1.209 | 54.23 | 7.68 |
| Canary F | 70 | 1264.88 | 1.412 | 61.43 | 18.07 |
| Canary G | 98 | 1552.15 | 1.411 | 60.20 | 15.84 |
| Canary H | 85 | 1732.19 | 1.514 | 63.53 | 20.38 |
| Canary I | 79 | 1768.33 | 1.562 | 64.56 | 22.38 |
| Canary J | 82 | 1962.61 | 1.623 | 65.85 | 23.93 |

Delta:

| Comparison | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| J - E | -60 | +872.68 | +0.414 | +11.62 | +16.25 |
| J - H | -3 | +230.42 | +0.110 | +2.32 | +3.56 |
| J - I | +3 | +194.28 | +0.061 | +1.30 | +1.55 |

## Canary J By Symbol

| Symbol | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| ETH | 29 | 1348.21 | 2.576 | 75.86 | 46.49 |
| SOL | 20 | 142.84 | 1.149 | 55.00 | 7.14 |
| DOGE | 15 | 345.03 | 1.636 | 66.67 | 23.00 |
| ZEC | 18 | 126.53 | 1.160 | 61.11 | 7.03 |

## Canary J By Side

| Side | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| Long | 66 | 1078.54 | 1.361 | 60.61 | 16.34 |
| Short | 16 | 884.07 | 6.413 | 87.50 | 55.25 |

## Canary J By Symbol And Side

| Symbol/Side | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| ETH long | 19 | 696.89 | 1.875 | 68.42 | 36.68 |
| ETH short | 10 | 651.32 | 12.122 | 90.00 | 65.13 |
| SOL long | 17 | 106.86 | 1.125 | 52.94 | 6.29 |
| SOL short | 3 | 35.98 | 1.343 | 66.67 | 11.99 |
| DOGE long | 13 | 197.07 | 1.363 | 61.54 | 15.16 |
| DOGE short | 2 | 147.96 | n/a | 100.00 | 73.98 |
| ZEC long | 17 | 77.72 | 1.098 | 58.82 | 4.57 |
| ZEC short | 1 | 48.81 | n/a | 100.00 | 48.81 |

## Short Confluence Breakdown

| Bucket | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| Short C3 | 12 | 689.15 | 12.768 | 91.67 | 57.43 |
| Short C4 | 4 | 194.92 | 2.861 | 75.00 | 48.73 |

C3 rescue by symbol:

| Symbol | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| ETH | 8 | 450.72 | 8.697 | 87.50 | 56.34 |
| SOL | 2 | 140.73 | n/a | 100.00 | 70.37 |
| DOGE | 1 | 48.89 | n/a | 100.00 | 48.89 |
| ZEC | 1 | 48.81 | n/a | 100.00 | 48.81 |

C3 rescue by strength age:

| Strength Age | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| S0-2 | 4 | 307.40 | n/a | 100.00 | 76.85 |
| S3-6 | 3 | 193.01 | n/a | 100.00 | 64.34 |
| S7+ | 5 | 188.74 | 4.223 | 80.00 | 37.75 |

## What Changed Versus H

Canary J removes three H C3 short rescue losers:

| Symbol | Side | Net USDT | C | S | Strength Slope | ATR bps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ETH | short | -119.35 | 3 | 3 | -0.5440 | 37.50 |
| DOGE | short | -54.91 | 3 | 4 | -0.2258 | 45.43 |
| DOGE | short | -53.84 | 3 | 3 | -0.6491 | 54.89 |

Unlike Canary I, Canary J keeps the delayed but decisive SOL C3 winners:

| Symbol | Side | Net USDT | C | S | Strength Slope | ATR bps |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| SOL | short | 92.56 | 3 | 5 | -0.7262 | 32.28 |
| SOL | short | 48.17 | 3 | 3 | -0.9252 | 50.29 |

## Interpretation

Canary J is the strongest validated candidate so far on the four-symbol basket.

The rule is more faithful than a symbol ban because it does not name DOGE or suppress all lower-confluence shorts. It asks a narrower Unity-themed question: if a C3 short's strength confirmation is delayed, is the later sentiment/strength shift decisive enough to support the reversal after the liquidity sweep?

The answer on this basket is yes. The filter removes three weak delayed C3 shorts while preserving the productive delayed C3 shorts in SOL and ETH.

## Remaining Defects

- SOL is still only modestly positive, and the SOL short sample is just three trades.
- ZEC short evidence is only one trade.
- The short book is now very strong, but small-sample PF can be misleading.
- Trade management still uses the existing TP1/stop style rather than a full Unity partial TP1/TP2/runner model.

## Overfitting Risk

High.

The concept is defensible, but the `-0.70` delayed-strength slope threshold was selected from this four-symbol refinement set. It must be pressure tested on a broader symbol-class basket before promotion.

## Recommendation

Use Canary J as the current best validated branch, not as final production logic.

Next pressure test:

1. Run Canary J across a broader high-beta and meme/perp basket.
2. Compare C3 rescue by strength age and strength slope before changing the threshold.
3. If the rule holds outside this four-symbol set, then evaluate whether trade management should be the next refinement axis.
