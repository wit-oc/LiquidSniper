# Canary J OP/PENDLE Generalization Verdict

Date: 2026-06-15 ET / 2026-06-16 UTC

## Scope

Candidate:

`Unity UTM Strategy v7 QS3 PDF Filter Canary J`

This pass tested the follow-up diagnostic symbols recommended after the failure-control batch:

- `BINANCE:OPUSDT.P`
- `BINANCE:PENDLEUSDT.P`

No Pine strategy logic was changed.

## Harness Proof

Run directory:

`artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T03-50-01-446Z-deep-date-window-matrix`

Parsed metrics:

- `artifacts/v7_pdf_strategy_refinement/canary_j_op_pendle_diagnostic_metrics.json`
- `artifacts/v7_pdf_strategy_refinement/CANARY_J_OP_PENDLE_DIAGNOSTIC_RESULTS.md`

The TradingView harness returned `status: ok`.

Guards passed for both symbols:

- Layout: `Codex-Automation`
- Strategy title: `Unity UTM Strategy v7 QS3 PDF Filter Canary J`
- Sentinel: `CODEX_INSTALL_SENTINEL_QS3_PDF_CANARY_J`
- Mapped Unity/Oracle sources applied per symbol
- Strategy Report date range set to `Entire history`
- OP visible range: `Jun 1, 2022 - Jun 15, 2026`
- PENDLE visible range: `Jul 27, 2023 - Jun 15, 2026`
- Strategy exports completed from the active Strategy Report context menu

## OP/PENDLE Metrics

Combined:

| Trades | Net USDT | PF | Win % |
| ---: | ---: | ---: | ---: |
| 32 | -605.37 | 0.671 | 40.6 |

By symbol:

| Symbol | Trades | Net USDT | PF | Win % | Read |
| --- | ---: | ---: | ---: | ---: | --- |
| OP | 14 | -147.10 | 0.794 | 42.9 | Fail |
| PENDLE | 18 | -458.27 | 0.592 | 38.9 | Fail |

By side:

| Side | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| Long | 26 | -441.14 | 0.703 | 42.3 |
| Short | 6 | -164.23 | 0.537 | 33.3 |

By confluence:

| Bucket | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| Long C3 | 3 | -153.66 | 0.000 | 0.0 |
| Long C4 | 21 | 16.92 | 1.016 | 52.4 |
| Long C5 | 2 | -304.40 | 0.000 | 0.0 |
| Short C3 | 2 | -5.22 | 0.899 | 50.0 |
| Short C4 | 3 | -303.13 | 0.000 | 0.0 |
| Short C5 | 1 | 144.12 | n/a | 100.0 |

## Current Canary J Aggregate

Current TradingView-validated Canary J symbols:

- Original refinement basket: ETH, SOL, DOGE, ZEC
- Admitted-control pressure batch: ADA, LINK, XRP
- High-beta/reflexive pressure batch: ARB, PYTH, SEI
- Failure-control batch: SUI, WIF, ENA
- OP/PENDLE diagnostic batch: OP, PENDLE

| Scope | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| Original J only | 82 | 1962.61 | 1.623 | 65.9 |
| 9-symbol expanded read | 157 | 2019.77 | 1.319 | 59.2 |
| 12-symbol read after failure controls | 191 | 1552.33 | 1.198 | 56.5 |
| 14-symbol read after OP/PENDLE | 223 | 946.96 | 1.098 | 54.3 |

By side across all 14 symbols:

| Side | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| Long | 178 | 42.20 | 1.005 | 51.1 |
| Short | 45 | 904.76 | 1.726 | 66.7 |
| Short C3 | 32 | 827.33 | 2.410 | 71.9 |

## Interpretation

The OP/PENDLE diagnostic strengthens the admission/generalization diagnosis.

The original Canary E defect was weak SOL/DOGE shorts. Canary J addressed that on the original four-symbol basket, and short C3 remains positive across the broader 14-symbol read. The larger problem is now different: Canary J does not generalize across arbitrary symbols, and the long book is near flat after adding failure controls and OP/PENDLE.

The tempting global filters are not clean enough to promote:

- Removing long `S7+` improves the 14-symbol aggregate, but it damages the original and high-beta baskets where long `S7+` was profitable.
- Removing long `C5+` improves the aggregate, but it only removes six trades. That is too small and too likely to be sample-specific.
- Tightening shorts again is not supported because shorts remain the stronger side of the current candidate.

This means the next implementation should not be another hidden global entry threshold. The more defensible path is an explicit admission/routing layer: decide which symbols or symbol classes are eligible for this 15m hydrated-source strategy, then keep entry logic stable while validating that admitted set.

## Current Working Classification

This classification is diagnostic, not production approval.

| Class | Symbols | Read |
| --- | --- | --- |
| Strong pass | ETH, ADA, ARB, SEI | Strong positive PF and net in current Canary J exports |
| Positive but monitor | SOL, DOGE, ZEC, WIF, ENA | Positive, but some are marginal or small sample |
| Fail | LINK, XRP, PYTH, SUI, OP, PENDLE | Negative current Canary J behavior |

This differs from older V7 admission artifacts because those artifacts used different candidate logic, different timeframe coverage, or earlier strategy branches. For this goal, the current Canary J hydrated 15m exports are the relevant evidence.

## Strong-Admitted Set Validation

After the OP/PENDLE verdict, the strongest four-symbol admission candidate was run as a fresh TradingView batch with no Pine logic changes:

- `BINANCE:ETHUSDT.P`
- `BINANCE:ADAUSDT.P`
- `BINANCE:ARBUSDT.P`
- `BINANCE:SEIUSDT.P`

Run directory:

`artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T04-01-32-075Z-deep-date-window-matrix`

Parsed metrics:

- `artifacts/v7_pdf_strategy_refinement/canary_j_strong_admitted_set_metrics.json`
- `artifacts/v7_pdf_strategy_refinement/CANARY_J_STRONG_ADMITTED_SET_RESULTS.md`

The TradingView harness returned `status: ok`.

Guards passed:

- Layout: `Codex-Automation`
- Strategy title: `Unity UTM Strategy v7 QS3 PDF Filter Canary J`
- Sentinel: `CODEX_INSTALL_SENTINEL_QS3_PDF_CANARY_J`
- Mapped Unity/Oracle sources applied per symbol
- Strategy Report date range set to `Entire history`
- ETH visible range: `Nov 27, 2019 - Jun 16, 2026`
- ADA visible range: `Jan 31, 2020 - Jun 16, 2026`
- ARB visible range: `Mar 23, 2023 - Jun 16, 2026`
- SEI visible range: `Aug 16, 2023 - Jun 16, 2026`

Strong-admitted metrics:

| Scope | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| ETH + ADA + ARB + SEI | 64 | 2548.21 | 2.494 | 75.0 |

By side:

| Side | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| Long | 42 | 1234.29 | 1.804 | 66.7 |
| Short | 22 | 1313.92 | 8.712 | 90.9 |

By symbol:

| Symbol | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| ETH | 29 | 1348.21 | 2.576 | 75.9 |
| ADA | 12 | 356.52 | 2.111 | 66.7 |
| ARB | 12 | 466.09 | 2.466 | 75.0 |
| SEI | 11 | 377.39 | 2.778 | 81.8 |

This is the strongest current evidence that Canary J should be handled as an admitted-symbol strategy rather than a universal all-coin strategy. The signal remains faithful to the Unity theme because the entry logic is unchanged: liquidity sweep/reclaim, mapped LTF MSS, Oracle Strength, 30m/1h timing, and real invalidation remain intact. The improvement comes from refusing to deploy the same 15m reaction model on symbols where current evidence says it does not behave.

## Monitored-Positive Validation

The monitored-positive bucket was then split by reliability:

- SOL, DOGE, and ZEC were rerun as a monitored legacy batch.
- ZEC failed inside the three-symbol batch because TradingView returned a long-processing warning and no trade data.
- ZEC passed when retried as a single-symbol run, so the failure is treated as a TradingView processing timeout, not a strategy rejection.
- WIF and ENA use the already-successful newer-listing rerun from the failure-control pass because that batch passed the same Canary J source, layout, mapping, and date-range guards.

Artifacts:

- `artifacts/v7_pdf_strategy_refinement/CANARY_J_MONITORED_SOL_DOGE_PARTIAL_RESULTS.md`
- `artifacts/v7_pdf_strategy_refinement/canary_j_monitored_sol_doge_partial_metrics.json`
- `artifacts/v7_pdf_strategy_refinement/CANARY_J_MONITORED_ZEC_RETRY_RESULTS.md`
- `artifacts/v7_pdf_strategy_refinement/canary_j_monitored_zec_retry_metrics.json`
- `artifacts/v7_pdf_strategy_refinement/CANARY_J_FAILURE_CONTROL_WIF_ENA_RESULTS.md`
- `artifacts/v7_pdf_strategy_refinement/canary_j_failure_control_wif_ena_metrics.json`

Monitored-positive combined metrics:

| Scope | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| SOL + DOGE + ZEC + WIF + ENA | 73 | 855.03 | 1.302 | 58.9 |

By symbol:

| Symbol | Trades | Net USDT | PF | Win % | Read |
| --- | ---: | ---: | ---: | ---: | --- |
| DOGE | 15 | 345.03 | 1.636 | 66.7 | Candidate add |
| ENA | 7 | 185.78 | 2.187 | 71.4 | Candidate add, small sample |
| SOL | 20 | 142.84 | 1.149 | 55.0 | Monitor |
| WIF | 12 | 72.61 | 1.198 | 50.0 | Monitor |
| ZEC | 19 | 108.77 | 1.134 | 57.9 | Monitor |

By side:

| Side | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| Long | 64 | 733.92 | 1.286 | 57.8 |
| Short | 9 | 121.11 | 1.457 | 66.7 |

This keeps SOL/DOGE/ZEC/WIF/ENA out of the same confidence tier as ETH/ADA/ARB/SEI. They are not failures, but the edge is thinner, more symbol-specific, and more exposed to sample risk.

## Recommendation

Do not make a Pine logic edit yet.

Current admission stance:

1. Core admitted candidate: ETH, ADA, ARB, SEI.
2. Candidate add: DOGE and ENA, with ENA marked small-sample.
3. Monitor only: SOL, ZEC, WIF.
4. Exclude for current Canary J: LINK, XRP, PYTH, SUI, OP, PENDLE.
5. Only after admission is stable should we test a narrow Unity-themed reaction-quality gate, such as a fresh long strength requirement or late-long suppression.

Overfit risk is high for any immediate Pine change. The current evidence says the strategy has pockets of real edge, but the edge is not universal across coins.
