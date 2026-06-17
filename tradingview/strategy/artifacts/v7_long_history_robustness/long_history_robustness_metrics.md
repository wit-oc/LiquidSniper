# V7 Long-History Robustness Metrics

Generated from 1 run(s). Minimum coverage gate: 365 days. Evidence trade gate: 20 trades.

## Verdict Inputs

- Primary verdict: not enough historical coverage
- 5m rows with >=365 days: 0/17
- Materially capped under one year: yes
- Pass assets: none
- Fail assets: none
- Thin assets: none
- Recommendation: Do not confirm QS3 + 5m. Acquire deeper 5m history through TradingView Deep Backtesting or another TradingView-sourced export path before tuning.

## Run: v7-long-history-qs3-5m

Expected slots: 17. Accounted: 17. Missing: 0. Failed: 0. Rejected report candidates: 0.

### Basket
| Scope | Trades | P&L | PF | Win % | DD % |
| --- | ---: | ---: | ---: | ---: | ---: |
| all_symbols | 196 | 5145.61 | 1.633 | 59.7 | 8.24 |

### Per-Symbol Metrics And Classification
| Asset | TV Symbol | Tier | Prior | TF | Status | Class | Reason | Range | Days | Trades | P&L | PF | Win % | DD % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ZEC | ZEC | prior admitted control | pass | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 31 | 1632.50 | 3.088 | 77.4 | 2.16 |
| ADA | ADA | prior admitted control | pass | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 9 | 192.27 | 1.570 | 55.6 | 1.24 |
| LINK | LINK | prior admitted control | pass | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 7 | 328.38 | 1.973 | 71.4 | 2.16 |
| XRP | XRP | prior admitted control | pass | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 6 | 447.17 | 3.657 | 66.7 | 1.08 |
| ARB | ARB | prior admitted control | pass | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 10 | 671.62 | 4.820 | 80.0 | 1.11 |
| PYTH | PYTH | prior admitted control | pass | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 8 | 379.26 | 2.240 | 75.0 | 2.42 |
| SEI | SEI | prior admitted control | pass | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 9 | 227.48 | 2.140 | 66.7 | 1.40 |
| BTC | BTC | prior failed control | fail | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 4 | 32.84 | 1.308 | 50.0 | 0.53 |
| ETH | ETH | major control | diagnostic-only | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 13 | 459.95 | 1.648 | 61.5 | 4.25 |
| SOL | SOL | prior failed control | fail | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 7 | 52.07 | 1.165 | 42.9 | 3.15 |
| BNB | BNB | prior failed control | fail | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 2 | -15.49 | 0.855 | 50.0 | 1.07 |
| DOGE | DOGE | prior failed control | fail | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 11 | 313.27 | 1.644 | 54.5 | 2.09 |
| LTC | LTC | major control | marginal | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 1 | -53.10 | 0.000 | 0.0 | 0.53 |
| HYPE | HYPE.P | perp route probe | spot-route-unresolved | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 23 | 629.37 | 1.537 | 56.5 | 4.29 |
| AERO | AERO.P | perp route probe | spot-route-unresolved | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 17 | 120.12 | 1.130 | 58.8 | 4.32 |
| VIRTUAL | VIRTUAL.P | perp route probe | new | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 21 | -492.48 | 0.526 | 28.6 | 5.77 |
| RENDER | RENDER.P | perp route probe | spot-route-fail | 5m | ok | inconclusive | history under 365 days | Mar 15, 2026 to May 30, 2026 | 78 | 17 | 220.38 | 1.242 | 58.8 | 5.29 |

### Scope Summary
| Scope | Trades | P&L | PF | Win % | DD % |
| --- | ---: | ---: | ---: | ---: | ---: |
| All symbols | 196 | 5145.61 | 1.633 | 59.7 | 8.24 |
| Prior admitted controls | 80 | 3878.68 | 2.682 | 72.5 | 3.45 |
| Prior failed controls | 24 | 382.69 | 1.377 | 50.0 | 4.79 |
| Major controls | 14 | 406.85 | 1.533 | 57.1 | 4.25 |
| Perp route probes | 78 | 477.39 | 1.118 | 50.0 | 8.46 |
| Failed+perp controls | 102 | 860.08 | 1.170 | 50.0 | 10.74 |

### Temporal Persistence
| Asset | TF | Class | Positive Years | Positive Year % | Trades | P&L | PF | DD % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ZEC | 5m | inconclusive | 1 | 100.0 | 31 | 1632.50 | 3.088 | 2.16 |
| ADA | 5m | inconclusive | 1 | 100.0 | 9 | 192.27 | 1.570 | 1.24 |
| LINK | 5m | inconclusive | 1 | 100.0 | 7 | 328.38 | 1.973 | 2.16 |
| XRP | 5m | inconclusive | 1 | 100.0 | 6 | 447.17 | 3.657 | 1.08 |
| ARB | 5m | inconclusive | 1 | 100.0 | 10 | 671.62 | 4.820 | 1.11 |
| PYTH | 5m | inconclusive | 1 | 100.0 | 8 | 379.26 | 2.240 | 2.42 |
| SEI | 5m | inconclusive | 1 | 100.0 | 9 | 227.48 | 2.140 | 1.40 |
| BTC | 5m | inconclusive | 1 | 100.0 | 4 | 32.84 | 1.308 | 0.53 |
| ETH | 5m | inconclusive | 1 | 100.0 | 13 | 459.95 | 1.648 | 4.25 |
| SOL | 5m | inconclusive | 1 | 100.0 | 7 | 52.07 | 1.165 | 3.15 |
| BNB | 5m | inconclusive | 0 | n/a | 2 | -15.49 | 0.855 | 1.07 |
| DOGE | 5m | inconclusive | 1 | 100.0 | 11 | 313.27 | 1.644 | 2.09 |
| LTC | 5m | inconclusive | 0 | n/a | 1 | -53.10 | 0.000 | 0.53 |
| HYPE | 5m | inconclusive | 1 | 100.0 | 23 | 629.37 | 1.537 | 4.29 |
| AERO | 5m | inconclusive | 1 | 100.0 | 17 | 120.12 | 1.130 | 4.32 |
| VIRTUAL | 5m | inconclusive | 0 | 0.0 | 21 | -492.48 | 0.526 | 5.77 |
| RENDER | 5m | inconclusive | 1 | 100.0 | 17 | 220.38 | 1.242 | 5.29 |

### Market Regime Segments
| Asset | TF | Regime | Trades | P&L | PF | Win % | DD % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| ADA | 5m | 2025-2026 current | 9 | 192.27 | 1.570 | 55.6 | 1.24 |
| AERO | 5m | 2025-2026 current | 17 | 120.12 | 1.130 | 58.8 | 4.32 |
| ARB | 5m | 2025-2026 current | 10 | 671.62 | 4.820 | 80.0 | 1.11 |
| BNB | 5m | 2025-2026 current | 2 | -15.49 | 0.855 | 50.0 | 1.07 |
| BTC | 5m | 2025-2026 current | 4 | 32.84 | 1.308 | 50.0 | 0.53 |
| DOGE | 5m | 2025-2026 current | 11 | 313.27 | 1.644 | 54.5 | 2.09 |
| ETH | 5m | 2025-2026 current | 13 | 459.95 | 1.648 | 61.5 | 4.25 |
| HYPE | 5m | 2025-2026 current | 23 | 629.37 | 1.537 | 56.5 | 4.29 |
| LINK | 5m | 2025-2026 current | 7 | 328.38 | 1.973 | 71.4 | 2.16 |
| LTC | 5m | 2025-2026 current | 1 | -53.10 | 0.000 | 0.0 | 0.53 |
| PYTH | 5m | 2025-2026 current | 8 | 379.26 | 2.240 | 75.0 | 2.42 |
| RENDER | 5m | 2025-2026 current | 17 | 220.38 | 1.242 | 58.8 | 5.29 |
| SEI | 5m | 2025-2026 current | 9 | 227.48 | 2.140 | 66.7 | 1.40 |
| SOL | 5m | 2025-2026 current | 7 | 52.07 | 1.165 | 42.9 | 3.15 |
| VIRTUAL | 5m | 2025-2026 current | 21 | -492.48 | 0.526 | 28.6 | 5.77 |
| XRP | 5m | 2025-2026 current | 6 | 447.17 | 3.657 | 66.7 | 1.08 |
| ZEC | 5m | 2025-2026 current | 31 | 1632.50 | 3.088 | 77.4 | 2.16 |

### Year Segments
| Asset | TF | Year | Trades | P&L | PF | Win % | DD % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| ADA | 5m | 2026 | 9 | 192.27 | 1.570 | 55.6 | 1.24 |
| AERO | 5m | 2026 | 17 | 120.12 | 1.130 | 58.8 | 4.32 |
| ARB | 5m | 2026 | 10 | 671.62 | 4.820 | 80.0 | 1.11 |
| BNB | 5m | 2026 | 2 | -15.49 | 0.855 | 50.0 | 1.07 |
| BTC | 5m | 2026 | 4 | 32.84 | 1.308 | 50.0 | 0.53 |
| DOGE | 5m | 2026 | 11 | 313.27 | 1.644 | 54.5 | 2.09 |
| ETH | 5m | 2026 | 13 | 459.95 | 1.648 | 61.5 | 4.25 |
| HYPE | 5m | 2026 | 23 | 629.37 | 1.537 | 56.5 | 4.29 |
| LINK | 5m | 2026 | 7 | 328.38 | 1.973 | 71.4 | 2.16 |
| LTC | 5m | 2026 | 1 | -53.10 | 0.000 | 0.0 | 0.53 |
| PYTH | 5m | 2026 | 8 | 379.26 | 2.240 | 75.0 | 2.42 |
| RENDER | 5m | 2026 | 17 | 220.38 | 1.242 | 58.8 | 5.29 |
| SEI | 5m | 2026 | 9 | 227.48 | 2.140 | 66.7 | 1.40 |
| SOL | 5m | 2026 | 7 | 52.07 | 1.165 | 42.9 | 3.15 |
| VIRTUAL | 5m | 2026 | 21 | -492.48 | 0.526 | 28.6 | 5.77 |
| XRP | 5m | 2026 | 6 | 447.17 | 3.657 | 66.7 | 1.08 |
| ZEC | 5m | 2026 | 31 | 1632.50 | 3.088 | 77.4 | 2.16 |

### Early/Middle/Latest Windows
| Asset | TF | Window | Trades | P&L | PF | Win % | DD % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| ADA | 5m | early | 4 | 270.24 | 3.442 | 75.0 | 1.08 |
| ADA | 5m | latest | 5 | -77.97 | 0.656 | 40.0 | 1.27 |
| AERO | 5m | early | 4 | 173.06 | 2.542 | 75.0 | 1.09 |
| AERO | 5m | latest | 6 | -91.18 | 0.761 | 50.0 | 2.20 |
| AERO | 5m | middle | 7 | 38.24 | 1.089 | 57.1 | 4.25 |
| ARB | 5m | early | 1 | 48.86 | n/a | 100.0 | 0.00 |
| ARB | 5m | latest | 7 | 333.09 | 2.894 | 71.4 | 1.14 |
| ARB | 5m | middle | 2 | 289.67 | n/a | 100.0 | 0.00 |
| BNB | 5m | early | 2 | -15.49 | 0.855 | 50.0 | 1.07 |
| BTC | 5m | early | 3 | 86.34 | 2.626 | 66.7 | 0.53 |
| BTC | 5m | middle | 1 | -53.50 | 0.000 | 0.0 | 0.53 |
| DOGE | 5m | early | 3 | 22.58 | 1.142 | 33.3 | 1.60 |
| DOGE | 5m | latest | 2 | -10.30 | 0.905 | 50.0 | 1.08 |
| DOGE | 5m | middle | 6 | 300.99 | 2.377 | 66.7 | 1.06 |
| ETH | 5m | early | 5 | -128.27 | 0.519 | 40.0 | 1.28 |
| ETH | 5m | latest | 2 | 287.41 | n/a | 100.0 | 0.00 |
| ETH | 5m | middle | 6 | 300.81 | 1.678 | 66.7 | 4.20 |
| HYPE | 5m | early | 5 | -429.44 | 0.173 | 20.0 | 4.29 |
| HYPE | 5m | latest | 9 | 160.17 | 1.363 | 55.6 | 3.29 |
| HYPE | 5m | middle | 9 | 898.64 | 5.245 | 77.8 | 1.01 |
| LINK | 5m | latest | 7 | 328.38 | 1.973 | 71.4 | 2.16 |
| LTC | 5m | latest | 1 | -53.10 | 0.000 | 0.0 | 0.53 |
| PYTH | 5m | early | 2 | 162.81 | n/a | 100.0 | 0.00 |
| PYTH | 5m | latest | 5 | 462.10 | 8.681 | 80.0 | 0.57 |
| PYTH | 5m | middle | 1 | -245.65 | 0.000 | 0.0 | 2.46 |
| RENDER | 5m | early | 8 | -458.61 | 0.387 | 37.5 | 5.29 |
| RENDER | 5m | latest | 7 | 319.71 | 2.984 | 71.4 | 1.55 |
| RENDER | 5m | middle | 2 | 359.28 | n/a | 100.0 | 0.00 |
| SEI | 5m | early | 3 | 86.18 | 2.594 | 66.7 | 0.54 |
| SEI | 5m | latest | 4 | -47.32 | 0.675 | 50.0 | 1.44 |
| SEI | 5m | middle | 2 | 188.62 | n/a | 100.0 | 0.00 |
| SOL | 5m | early | 4 | -315.09 | 0.000 | 0.0 | 3.15 |
| SOL | 5m | latest | 3 | 367.16 | n/a | 100.0 | 0.00 |
| VIRTUAL | 5m | early | 8 | -131.49 | 0.589 | 37.5 | 1.79 |
| VIRTUAL | 5m | latest | 7 | -174.46 | 0.509 | 28.6 | 3.03 |
| VIRTUAL | 5m | middle | 6 | -186.53 | 0.487 | 16.7 | 3.63 |
| XRP | 5m | early | 4 | 464.18 | 9.520 | 75.0 | 0.53 |
| XRP | 5m | latest | 2 | -17.01 | 0.851 | 50.0 | 1.13 |
| ZEC | 5m | early | 12 | 567.91 | 6.308 | 83.3 | 0.53 |
| ZEC | 5m | latest | 11 | 362.61 | 1.645 | 63.6 | 2.42 |
| ZEC | 5m | middle | 8 | 701.98 | 7.227 | 87.5 | 1.12 |
