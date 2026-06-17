# V7 Snapshot Window Validation Verdict

Generated from the recovered TradingView snapshot-window run set on 2026-06-04.

## Executive Verdict

The interrupted TradingView session contaminated one latest-window automation run, but the contaminated symbols were rerun with targeted retries. The latest 2026 window now has clean coverage for all 13 configured symbols.

This does not validate QS3 + 5m as historically robust. The normal TradingView Strategy Tester custom date-range path could not provide the older 5m windows needed for an implementation verdict. Treat the latest-window results as a promising short-horizon signal only.

Primary verdict from `snapshot_window_validation_metrics.md`: not enough TradingView historical coverage.

## Contamination Audit

The suspect run was:

- `v7-snapshot-qs3-5m-latest-2026/2026-06-03T23-15-23-948Z-snapshot-window-matrix`

That run produced a valid BTC result, then failed on ETH, SOL, BNB, DOGE, ZEC, ARB, LINK, XRP, HYPE, AERO, VIRTUAL, and RENDER. The failure pattern was UI-state contamination, including Strategy Report not becoming visible and an overlay/backdrop intercepting the Pine button around AERO.

Clean evidence after targeted retries:

| Run timestamp | Clean recovered symbols |
| --- | --- |
| `2026-06-03T02-02-29-217Z` | BTC, ETH, SOL |
| `2026-06-03T23-26-06-024Z` | DOGE, ARB, XRP, AERO, RENDER |
| `2026-06-03T23-56-51-769Z` | ZEC, HYPE |
| `2026-06-04T00-10-50-362Z` | LINK, VIRTUAL |
| `2026-06-04T00-31-33-897Z` | BNB, as a valid no-trade-data slot |

The analyzer was updated to prefer valid evidence over newer failed attempts, so the contaminated report no longer overrides earlier or later clean exports.

## Latest-Window Result

Requested window: 2026-03-22 to 2026-06-02.

TradingView report labels sometimes displayed `Mar 2, 2026` to `Jun 2, 2026` or `Jun 3, 2026`, but the automation selected the requested custom calendar dates and the analyzer counted the requested interval as fully covered.

| Scope | Covered | Trades | P&L | PF | Win % | DD % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Latest 2026 basket | 13/13 | 129 | 3910.99 | 1.793 | 62.0 | 4.71 |

Latest-window classifications:

| Asset | Classification | Trades | P&L | PF | Win % | DD % |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| BTC | thin-negative | 1 | -53.05 | 0.000 | 0.0 | 0.53 |
| ETH | pass | 9 | 527.56 | 2.914 | 66.7 | 2.14 |
| SOL | pass | 7 | 499.00 | 4.083 | 71.4 | 1.08 |
| BNB | inconclusive | 0 | 0.00 | 0.000 | n/a | 0.00 |
| DOGE | pass | 12 | 201.08 | 1.340 | 50.0 | 2.64 |
| ZEC | pass | 26 | 749.08 | 1.730 | 73.1 | 3.18 |
| ARB | pass | 7 | 603.61 | 16.931 | 85.7 | 0.36 |
| LINK | pass | 7 | 442.19 | 2.986 | 71.4 | 1.08 |
| XRP | pass | 5 | 248.67 | 2.112 | 80.0 | 2.16 |
| HYPE | pass | 22 | 1016.96 | 2.665 | 68.2 | 3.14 |
| AERO | fail | 17 | -40.56 | 0.952 | 47.1 | 2.61 |
| VIRTUAL | inconclusive | 0 | 0.00 | 0.000 | n/a | 0.00 |
| RENDER | fail | 16 | -283.55 | 0.682 | 37.5 | 4.61 |

## Historical Coverage Gap

Configured validation expected 65 symbol-window slots across six windows. Only the latest 13 slots were covered.

| Window | Requested | Covered |
| --- | --- | ---: |
| latest-2026 | 2026-03-22 to 2026-06-02 | 13/13 |
| prior-2026 | 2025-12-15 to 2026-03-14 | 0/13 |
| q4-2025 | 2025-09-01 to 2025-11-30 | 0/13 |
| q3-2024 | 2024-07-01 to 2024-09-30 | 0/10 |
| bear-2022 | 2022-05-01 to 2022-07-31 | 0/8 |
| top-2021 | 2021-10-01 to 2021-12-31 | 0/8 |

The older windows should not be treated as strategy failures. They are coverage failures. A BTC custom-date probe for `prior-2026` reached the Strategy Tester date-range calendar but could not navigate before March 2026, while the target start was 2025-12-15. Since BTC should be among the deepest available 5m histories, this is strong evidence that the normal Strategy Tester custom-date path is insufficient for this historical validation shape.

## Next Decision

Do not lock QS3 + 5m as the Unity Trading Model implementation from this run. The latest-window performance is encouraging, but it is only one recent regime.

The next validation step must stay TradingView-sourced and use a path that can access older history, likely TradingView Deep Backtesting or an equivalent TradingView report export path. If that is not available, claims should be limited to latest-window and live-forward validation.
