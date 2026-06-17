# Canary J Failure-Control Verdict

Date: 2026-06-15 ET / 2026-06-16 UTC

## Scope

Candidate:

`Unity UTM Strategy v7 QS3 PDF Filter Canary J`

This pass tested the failure-control basket recommended after the expanded pressure run. No Pine strategy logic was changed.

Failure-control symbols:

- `BINANCE:SUIUSDT.P`
- `BINANCE:WIFUSDT.P`
- `BINANCE:ENAUSDT.P`

## Harness Notes

Primary run:

`artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T03-20-28-923Z-deep-date-window-matrix`

Result:

- SUI exported successfully.
- WIF and ENA were valid TradingView reports, but the harness rejected them because their full visible histories started after the generic `2024-01-01` guard.
- WIF visible range: `Jan 18, 2024 — Jun 15, 2026`.
- ENA visible range: `Apr 2, 2024 — Jun 15, 2026`.

Harness update:

`artifacts/v7_deep_backtest_date_window_proof/tv_deep_backtest_date_window_matrix.mjs`

Added CLI-only `--minimum-start` override for newer listed symbols. This does not alter the manifest default. It only lets a validation batch prove full visible history when the instrument did not trade back to `2024-01-01`.

Rerun:

`artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T03-32-06-743Z-deep-date-window-matrix`

Command shape:

```bash
node tradingview/strategy/artifacts/v7_deep_backtest_date_window_proof/tv_deep_backtest_date_window_matrix.mjs \
  --config tradingview/strategy/artifacts/v7_pdf_strategy_refinement/tv_pdf_strategy_refinement_runs.json \
  --run v7-qs3-pdf-filters-eth-install-canary \
  --symbols BINANCE:WIFUSDT.P,BINANCE:ENAUSDT.P \
  --minimum-start 2024-04-02
```

Rerun result:

- Status: `ok`
- Layout: `Codex-Automation`
- Strategy title: `Unity UTM Strategy v7 QS3 PDF Filter Canary J`
- Sentinel: `CODEX_INSTALL_SENTINEL_QS3_PDF_CANARY_J`
- Mapped sources applied per symbol
- Entire history selected
- WIF visible range still proved stricter coverage than the override: `Jan 18, 2024 — Jun 15, 2026`
- ENA visible range matched the newer-listing guard: `Apr 2, 2024 — Jun 15, 2026`

## Failure-Control Metrics

Combined SUI + WIF + ENA:

| Trades | Net USDT | PF | Win % |
| ---: | ---: | ---: | ---: |
| 34 | -467.44 | 0.695 | 44.1 |

By symbol:

| Symbol | Trades | Net USDT | PF | Win % | Read |
| --- | ---: | ---: | ---: | ---: | --- |
| SUI | 15 | -725.83 | 0.281 | 26.7 | Hard fail |
| WIF | 12 | 72.61 | 1.198 | 50.0 | Marginal positive |
| ENA | 7 | 185.78 | 2.187 | 71.4 | Strong positive, small sample |

By side:

| Side | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| Long | 27 | -151.87 | 0.865 | 48.1 |
| Short | 7 | -315.57 | 0.228 | 28.6 |

By confluence:

| Bucket | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| Long C3 | 12 | -15.97 | 0.948 | 50.0 |
| Long C4 | 15 | -135.90 | 0.833 | 46.7 |
| Short C3 | 5 | -63.63 | 0.595 | 40.0 |
| Short C4 | 1 | -105.69 | 0.000 | 0.0 |
| Short C5 | 1 | -146.25 | 0.000 | 0.0 |

## Expanded Read After Failure Controls

All current Canary J TradingView validation baskets combined:

- Original J: ETH, SOL, DOGE, ZEC.
- Admitted controls: ADA, LINK, XRP.
- High-beta/reflexive: ARB, PYTH, SEI.
- Failure controls: SUI, WIF, ENA.

| Scope | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| Original J only | 82 | 1962.61 | 1.623 | 65.9 |
| 9-symbol expanded read before failure controls | 157 | 2019.77 | 1.319 | 59.2 |
| 12-symbol read after failure controls | 191 | 1552.33 | 1.198 | 56.5 |

By side across all 12 symbols:

| Side | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| Long | 152 | 483.34 | 1.069 | 52.6 |
| Short | 39 | 1068.99 | 2.199 | 71.8 |
| Short C3 | 30 | 832.55 | 2.556 | 73.3 |

## Interpretation

The failure-control batch does not support a simple conclusion like "all high-beta/failure names should be banned."

It does support these narrower conclusions:

- SUI is a clear non-fit in this implementation: long and short are both poor.
- WIF is marginal but not a hard fail in Canary J.
- ENA is positive, but the sample is only seven trades.
- The broader short C3 rescue is still positive after adding failure controls, but it is no longer clean in every sub-basket.
- The main cross-symbol problem remains admission/generalization, not the original SOL/DOGE-only short defect.

This weakens the case for another short-side threshold tune. It also weakens the case for a global long-strength recency gate, because long `S7+` is nearly flat across all symbols and is positive in the original/high-beta baskets.

## Canary E Comparison

On the original four-symbol validation basket, Canary J remains materially better than Canary E:

| Variant | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| Canary E | 142 | 1089.93 | 1.209 | 54.23 |
| Canary J | 82 | 1962.61 | 1.623 | 65.85 |

The expanded 12-symbol read is not an apples-to-apples Canary E comparison because Canary E was not rerun on the new symbols. It is a generalization pressure test for whether Canary J should be treated as production logic. On that broader read, the PF compresses to `1.198`, which is essentially back near Canary E's original PF while using a different symbol set. That is not enough to promote J as final.

## Recommendation

Do not make a Pine edit yet.

The evidence now points to a portfolio/admission problem more than an entry-threshold problem. The next useful step is one more small diagnostic batch, not a new threshold:

- `BINANCE:OPUSDT.P`
- `BINANCE:PENDLEUSDT.P`

If that batch also shows symbol-specific dispersion, the next implementation should be an explicit symbol-admission harness or config layer, not another hidden global entry filter. If OP/PENDLE show a consistent feature failure shared with SUI/LINK/XRP/PYTH, then a narrow Unity-themed reaction-quality gate becomes more defensible.

Overfit risk remains high for any immediate Pine change.
