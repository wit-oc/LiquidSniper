# V7 HTF Premise Validation Metrics

Generated from 1 run(s). Minimum coverage gate: 365 days. Evidence trade gate: 10 trades.

## Verdict Inputs

- Primary verdict: candidate rejected
- 4H rows with >=365 days: 17/17
- Materially capped under one year: no
- Pass assets: none
- Fail assets: none
- Thin assets: ADA:thin-negative, XRP:thin-positive, BTC:thin-negative, BNB:thin-positive, DOGE:thin-positive
- Recommendation: Do not lock the strategy as globally robust; inspect failed symbols and temporal concentration before any implementation commitment.

## Run: v7-htf-premise-qs3-4h

Expected slots: 17. Accounted: 17. Missing: 0. Failed: 0. Rejected report candidates: 0.

### Basket
| Scope | Trades | P&L | PF | Win % | DD % |
| --- | ---: | ---: | ---: | ---: | ---: |
| all_symbols | 56 | 239.88 | 1.092 | 53.6 | 7.20 |

### Per-Symbol Metrics And Classification
| Asset | TV Symbol | Tier | Prior | TF | Status | Class | Reason | Range | Days | Trades | P&L | PF | Win % | DD % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ZEC | ZEC | prior admitted control | pass | 4H | ok | inconclusive | fewer than 3 trades | Mar 21, 2019 to May 31, 2026 | 2630 | 1 | -102.61 | 0.000 | 0.0 | 1.03 |
| ADA | ADA | prior admitted control | pass | 4H | ok | thin-negative | negative but fewer than 10 trades | Apr 17, 2018 to May 31, 2026 | 2968 | 3 | -113.01 | 0.462 | 33.3 | 1.13 |
| LINK | LINK | prior admitted control | pass | 4H | ok | inconclusive | fewer than 10 evidence trades | Jan 16, 2019 to May 31, 2026 | 2694 | 5 | 70.51 | 1.311 | 60.0 | 2.21 |
| XRP | XRP | prior admitted control | pass | 4H | ok | thin-positive | positive but fewer than 10 trades | May 4, 2018 to May 31, 2026 | 2951 | 5 | 90.30 | 1.578 | 60.0 | 1.03 |
| ARB | ARB | prior admitted control | pass | 4H | ok | inconclusive | fewer than 10 evidence trades | Mar 23, 2023 to May 31, 2026 | 1167 | 5 | 40.94 | 1.263 | 60.0 | 1.05 |
| PYTH | PYTH | prior admitted control | pass | 4H | no_trade_data | inconclusive | valid export with no trades | Feb 2, 2024 to May 31, 2026 | 851 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| SEI | SEI | prior admitted control | pass | 4H | ok | inconclusive | fewer than 3 trades | Aug 15, 2023 to May 31, 2026 | 1022 | 1 | -101.97 | 0.000 | 0.0 | 1.02 |
| BTC | BTC | prior failed control | fail | 4H | ok | thin-negative | negative but fewer than 10 trades | Aug 17, 2017 to May 31, 2026 | 3211 | 9 | -433.07 | 0.352 | 33.3 | 5.25 |
| ETH | ETH | major control | diagnostic-only | 4H | ok | inconclusive | fewer than 10 evidence trades | Aug 17, 2017 to May 31, 2026 | 3211 | 7 | 81.97 | 1.316 | 57.1 | 2.53 |
| SOL | SOL | prior failed control | fail | 4H | ok | inconclusive | fewer than 3 trades | Aug 11, 2020 to May 31, 2026 | 2121 | 2 | -56.08 | 0.632 | 50.0 | 1.52 |
| BNB | BNB | prior failed control | fail | 4H | ok | thin-positive | positive but fewer than 10 trades | Nov 5, 2017 to May 31, 2026 | 3131 | 8 | 585.15 | 3.754 | 75.0 | 1.53 |
| DOGE | DOGE | prior failed control | fail | 4H | ok | thin-positive | positive but fewer than 10 trades | Jul 5, 2019 to May 31, 2026 | 2524 | 3 | 47.00 | 1.454 | 66.7 | 1.02 |
| LTC | LTC | major control | marginal | 4H | ok | inconclusive | fewer than 10 evidence trades | Dec 12, 2017 to May 31, 2026 | 3094 | 6 | 33.91 | 1.131 | 50.0 | 1.54 |
| HYPE | HYPE.P | perp route probe | spot-route-unresolved | 4H | no_trade_data | inconclusive | valid export with no trades | May 30, 2025 to May 31, 2026 | 368 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| AERO | AERO.P | perp route probe | spot-route-unresolved | 4H | no_trade_data | inconclusive | valid export with no trades | Dec 4, 2024 to May 31, 2026 | 545 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| VIRTUAL | VIRTUAL.P | perp route probe | new | 4H | no_trade_data | inconclusive | valid export with no trades | Dec 10, 2024 to May 31, 2026 | 539 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| RENDER | RENDER.P | perp route probe | spot-route-fail | 4H | ok | inconclusive | fewer than 3 trades | Feb 2, 2023 to May 31, 2026 | 1216 | 1 | 96.84 | n/a | 100.0 | 0.00 |

### Scope Summary
| Scope | Trades | P&L | PF | Win % | DD % |
| --- | ---: | ---: | ---: | ---: | ---: |
| All symbols | 56 | 239.88 | 1.092 | 53.6 | 7.20 |
| Prior admitted controls | 20 | -115.84 | 0.879 | 50.0 | 3.87 |
| Prior failed controls | 22 | 143.00 | 1.126 | 54.5 | 5.06 |
| Major controls | 13 | 115.88 | 1.224 | 53.8 | 2.56 |
| Perp route probes | 1 | 96.84 | n/a | 100.0 | 0.00 |
| Failed+perp controls | 23 | 239.84 | 1.211 | 56.5 | 5.02 |

### Temporal Persistence
| Asset | TF | Class | Positive Years | Positive Year % | Trades | P&L | PF | DD % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ZEC | 4H | inconclusive | 0 | n/a | 1 | -102.61 | 0.000 | 1.03 |
| ADA | 4H | thin-negative | 0 | 0.0 | 3 | -113.01 | 0.462 | 1.13 |
| LINK | 4H | inconclusive | 0 | n/a | 5 | 70.51 | 1.311 | 2.21 |
| XRP | 4H | thin-positive | 0 | n/a | 5 | 90.30 | 1.578 | 1.03 |
| ARB | 4H | inconclusive | 1 | 100.0 | 5 | 40.94 | 1.263 | 1.05 |
| PYTH | 4H | inconclusive | 0 | n/a | 0 | 0.00 | 0.000 | 0.00 |
| SEI | 4H | inconclusive | 0 | n/a | 1 | -101.97 | 0.000 | 1.02 |
| BTC | 4H | thin-negative | 1 | 100.0 | 9 | -433.07 | 0.352 | 5.25 |
| ETH | 4H | inconclusive | 0 | n/a | 7 | 81.97 | 1.316 | 2.53 |
| SOL | 4H | inconclusive | 0 | n/a | 2 | -56.08 | 0.632 | 1.52 |
| BNB | 4H | thin-positive | 0 | n/a | 8 | 585.15 | 3.754 | 1.53 |
| DOGE | 4H | thin-positive | 0 | n/a | 3 | 47.00 | 1.454 | 1.02 |
| LTC | 4H | inconclusive | 0 | n/a | 6 | 33.91 | 1.131 | 1.54 |
| HYPE | 4H | inconclusive | 0 | n/a | 0 | 0.00 | 0.000 | 0.00 |
| AERO | 4H | inconclusive | 0 | n/a | 0 | 0.00 | 0.000 | 0.00 |
| VIRTUAL | 4H | inconclusive | 0 | n/a | 0 | 0.00 | 0.000 | 0.00 |
| RENDER | 4H | inconclusive | 0 | n/a | 1 | 96.84 | n/a | 0.00 |

### Market Regime Segments
| Asset | TF | Regime | Trades | P&L | PF | Win % | DD % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| ADA | 4H | 2019-2020 accumulation | 3 | -113.01 | 0.462 | 33.3 | 1.13 |
| ARB | 4H | 2023 recovery | 3 | 94.94 | 2.817 | 66.7 | 0.51 |
| ARB | 4H | 2024 cycle | 1 | 49.46 | n/a | 100.0 | 0.00 |
| ARB | 4H | 2025-2026 current | 1 | -103.46 | 0.000 | 0.0 | 1.03 |
| BNB | 4H | 2019-2020 accumulation | 3 | 143.70 | 3.709 | 66.7 | 0.52 |
| BNB | 4H | 2023 recovery | 2 | 296.58 | n/a | 100.0 | 0.00 |
| BNB | 4H | 2024 cycle | 1 | -159.42 | 0.000 | 0.0 | 1.59 |
| BNB | 4H | 2025-2026 current | 2 | 304.29 | n/a | 100.0 | 0.00 |
| BTC | 4H | 2017-2018 prior cycle | 1 | -215.34 | 0.000 | 0.0 | 2.15 |
| BTC | 4H | 2021 bull/top | 1 | -102.05 | 0.000 | 0.0 | 1.02 |
| BTC | 4H | 2022 bear | 3 | 91.08 | 2.759 | 66.7 | 0.51 |
| BTC | 4H | 2023 recovery | 2 | -199.68 | 0.000 | 0.0 | 2.00 |
| BTC | 4H | 2024 cycle | 1 | -99.40 | 0.000 | 0.0 | 0.99 |
| BTC | 4H | 2025-2026 current | 1 | 92.32 | n/a | 100.0 | 0.00 |
| DOGE | 4H | 2019-2020 accumulation | 1 | 101.09 | n/a | 100.0 | 0.00 |
| DOGE | 4H | 2022 bear | 1 | 49.44 | n/a | 100.0 | 0.00 |
| DOGE | 4H | 2025-2026 current | 1 | -103.53 | 0.000 | 0.0 | 1.04 |
| ETH | 4H | 2019-2020 accumulation | 1 | 94.97 | n/a | 100.0 | 0.00 |
| ETH | 4H | 2022 bear | 2 | 148.71 | n/a | 100.0 | 0.00 |
| ETH | 4H | 2023 recovery | 2 | -207.77 | 0.000 | 0.0 | 2.08 |
| ETH | 4H | 2024 cycle | 1 | -51.77 | 0.000 | 0.0 | 0.52 |
| ETH | 4H | 2025-2026 current | 1 | 97.83 | n/a | 100.0 | 0.00 |
| LINK | 4H | 2019-2020 accumulation | 2 | 247.19 | n/a | 100.0 | 0.00 |
| LINK | 4H | 2022 bear | 1 | 50.40 | n/a | 100.0 | 0.00 |
| LINK | 4H | 2023 recovery | 1 | -175.49 | 0.000 | 0.0 | 1.75 |
| LINK | 4H | 2025-2026 current | 1 | -51.59 | 0.000 | 0.0 | 0.52 |
| LTC | 4H | 2017-2018 prior cycle | 2 | -54.15 | 0.475 | 50.0 | 1.03 |
| LTC | 4H | 2019-2020 accumulation | 2 | 44.41 | 1.868 | 50.0 | 0.51 |
| LTC | 4H | 2021 bull/top | 1 | 147.21 | n/a | 100.0 | 0.00 |
| LTC | 4H | 2025-2026 current | 1 | -103.56 | 0.000 | 0.0 | 1.04 |
| RENDER | 4H | 2023 recovery | 1 | 96.84 | n/a | 100.0 | 0.00 |
| SEI | 4H | 2025-2026 current | 1 | -101.97 | 0.000 | 0.0 | 1.02 |
| SOL | 4H | 2025-2026 current | 2 | -56.08 | 0.632 | 50.0 | 1.52 |
| XRP | 4H | 2017-2018 prior cycle | 1 | 97.85 | n/a | 100.0 | 0.00 |
| XRP | 4H | 2022 bear | 1 | -51.59 | 0.000 | 0.0 | 0.52 |
| XRP | 4H | 2024 cycle | 2 | 148.55 | n/a | 100.0 | 0.00 |
| XRP | 4H | 2025-2026 current | 1 | -104.51 | 0.000 | 0.0 | 1.05 |
| ZEC | 4H | 2022 bear | 1 | -102.61 | 0.000 | 0.0 | 1.03 |

### Year Segments
| Asset | TF | Year | Trades | P&L | PF | Win % | DD % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| ADA | 4H | 2019 | 3 | -113.01 | 0.462 | 33.3 | 1.13 |
| ARB | 4H | 2023 | 3 | 94.94 | 2.817 | 66.7 | 0.51 |
| ARB | 4H | 2024 | 1 | 49.46 | n/a | 100.0 | 0.00 |
| ARB | 4H | 2025 | 1 | -103.46 | 0.000 | 0.0 | 1.03 |
| BNB | 4H | 2019 | 1 | 147.45 | n/a | 100.0 | 0.00 |
| BNB | 4H | 2020 | 2 | -3.75 | 0.929 | 50.0 | 0.53 |
| BNB | 4H | 2023 | 2 | 296.58 | n/a | 100.0 | 0.00 |
| BNB | 4H | 2024 | 1 | -159.42 | 0.000 | 0.0 | 1.59 |
| BNB | 4H | 2025 | 2 | 304.29 | n/a | 100.0 | 0.00 |
| BTC | 4H | 2018 | 1 | -215.34 | 0.000 | 0.0 | 2.15 |
| BTC | 4H | 2021 | 1 | -102.05 | 0.000 | 0.0 | 1.02 |
| BTC | 4H | 2022 | 3 | 91.08 | 2.759 | 66.7 | 0.51 |
| BTC | 4H | 2023 | 2 | -199.68 | 0.000 | 0.0 | 2.00 |
| BTC | 4H | 2024 | 1 | -99.40 | 0.000 | 0.0 | 0.99 |
| BTC | 4H | 2026 | 1 | 92.32 | n/a | 100.0 | 0.00 |
| DOGE | 4H | 2019 | 1 | 101.09 | n/a | 100.0 | 0.00 |
| DOGE | 4H | 2022 | 1 | 49.44 | n/a | 100.0 | 0.00 |
| DOGE | 4H | 2025 | 1 | -103.53 | 0.000 | 0.0 | 1.04 |
| ETH | 4H | 2020 | 1 | 94.97 | n/a | 100.0 | 0.00 |
| ETH | 4H | 2022 | 2 | 148.71 | n/a | 100.0 | 0.00 |
| ETH | 4H | 2023 | 2 | -207.77 | 0.000 | 0.0 | 2.08 |
| ETH | 4H | 2024 | 1 | -51.77 | 0.000 | 0.0 | 0.52 |
| ETH | 4H | 2025 | 1 | 97.83 | n/a | 100.0 | 0.00 |
| LINK | 4H | 2019 | 1 | 98.49 | n/a | 100.0 | 0.00 |
| LINK | 4H | 2020 | 1 | 148.70 | n/a | 100.0 | 0.00 |
| LINK | 4H | 2022 | 1 | 50.40 | n/a | 100.0 | 0.00 |
| LINK | 4H | 2023 | 1 | -175.49 | 0.000 | 0.0 | 1.75 |
| LINK | 4H | 2025 | 1 | -51.59 | 0.000 | 0.0 | 0.52 |
| LTC | 4H | 2018 | 2 | -54.15 | 0.475 | 50.0 | 1.03 |
| LTC | 4H | 2019 | 1 | -51.16 | 0.000 | 0.0 | 0.51 |
| LTC | 4H | 2020 | 1 | 95.57 | n/a | 100.0 | 0.00 |
| LTC | 4H | 2021 | 1 | 147.21 | n/a | 100.0 | 0.00 |
| LTC | 4H | 2026 | 1 | -103.56 | 0.000 | 0.0 | 1.04 |
| RENDER | 4H | 2023 | 1 | 96.84 | n/a | 100.0 | 0.00 |
| SEI | 4H | 2026 | 1 | -101.97 | 0.000 | 0.0 | 1.02 |
| SOL | 4H | 2025 | 2 | -56.08 | 0.632 | 50.0 | 1.52 |
| XRP | 4H | 2018 | 1 | 97.85 | n/a | 100.0 | 0.00 |
| XRP | 4H | 2022 | 1 | -51.59 | 0.000 | 0.0 | 0.52 |
| XRP | 4H | 2024 | 2 | 148.55 | n/a | 100.0 | 0.00 |
| XRP | 4H | 2026 | 1 | -104.51 | 0.000 | 0.0 | 1.05 |
| ZEC | 4H | 2022 | 1 | -102.61 | 0.000 | 0.0 | 1.03 |

### Early/Middle/Latest Windows
| Asset | TF | Window | Trades | P&L | PF | Win % | DD % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| ADA | 4H | early | 3 | -113.01 | 0.462 | 33.3 | 1.13 |
| ARB | 4H | early | 4 | 144.40 | 3.764 | 75.0 | 0.51 |
| ARB | 4H | middle | 1 | -103.46 | 0.000 | 0.0 | 1.03 |
| BNB | 4H | early | 3 | 143.70 | 3.709 | 66.7 | 0.52 |
| BNB | 4H | latest | 5 | 441.45 | 3.769 | 80.0 | 1.55 |
| BTC | 4H | early | 1 | -215.34 | 0.000 | 0.0 | 2.15 |
| BTC | 4H | latest | 3 | -106.47 | 0.464 | 33.3 | 1.99 |
| BTC | 4H | middle | 5 | -111.26 | 0.562 | 40.0 | 1.51 |
| DOGE | 4H | early | 1 | 101.09 | n/a | 100.0 | 0.00 |
| DOGE | 4H | latest | 1 | -103.53 | 0.000 | 0.0 | 1.04 |
| DOGE | 4H | middle | 1 | 49.44 | n/a | 100.0 | 0.00 |
| ETH | 4H | latest | 4 | -161.71 | 0.377 | 25.0 | 2.60 |
| ETH | 4H | middle | 3 | 243.68 | n/a | 100.0 | 0.00 |
| LINK | 4H | early | 2 | 247.19 | n/a | 100.0 | 0.00 |
| LINK | 4H | latest | 1 | -51.59 | 0.000 | 0.0 | 0.52 |
| LINK | 4H | middle | 2 | -125.09 | 0.287 | 50.0 | 1.75 |
| LTC | 4H | early | 4 | -9.74 | 0.937 | 50.0 | 1.54 |
| LTC | 4H | latest | 1 | -103.56 | 0.000 | 0.0 | 1.04 |
| LTC | 4H | middle | 1 | 147.21 | n/a | 100.0 | 0.00 |
| RENDER | 4H | early | 1 | 96.84 | n/a | 100.0 | 0.00 |
| SEI | 4H | latest | 1 | -101.97 | 0.000 | 0.0 | 1.02 |
| SOL | 4H | latest | 2 | -56.08 | 0.632 | 50.0 | 1.52 |
| XRP | 4H | early | 1 | 97.85 | n/a | 100.0 | 0.00 |
| XRP | 4H | latest | 3 | 44.04 | 1.421 | 66.7 | 1.03 |
| XRP | 4H | middle | 1 | -51.59 | 0.000 | 0.0 | 0.52 |
| ZEC | 4H | middle | 1 | -102.61 | 0.000 | 0.0 | 1.03 |
