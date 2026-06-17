# V7 Snapshot Window Validation Metrics

Generated from 6 configured window run(s). Evidence trade gate: 5 trades. Window coverage gate: 75%.

## Verdict Inputs

- Primary verdict: not enough TradingView historical coverage
- Covered slots: 13/65 (20.0%)
- Covered non-latest slots: 0 (0.0%)
- Coverage-failure slots: 52
- Pass slots: 8
- Fail slots: 2
- Destructive slots including thin-negative: 3
- Recommendation: Do not confirm QS3 + 5m until TradingView can provide older 5m windows through Deep Backtesting or another TradingView-sourced export path.

## Covered Basket
| Scope | Trades | P&L | PF | Win % | DD % |
| --- | ---: | ---: | ---: | ---: | ---: |
| covered_slots | 129 | 3910.99 | 1.793 | 62.0 | 4.71 |

## Window Summary
| Window | Requested | Covered Slots | Coverage % | Pass | Fail | Thin+ | Thin- | Trades | P&L | PF | Win % | DD % |
| --- | --- | ---: | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| latest-2026 | 2026-03-22 to 2026-06-02 | 13/13 | 100.0 | 8 | 2 | 0 | 1 | 129 | 3910.99 | 1.793 | 62.0 | 4.71 |
| prior-2026 | 2025-12-15 to 2026-03-14 | 0/13 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q4-2025 | 2025-09-01 to 2025-11-30 | 0/13 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q3-2024 | 2024-07-01 to 2024-09-30 | 0/10 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| bear-2022 | 2022-05-01 to 2022-07-31 | 0/8 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| top-2021 | 2021-10-01 to 2021-12-31 | 0/8 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.000 | n/a | 0.00 |

## Symbol Persistence On Covered Windows
| Asset | Symbol | Covered Windows | Pass | Fail | Thin+ | Thin- | Trades | P&L | PF | Win % | DD % |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| BTC | BTC | 1 | 0 | 0 | 0 | 1 | 1 | -53.05 | 0.000 | 0.0 | 0.53 |
| ETH | ETH | 1 | 1 | 0 | 0 | 0 | 9 | 527.56 | 2.914 | 66.7 | 2.14 |
| SOL | SOL | 1 | 1 | 0 | 0 | 0 | 7 | 499.00 | 4.083 | 71.4 | 1.08 |
| BNB | BNB | 1 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| DOGE | DOGE | 1 | 1 | 0 | 0 | 0 | 12 | 201.08 | 1.340 | 50.0 | 2.64 |
| ZEC | ZEC | 1 | 1 | 0 | 0 | 0 | 26 | 749.08 | 1.730 | 73.1 | 3.18 |
| ARB | ARB | 1 | 1 | 0 | 0 | 0 | 7 | 603.61 | 16.931 | 85.7 | 0.36 |
| LINK | LINK | 1 | 1 | 0 | 0 | 0 | 7 | 442.19 | 2.986 | 71.4 | 1.08 |
| XRP | XRP | 1 | 1 | 0 | 0 | 0 | 5 | 248.67 | 2.112 | 80.0 | 2.16 |
| HYPE | HYPE.P | 1 | 1 | 0 | 0 | 0 | 22 | 1016.96 | 2.665 | 68.2 | 3.14 |
| AERO | AERO.P | 1 | 0 | 1 | 0 | 0 | 17 | -40.56 | 0.952 | 47.1 | 2.61 |
| VIRTUAL | VIRTUAL.P | 1 | 0 | 0 | 0 | 0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| RENDER | RENDER.P | 1 | 0 | 1 | 0 | 0 | 16 | -283.55 | 0.682 | 37.5 | 4.61 |

## Per-Symbol Window Classifications
| Window | Asset | TV Symbol | Status | Coverage | Class | Reason | Requested | TV Range | Overlap % | Trades | P&L | PF | Win % | DD % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| latest-2026 | BTC | BTC | ok | covered | thin-negative | negative/weak but fewer than 5 trades | 2026-03-22 to 2026-06-02 | Mar 2, 2026 to Jun 2, 2026 | 100.0 | 1 | -53.05 | 0.000 | 0.0 | 0.53 |
| latest-2026 | ETH | ETH | ok | covered | pass | meets snapshot PF/P&L/DD gate | 2026-03-22 to 2026-06-02 | Mar 2, 2026 to Jun 2, 2026 | 100.0 | 9 | 527.56 | 2.914 | 66.7 | 2.14 |
| latest-2026 | SOL | SOL | ok | covered | pass | meets snapshot PF/P&L/DD gate | 2026-03-22 to 2026-06-02 | Mar 2, 2026 to Jun 2, 2026 | 100.0 | 7 | 499.00 | 4.083 | 71.4 | 1.08 |
| latest-2026 | BNB | BNB | no_trade_data | covered | inconclusive | adequate window coverage but no trades | 2026-03-22 to 2026-06-02 | Mar 2, 2026 to Jun 2, 2026 | 100.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| latest-2026 | DOGE | DOGE | ok | covered | pass | meets snapshot PF/P&L/DD gate | 2026-03-22 to 2026-06-02 | Mar 2, 2026 to Jun 2, 2026 | 100.0 | 12 | 201.08 | 1.340 | 50.0 | 2.64 |
| latest-2026 | ZEC | ZEC | ok | covered | pass | meets snapshot PF/P&L/DD gate | 2026-03-22 to 2026-06-02 | Mar 2, 2026 to Jun 2, 2026 | 100.0 | 26 | 749.08 | 1.730 | 73.1 | 3.18 |
| latest-2026 | ARB | ARB | ok | covered | pass | meets snapshot PF/P&L/DD gate | 2026-03-22 to 2026-06-02 | Mar 2, 2026 to Jun 2, 2026 | 100.0 | 7 | 603.61 | 16.931 | 85.7 | 0.36 |
| latest-2026 | LINK | LINK | ok | covered | pass | meets snapshot PF/P&L/DD gate | 2026-03-22 to 2026-06-02 | Mar 2, 2026 to Jun 2, 2026 | 100.0 | 7 | 442.19 | 2.986 | 71.4 | 1.08 |
| latest-2026 | XRP | XRP | ok | covered | pass | meets snapshot PF/P&L/DD gate | 2026-03-22 to 2026-06-02 | Mar 2, 2026 to Jun 2, 2026 | 100.0 | 5 | 248.67 | 2.112 | 80.0 | 2.16 |
| latest-2026 | HYPE | HYPE.P | ok | covered | pass | meets snapshot PF/P&L/DD gate | 2026-03-22 to 2026-06-02 | Mar 2, 2026 to Jun 2, 2026 | 100.0 | 22 | 1016.96 | 2.665 | 68.2 | 3.14 |
| latest-2026 | AERO | AERO.P | ok | covered | fail | negative expectancy over adequate sample | 2026-03-22 to 2026-06-02 | Mar 2, 2026 to Jun 2, 2026 | 100.0 | 17 | -40.56 | 0.952 | 47.1 | 2.61 |
| latest-2026 | VIRTUAL | VIRTUAL.P | ok | covered | inconclusive | adequate window coverage but no trades | 2026-03-22 to 2026-06-02 | Mar 2, 2026 to Jun 2, 2026 | 100.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| latest-2026 | RENDER | RENDER.P | ok | covered | fail | negative expectancy over adequate sample | 2026-03-22 to 2026-06-02 | Mar 2, 2026 to Jun 2, 2026 | 100.0 | 16 | -283.55 | 0.682 | 37.5 | 4.61 |
| prior-2026 | BTC | BTC | failed | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-12-15 to 2026-03-14 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| prior-2026 | ETH | ETH | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-12-15 to 2026-03-14 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| prior-2026 | SOL | SOL | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-12-15 to 2026-03-14 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| prior-2026 | BNB | BNB | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-12-15 to 2026-03-14 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| prior-2026 | DOGE | DOGE | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-12-15 to 2026-03-14 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| prior-2026 | ZEC | ZEC | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-12-15 to 2026-03-14 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| prior-2026 | ARB | ARB | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-12-15 to 2026-03-14 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| prior-2026 | LINK | LINK | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-12-15 to 2026-03-14 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| prior-2026 | XRP | XRP | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-12-15 to 2026-03-14 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| prior-2026 | HYPE | HYPE.P | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-12-15 to 2026-03-14 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| prior-2026 | AERO | AERO.P | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-12-15 to 2026-03-14 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| prior-2026 | VIRTUAL | VIRTUAL.P | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-12-15 to 2026-03-14 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| prior-2026 | RENDER | RENDER.P | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-12-15 to 2026-03-14 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q4-2025 | BTC | BTC | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-09-01 to 2025-11-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q4-2025 | ETH | ETH | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-09-01 to 2025-11-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q4-2025 | SOL | SOL | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-09-01 to 2025-11-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q4-2025 | BNB | BNB | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-09-01 to 2025-11-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q4-2025 | DOGE | DOGE | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-09-01 to 2025-11-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q4-2025 | ZEC | ZEC | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-09-01 to 2025-11-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q4-2025 | ARB | ARB | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-09-01 to 2025-11-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q4-2025 | LINK | LINK | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-09-01 to 2025-11-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q4-2025 | XRP | XRP | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-09-01 to 2025-11-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q4-2025 | HYPE | HYPE.P | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-09-01 to 2025-11-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q4-2025 | AERO | AERO.P | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-09-01 to 2025-11-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q4-2025 | VIRTUAL | VIRTUAL.P | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-09-01 to 2025-11-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q4-2025 | RENDER | RENDER.P | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2025-09-01 to 2025-11-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q3-2024 | BTC | BTC | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2024-07-01 to 2024-09-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q3-2024 | ETH | ETH | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2024-07-01 to 2024-09-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q3-2024 | SOL | SOL | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2024-07-01 to 2024-09-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q3-2024 | BNB | BNB | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2024-07-01 to 2024-09-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q3-2024 | DOGE | DOGE | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2024-07-01 to 2024-09-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q3-2024 | ZEC | ZEC | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2024-07-01 to 2024-09-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q3-2024 | ARB | ARB | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2024-07-01 to 2024-09-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q3-2024 | LINK | LINK | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2024-07-01 to 2024-09-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q3-2024 | XRP | XRP | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2024-07-01 to 2024-09-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| q3-2024 | RENDER | RENDER.P | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2024-07-01 to 2024-09-30 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| bear-2022 | BTC | BTC | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2022-05-01 to 2022-07-31 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| bear-2022 | ETH | ETH | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2022-05-01 to 2022-07-31 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| bear-2022 | SOL | SOL | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2022-05-01 to 2022-07-31 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| bear-2022 | BNB | BNB | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2022-05-01 to 2022-07-31 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| bear-2022 | DOGE | DOGE | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2022-05-01 to 2022-07-31 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| bear-2022 | ZEC | ZEC | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2022-05-01 to 2022-07-31 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| bear-2022 | LINK | LINK | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2022-05-01 to 2022-07-31 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| bear-2022 | XRP | XRP | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2022-05-01 to 2022-07-31 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| top-2021 | BTC | BTC | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2021-10-01 to 2021-12-31 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| top-2021 | ETH | ETH | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2021-10-01 to 2021-12-31 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| top-2021 | SOL | SOL | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2021-10-01 to 2021-12-31 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| top-2021 | BNB | BNB | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2021-10-01 to 2021-12-31 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| top-2021 | DOGE | DOGE | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2021-10-01 to 2021-12-31 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| top-2021 | ZEC | ZEC | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2021-10-01 to 2021-12-31 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| top-2021 | LINK | LINK | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2021-10-01 to 2021-12-31 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |
| top-2021 | XRP | XRP | missing | coverage-failure | inconclusive | TradingView report range was not detectable | 2021-10-01 to 2021-12-31 | n/a | 0.0 | 0 | 0.00 | 0.000 | n/a | 0.00 |

## Run Inventory
| Run | Window | Symbols | Requested Days |
| --- | --- | --- | ---: |
| v7-snapshot-qs3-5m-latest-2026 | latest-2026 | 13 | 74 |
| v7-snapshot-qs3-5m-prior-2026 | prior-2026 | 13 | 91 |
| v7-snapshot-qs3-5m-q4-2025 | q4-2025 | 13 | 92 |
| v7-snapshot-qs3-5m-q3-2024 | q3-2024 | 10 | 93 |
| v7-snapshot-qs3-5m-bear-2022 | bear-2022 | 8 | 93 |
| v7-snapshot-qs3-5m-top-2021 | top-2021 | 8 | 93 |
