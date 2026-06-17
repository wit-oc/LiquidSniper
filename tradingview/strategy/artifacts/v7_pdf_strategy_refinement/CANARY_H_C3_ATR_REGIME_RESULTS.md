# Canary H C3 ATR Regime Results

Date: 2026-06-15

## Candidate

`Unity UTM Strategy v7 QS3 PDF Filter Canary H`

Change tested:

- Preserve Canary G.
- Keep C4+ shorts fully allowed.
- Keep C3 short rescue allowed only when:
  - `shortQualityScore >= 3`
  - `shortChochAge <= 2`
  - `strengthSlope <= 0`
  - `strengthSlope >= -1.0`
  - `entryAtrBps <= 60`

Rationale: Canary G restored short participation but left DOGE C3 rescue shorts weak. The high-ATR C3 rescue bucket was broadly weak, while C3 rescue shorts with ATR at or below 60 bps were materially stronger. This is a general volatility/regime filter, not a DOGE-specific ban. It matches the Unity theme by requiring lower-confluence shorts to occur in controlled volatility rather than high-volatility chase conditions.

## Implementation

Pine source:

`artifacts/v7_generalization_independent_variables/generated/v7-generalization-quality-score-3.pine`

Added PDF input:

- `C3 Short Rescue Max ATR bps = 60.0`

The C3 rescue gate now also requires:

`not na(entryAtrBps) and entryAtrBps <= pdf_c3_short_rescue_max_atr_bps`

## Validation Runs

DOGE-only small batch:

`artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-15T19-59-16-610Z-deep-date-window-matrix/pine-text-matrix-report.json`

Full basket:

`artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-15T20-10-35-330Z-deep-date-window-matrix/pine-text-matrix-report.json`

Proof summary:

- Status: `ok`
- Layout: `Codex-Automation`
- Strategy title: `Unity UTM Strategy v7 QS3 PDF Filter Canary H`
- Sentinel: `CODEX_INSTALL_SENTINEL_QS3_PDF_CANARY_H`
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

Delta:

| Comparison | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| H - E | -57 | +642.26 | +0.305 | +9.30 | +12.70 |
| H - F | +15 | +467.31 | +0.102 | +2.10 | +2.31 |
| H - G | -13 | +180.04 | +0.103 | +3.33 | +4.54 |

## Canary H By Symbol

| Symbol | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| ETH | 30 | 1226.45 | 2.262 | 73.33 | 40.88 |
| SOL | 20 | 142.84 | 1.149 | 55.00 | 7.14 |
| DOGE | 17 | 236.37 | 1.363 | 58.82 | 13.90 |
| ZEC | 18 | 126.53 | 1.160 | 61.11 | 7.03 |

## Canary H By Side

| Side | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| Long | 66 | 1079.04 | 1.362 | 60.61 | 16.35 |
| Short | 19 | 653.15 | 2.669 | 73.68 | 34.38 |

## Canary H By Symbol And Side

| Symbol/Side | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| ETH long | 19 | 697.30 | 1.878 | 68.42 | 36.70 |
| ETH short | 11 | 529.15 | 3.974 | 81.82 | 48.10 |
| SOL long | 17 | 106.86 | 1.125 | 52.94 | 6.29 |
| SOL short | 3 | 35.98 | 1.343 | 66.67 | 11.99 |
| DOGE long | 13 | 197.16 | 1.364 | 61.54 | 15.17 |
| DOGE short | 4 | 39.21 | 1.361 | 50.00 | 9.80 |
| ZEC long | 17 | 77.72 | 1.098 | 58.82 | 4.57 |
| ZEC short | 1 | 48.81 | n/a | 100.00 | 48.81 |

## Short Confluence Breakdown

| Bucket | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| Short C3 | 15 | 459.36 | 2.602 | 73.33 | 30.62 |
| Short C4 | 4 | 193.79 | 2.850 | 75.00 | 48.45 |

C3 rescue by symbol:

| Symbol | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| ETH | 9 | 329.68 | 2.853 | 77.78 | 36.63 |
| SOL | 2 | 140.73 | n/a | 100.00 | 70.37 |
| DOGE | 3 | -59.86 | 0.450 | 33.33 | -19.95 |
| ZEC | 1 | 48.81 | n/a | 100.00 | 48.81 |

## DOGE Small-Batch Check

DOGE-only Canary H:

| Variant | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| Canary G DOGE | 19 | 131.02 | 1.174 | 52.63 | 6.90 |
| Canary H DOGE | 17 | 236.37 | 1.363 | 58.82 | 13.90 |

DOGE short specifically improved from `-66.05` USDT in Canary G to `+39.21` USDT in Canary H.

## Interpretation

Canary H is the strongest validated candidate so far on this four-symbol basket. It improves over Canary G without reverting to the near long-only profile of Canary F.

The main improvement is cleaner C3 short rescue selection:

- Canary G C3 rescue: 28 trades, +286.92 USDT, PF 1.408
- Canary H C3 rescue: 15 trades, +459.36 USDT, PF 2.602

The ATR cap removes the higher-volatility C3 short rescue conditions that were causing much of the weak DOGE behavior and several other poor lower-confluence shorts.

## Remaining Defect

DOGE C3 rescue shorts remain negative even after the ATR cap:

- 3 trades
- -59.86 USDT
- PF 0.450

The overall DOGE short book is now positive only because the retained C4 short offsets the remaining C3 weakness. That means the ATR cap helps, but does not fully explain the DOGE-specific C3 failure mode.

## Overfitting Risk

Medium to high.

The filter is thematically defensible as a volatility/regime gate for lower-confluence shorts, but the 60 bps threshold was selected from this four-symbol basket. It should not be promoted as final until it is tested across a broader high-beta/meme/perp set.

## Recommendation

Use Canary H as the current best validated candidate branch.

Next pressure test:

1. Run Canary H across a broader symbol-class basket that includes more high-beta and meme/perp names.
2. Compare C3 rescue behavior by ATR bucket across that expanded set.
3. Only consider symbol-class short suppression if DOGE-like C3 failures repeat outside DOGE.
