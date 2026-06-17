# V7 Generalization Independent Variables Metrics

Manifest: `tradingview/strategy/artifacts/v7_generalization_independent_variables/tv_generalization_independent_variables_runs.json`
Telemetry root: `tradingview/strategy/.telemetry/outputs/v7_generalization_independent_variables`

## Coverage
| Variant | OK Slots | No Trade | Failed | Missing |
| --- | ---: | --- | --- | --- |
| Baseline 125bps | 32 | 0 | 0 | 0 |
| Quality Score 3 | 31 | 1 | 0 | 0 |
| ATR Regime Filter | 32 | 0 | 0 | 0 |
| Close Confirmed Stop | 32 | 0 | 0 | 0 |

## Basket Scorecard
| Variant | Trades | P&L | PF | Win % | DD % | Positive Rows | Negative Rows | PF<1 Rows | DD>5 Rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline 125bps | 473 | 5106.00 | 1.289 | 56.0 | 14.14 | 21 | 11 | 11 | 6 |
| Quality Score 3 | 439 | 5430.79 | 1.328 | 56.9 | 13.38 | 21 | 10 | 10 | 6 |
| ATR Regime Filter | 476 | 4690.21 | 1.264 | 55.9 | 14.44 | 21 | 11 | 11 | 7 |
| Close Confirmed Stop | 469 | 4109.55 | 1.213 | 58.6 | 24.52 | 20 | 12 | 12 | 7 |

## Baseline Delta Ranking
| Variant | Delta P&L | Delta PF | Delta DD % | Improved Slots | Degraded Slots | Improved Symbols | Degraded Symbols | Score |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: |
| Quality Score 3 | 324.79 | 0.039 | -0.75 | 8 | 9 | 8 | 5 | 4.02 |
| ATR Regime Filter | -415.79 | -0.025 | 0.30 | 1 | 8 | 1 | 7 | -11.65 |
| Close Confirmed Stop | -996.45 | -0.076 | 10.38 | 4 | 22 | 3 | 9 | -27.95 |

## Symbol Classifications
| Variant | Pass | Marginal | Fail |
| --- | --- | --- | --- |
| Baseline 125bps | ADA, ARB, LINK, PYTH, SEI, XRP, ZEC | LTC | AERO, BNB, BTC, DOGE, ETH, HYPE, RENDER, SOL |
| Quality Score 3 | ADA, ARB, LINK, LTC, PYTH, SEI, XRP, ZEC | none | AERO, BNB, DOGE, ETH, HYPE, RENDER, SOL |
| ATR Regime Filter | ADA, ARB, LINK, PYTH, SEI, XRP, ZEC | LTC | AERO, BNB, BTC, DOGE, ETH, HYPE, RENDER, SOL |
| Close Confirmed Stop | ARB, LINK, PYTH, SEI, ZEC | ADA, LTC, XRP | AERO, BNB, BTC, DOGE, ETH, HYPE, RENDER, SOL |

## Timeframe Rows
| Variant | Asset | TF | Status | Trades | P&L | PF | Win % | DD % |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Baseline 125bps | ADA | 15m | ok | 22 | 437.36 | 1.876 | 68.2 | 1.62 |
| Baseline 125bps | ADA | 5m | ok | 9 | 196.46 | 1.590 | 55.6 | 1.20 |
| Baseline 125bps | AERO | 15m | ok | 24 | -241.01 | 0.748 | 50.0 | 6.00 |
| Baseline 125bps | AERO | 5m | ok | 19 | 143.97 | 1.156 | 57.9 | 4.32 |
| Baseline 125bps | ARB | 15m | ok | 23 | 241.16 | 1.402 | 65.2 | 2.12 |
| Baseline 125bps | ARB | 5m | ok | 10 | 552.31 | 2.882 | 80.0 | 2.21 |
| Baseline 125bps | BNB | 15m | ok | 13 | -471.18 | 0.309 | 30.8 | 5.24 |
| Baseline 125bps | BNB | 5m | ok | 2 | -15.49 | 0.855 | 50.0 | 1.07 |
| Baseline 125bps | BTC | 15m | ok | 15 | -173.79 | 0.728 | 46.7 | 2.80 |
| Baseline 125bps | BTC | 5m | ok | 4 | 32.84 | 1.308 | 50.0 | 0.53 |
| Baseline 125bps | DOGE | 15m | ok | 17 | -585.14 | 0.281 | 17.6 | 7.15 |
| Baseline 125bps | DOGE | 5m | ok | 12 | 361.52 | 1.743 | 58.3 | 2.09 |
| Baseline 125bps | ETH | 15m | ok | 22 | -172.51 | 0.802 | 40.9 | 4.52 |
| Baseline 125bps | ETH | 5m | ok | 13 | 459.95 | 1.648 | 61.5 | 4.25 |
| Baseline 125bps | HYPE | 15m | ok | 24 | -409.30 | 0.671 | 45.8 | 5.21 |
| Baseline 125bps | HYPE | 5m | ok | 23 | 707.44 | 1.647 | 56.5 | 4.29 |
| Baseline 125bps | LINK | 15m | ok | 7 | 80.06 | 1.491 | 71.4 | 1.08 |
| Baseline 125bps | LINK | 5m | ok | 7 | 328.38 | 1.973 | 71.4 | 2.16 |
| Baseline 125bps | LTC | 15m | ok | 12 | 252.52 | 1.795 | 58.3 | 1.57 |
| Baseline 125bps | LTC | 5m | ok | 2 | -106.90 | 0.000 | 0.0 | 1.07 |
| Baseline 125bps | PYTH | 15m | ok | 16 | 238.24 | 1.732 | 62.5 | 1.11 |
| Baseline 125bps | PYTH | 5m | ok | 7 | 548.57 | 3.233 | 85.7 | 2.42 |
| Baseline 125bps | RENDER | 15m | ok | 25 | 251.77 | 1.364 | 60.0 | 2.07 |
| Baseline 125bps | RENDER | 5m | ok | 17 | -326.88 | 0.701 | 41.2 | 7.41 |
| Baseline 125bps | SEI | 15m | ok | 10 | 335.81 | 2.805 | 60.0 | 0.53 |
| Baseline 125bps | SEI | 5m | ok | 9 | 286.99 | 2.744 | 77.8 | 1.06 |
| Baseline 125bps | SOL | 15m | ok | 22 | -606.34 | 0.443 | 36.4 | 6.52 |
| Baseline 125bps | SOL | 5m | ok | 7 | 52.07 | 1.165 | 42.9 | 3.15 |
| Baseline 125bps | XRP | 15m | ok | 17 | -81.23 | 0.884 | 58.8 | 4.97 |
| Baseline 125bps | XRP | 5m | ok | 6 | 447.17 | 3.657 | 66.7 | 1.08 |
| Baseline 125bps | ZEC | 15m | ok | 26 | 708.68 | 2.095 | 65.4 | 1.13 |
| Baseline 125bps | ZEC | 5m | ok | 31 | 1632.50 | 3.088 | 77.4 | 2.16 |
| Quality Score 3 | ADA | 15m | ok | 22 | 437.36 | 1.876 | 68.2 | 1.62 |
| Quality Score 3 | ADA | 5m | ok | 9 | 261.47 | 1.946 | 66.7 | 1.08 |
| Quality Score 3 | AERO | 15m | ok | 22 | -184.29 | 0.795 | 54.5 | 5.82 |
| Quality Score 3 | AERO | 5m | ok | 17 | 120.12 | 1.130 | 58.8 | 4.32 |
| Quality Score 3 | ARB | 15m | ok | 22 | 216.27 | 1.361 | 63.6 | 2.12 |
| Quality Score 3 | ARB | 5m | ok | 10 | 671.62 | 4.820 | 80.0 | 1.11 |
| Quality Score 3 | BNB | 15m | ok | 12 | -494.20 | 0.273 | 25.0 | 5.24 |
| Quality Score 3 | BNB | 5m | ok | 2 | -15.49 | 0.855 | 50.0 | 1.07 |
| Quality Score 3 | BTC | 15m | no_trade_data | 0 | 0.00 | 0.000 | n/a | 0.00 |
| Quality Score 3 | BTC | 5m | ok | 4 | 32.84 | 1.308 | 50.0 | 0.53 |
| Quality Score 3 | DOGE | 15m | ok | 17 | -585.14 | 0.281 | 17.6 | 7.15 |
| Quality Score 3 | DOGE | 5m | ok | 11 | 313.27 | 1.644 | 54.5 | 2.09 |
| Quality Score 3 | ETH | 15m | ok | 21 | -147.14 | 0.826 | 42.9 | 4.28 |
| Quality Score 3 | ETH | 5m | ok | 13 | 459.95 | 1.648 | 61.5 | 4.25 |
| Quality Score 3 | HYPE | 15m | ok | 23 | -453.40 | 0.636 | 43.5 | 5.27 |
| Quality Score 3 | HYPE | 5m | ok | 23 | 629.37 | 1.537 | 56.5 | 4.29 |
| Quality Score 3 | LINK | 15m | ok | 7 | 80.06 | 1.491 | 71.4 | 1.08 |
| Quality Score 3 | LINK | 5m | ok | 7 | 328.38 | 1.973 | 71.4 | 2.16 |
| Quality Score 3 | LTC | 15m | ok | 11 | 308.77 | 2.175 | 63.6 | 1.05 |
| Quality Score 3 | LTC | 5m | ok | 1 | -53.10 | 0.000 | 0.0 | 0.53 |
| Quality Score 3 | PYTH | 15m | ok | 16 | 238.24 | 1.732 | 62.5 | 1.11 |
| Quality Score 3 | PYTH | 5m | ok | 8 | 545.94 | 3.199 | 75.0 | 2.42 |
| Quality Score 3 | RENDER | 15m | ok | 24 | 178.54 | 1.258 | 58.3 | 2.07 |
| Quality Score 3 | RENDER | 5m | ok | 14 | -266.57 | 0.730 | 42.9 | 7.41 |
| Quality Score 3 | SEI | 15m | ok | 9 | 363.06 | 3.286 | 66.7 | 0.53 |
| Quality Score 3 | SEI | 5m | ok | 8 | 262.74 | 2.599 | 75.0 | 1.06 |
| Quality Score 3 | SOL | 15m | ok | 22 | -606.34 | 0.443 | 36.4 | 6.52 |
| Quality Score 3 | SOL | 5m | ok | 7 | 52.07 | 1.165 | 42.9 | 3.15 |
| Quality Score 3 | XRP | 15m | ok | 17 | -81.23 | 0.884 | 58.8 | 4.97 |
| Quality Score 3 | XRP | 5m | ok | 6 | 447.17 | 3.657 | 66.7 | 1.08 |
| Quality Score 3 | ZEC | 15m | ok | 23 | 737.95 | 2.237 | 69.6 | 1.13 |
| Quality Score 3 | ZEC | 5m | ok | 31 | 1632.50 | 3.088 | 77.4 | 2.16 |
| ATR Regime Filter | ADA | 15m | ok | 22 | 437.36 | 1.876 | 68.2 | 1.62 |
| ATR Regime Filter | ADA | 5m | ok | 10 | 195.69 | 1.586 | 50.0 | 1.20 |
| ATR Regime Filter | AERO | 15m | ok | 24 | -244.01 | 0.746 | 50.0 | 6.00 |
| ATR Regime Filter | AERO | 5m | ok | 19 | 143.97 | 1.156 | 57.9 | 4.32 |
| ATR Regime Filter | ARB | 15m | ok | 23 | 241.16 | 1.402 | 65.2 | 2.12 |
| ATR Regime Filter | ARB | 5m | ok | 10 | 671.62 | 4.820 | 80.0 | 1.11 |
| ATR Regime Filter | BNB | 15m | ok | 13 | -471.18 | 0.309 | 30.8 | 5.24 |
| ATR Regime Filter | BNB | 5m | ok | 2 | -15.49 | 0.855 | 50.0 | 1.07 |
| ATR Regime Filter | BTC | 15m | ok | 15 | -173.79 | 0.728 | 46.7 | 2.80 |
| ATR Regime Filter | BTC | 5m | ok | 4 | 32.84 | 1.308 | 50.0 | 0.53 |
| ATR Regime Filter | DOGE | 15m | ok | 17 | -585.14 | 0.281 | 17.6 | 7.15 |
| ATR Regime Filter | DOGE | 5m | ok | 12 | 361.52 | 1.743 | 58.3 | 2.09 |
| ATR Regime Filter | ETH | 15m | ok | 26 | -254.90 | 0.746 | 46.2 | 5.26 |
| ATR Regime Filter | ETH | 5m | ok | 13 | 459.95 | 1.648 | 61.5 | 4.25 |
| ATR Regime Filter | HYPE | 15m | ok | 24 | -409.30 | 0.671 | 45.8 | 5.21 |
| ATR Regime Filter | HYPE | 5m | ok | 23 | 629.37 | 1.537 | 56.5 | 4.29 |
| ATR Regime Filter | LINK | 15m | ok | 7 | 80.06 | 1.491 | 71.4 | 1.08 |
| ATR Regime Filter | LINK | 5m | ok | 7 | 328.38 | 1.973 | 71.4 | 2.16 |
| ATR Regime Filter | LTC | 15m | ok | 12 | 252.52 | 1.795 | 58.3 | 1.57 |
| ATR Regime Filter | LTC | 5m | ok | 2 | -106.90 | 0.000 | 0.0 | 1.07 |
| ATR Regime Filter | PYTH | 15m | ok | 16 | 238.24 | 1.732 | 62.5 | 1.11 |
| ATR Regime Filter | PYTH | 5m | ok | 8 | 433.53 | 2.416 | 75.0 | 2.42 |
| ATR Regime Filter | RENDER | 15m | ok | 23 | 205.29 | 1.321 | 60.9 | 2.07 |
| ATR Regime Filter | RENDER | 5m | ok | 17 | -326.88 | 0.701 | 41.2 | 7.41 |
| ATR Regime Filter | SEI | 15m | ok | 10 | 335.81 | 2.805 | 60.0 | 0.53 |
| ATR Regime Filter | SEI | 5m | ok | 9 | 286.99 | 2.744 | 77.8 | 1.06 |
| ATR Regime Filter | SOL | 15m | ok | 22 | -606.34 | 0.443 | 36.4 | 6.52 |
| ATR Regime Filter | SOL | 5m | ok | 7 | 52.07 | 1.165 | 42.9 | 3.15 |
| ATR Regime Filter | XRP | 15m | ok | 17 | -81.23 | 0.884 | 58.8 | 4.97 |
| ATR Regime Filter | XRP | 5m | ok | 6 | 447.17 | 3.657 | 66.7 | 1.08 |
| ATR Regime Filter | ZEC | 15m | ok | 25 | 604.77 | 1.944 | 64.0 | 1.13 |
| ATR Regime Filter | ZEC | 5m | ok | 31 | 1527.06 | 2.958 | 77.4 | 2.16 |
| Close Confirmed Stop | ADA | 15m | ok | 22 | 112.42 | 1.138 | 68.2 | 4.07 |
| Close Confirmed Stop | ADA | 5m | ok | 10 | 146.86 | 1.384 | 50.0 | 1.68 |
| Close Confirmed Stop | AERO | 15m | ok | 24 | -402.19 | 0.638 | 50.0 | 7.37 |
| Close Confirmed Stop | AERO | 5m | ok | 19 | 63.25 | 1.063 | 57.9 | 4.82 |
| Close Confirmed Stop | ARB | 15m | ok | 22 | 192.40 | 1.297 | 68.2 | 2.40 |
| Close Confirmed Stop | ARB | 5m | ok | 10 | 664.45 | 4.631 | 80.0 | 1.11 |
| Close Confirmed Stop | BNB | 15m | ok | 13 | -568.64 | 0.270 | 30.8 | 6.21 |
| Close Confirmed Stop | BNB | 5m | ok | 2 | -189.42 | 0.321 | 50.0 | 2.79 |
| Close Confirmed Stop | BTC | 15m | ok | 15 | -450.56 | 0.531 | 53.3 | 6.34 |
| Close Confirmed Stop | BTC | 5m | ok | 4 | 14.70 | 1.118 | 50.0 | 0.65 |
| Close Confirmed Stop | DOGE | 15m | ok | 17 | -355.66 | 0.508 | 35.3 | 6.18 |
| Close Confirmed Stop | DOGE | 5m | ok | 12 | 326.63 | 1.629 | 58.3 | 2.18 |
| Close Confirmed Stop | ETH | 15m | ok | 20 | -244.75 | 0.726 | 40.0 | 5.09 |
| Close Confirmed Stop | ETH | 5m | ok | 13 | 610.42 | 1.913 | 69.2 | 4.50 |
| Close Confirmed Stop | HYPE | 15m | ok | 23 | -171.28 | 0.845 | 52.2 | 3.26 |
| Close Confirmed Stop | HYPE | 5m | ok | 23 | 499.20 | 1.388 | 56.5 | 4.96 |
| Close Confirmed Stop | LINK | 15m | ok | 7 | 285.03 | 6.195 | 85.7 | 0.54 |
| Close Confirmed Stop | LINK | 5m | ok | 7 | 286.51 | 1.756 | 71.4 | 2.48 |
| Close Confirmed Stop | LTC | 15m | ok | 12 | 245.64 | 1.758 | 58.3 | 1.57 |
| Close Confirmed Stop | LTC | 5m | ok | 2 | -110.15 | 0.000 | 0.0 | 1.10 |
| Close Confirmed Stop | PYTH | 15m | ok | 16 | 202.97 | 1.564 | 62.5 | 1.29 |
| Close Confirmed Stop | PYTH | 5m | ok | 8 | 433.53 | 2.416 | 75.0 | 2.42 |
| Close Confirmed Stop | RENDER | 15m | ok | 25 | 91.05 | 1.114 | 60.0 | 2.65 |
| Close Confirmed Stop | RENDER | 5m | ok | 17 | -316.00 | 0.733 | 47.1 | 7.70 |
| Close Confirmed Stop | SEI | 15m | ok | 8 | 414.33 | 4.760 | 75.0 | 0.56 |
| Close Confirmed Stop | SEI | 5m | ok | 9 | 271.48 | 2.508 | 77.8 | 1.17 |
| Close Confirmed Stop | SOL | 15m | ok | 22 | -706.76 | 0.429 | 40.9 | 8.34 |
| Close Confirmed Stop | SOL | 5m | ok | 7 | -25.25 | 0.935 | 42.9 | 3.90 |
| Close Confirmed Stop | XRP | 15m | ok | 17 | -83.72 | 0.888 | 64.7 | 4.99 |
| Close Confirmed Stop | XRP | 5m | ok | 6 | 427.69 | 3.280 | 66.7 | 1.21 |
| Close Confirmed Stop | ZEC | 15m | ok | 26 | 638.79 | 1.899 | 65.4 | 1.19 |
| Close Confirmed Stop | ZEC | 5m | ok | 31 | 1806.58 | 3.500 | 80.6 | 2.22 |

## Window Robustness
| Variant | Asset | Window | Trades | P&L | PF | Win % | DD % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Baseline 125bps | ADA | early | 15 | 499.61 | 2.838 | 73.3 | 1.05 |
| Baseline 125bps | ADA | latest | 8 | -104.78 | 0.768 | 37.5 | 1.78 |
| Baseline 125bps | ADA | middle | 8 | 238.99 | 3.205 | 75.0 | 0.53 |
| Baseline 125bps | AERO | early | 12 | 359.73 | 2.671 | 75.0 | 1.07 |
| Baseline 125bps | AERO | latest | 20 | -428.45 | 0.599 | 40.0 | 6.66 |
| Baseline 125bps | AERO | middle | 11 | -28.32 | 0.952 | 54.5 | 4.46 |
| Baseline 125bps | ARB | early | 14 | 320.00 | 2.508 | 71.4 | 1.05 |
| Baseline 125bps | ARB | latest | 14 | 51.87 | 1.076 | 57.1 | 2.42 |
| Baseline 125bps | ARB | middle | 5 | 421.60 | n/a | 100.0 | 0.00 |
| Baseline 125bps | BNB | early | 8 | 34.53 | 1.129 | 62.5 | 1.12 |
| Baseline 125bps | BNB | latest | 5 | -365.32 | 0.000 | 0.0 | 3.65 |
| Baseline 125bps | BNB | middle | 2 | -155.88 | 0.000 | 0.0 | 1.56 |
| Baseline 125bps | BTC | early | 6 | -23.41 | 0.889 | 50.0 | 2.10 |
| Baseline 125bps | BTC | latest | 4 | -174.82 | 0.343 | 25.0 | 1.75 |
| Baseline 125bps | BTC | middle | 9 | 57.28 | 1.214 | 55.6 | 1.59 |
| Baseline 125bps | DOGE | early | 10 | -97.94 | 0.767 | 30.0 | 4.14 |
| Baseline 125bps | DOGE | latest | 6 | -211.57 | 0.409 | 33.3 | 3.58 |
| Baseline 125bps | DOGE | middle | 13 | 85.89 | 1.164 | 38.5 | 2.53 |
| Baseline 125bps | ETH | early | 17 | -68.41 | 0.883 | 47.1 | 2.99 |
| Baseline 125bps | ETH | latest | 6 | 387.76 | 2.451 | 66.7 | 2.12 |
| Baseline 125bps | ETH | middle | 12 | -31.91 | 0.956 | 41.7 | 4.26 |
| Baseline 125bps | HYPE | early | 16 | -456.45 | 0.451 | 37.5 | 5.30 |
| Baseline 125bps | HYPE | latest | 20 | 111.36 | 1.102 | 55.0 | 5.38 |
| Baseline 125bps | HYPE | middle | 11 | 643.23 | 2.544 | 63.6 | 2.04 |
| Baseline 125bps | LINK | early | 5 | 140.99 | 3.664 | 80.0 | 0.52 |
| Baseline 125bps | LINK | latest | 8 | 218.34 | 1.488 | 62.5 | 3.20 |
| Baseline 125bps | LINK | middle | 1 | 49.11 | n/a | 100.0 | 0.00 |
| Baseline 125bps | LTC | early | 5 | 37.72 | 1.355 | 60.0 | 1.05 |
| Baseline 125bps | LTC | latest | 6 | -29.57 | 0.889 | 33.3 | 2.66 |
| Baseline 125bps | LTC | middle | 3 | 137.47 | 3.648 | 66.7 | 0.51 |
| Baseline 125bps | PYTH | early | 9 | 306.13 | 3.871 | 77.8 | 0.53 |
| Baseline 125bps | PYTH | latest | 8 | 786.05 | 15.143 | 87.5 | 0.55 |
| Baseline 125bps | PYTH | middle | 6 | -305.37 | 0.253 | 33.3 | 3.55 |
| Baseline 125bps | RENDER | early | 20 | -728.72 | 0.397 | 40.0 | 8.53 |
| Baseline 125bps | RENDER | latest | 15 | 250.39 | 1.480 | 53.3 | 2.10 |
| Baseline 125bps | RENDER | middle | 7 | 403.22 | 8.544 | 85.7 | 0.53 |
| Baseline 125bps | SEI | early | 5 | 125.34 | 2.169 | 60.0 | 0.53 |
| Baseline 125bps | SEI | latest | 7 | 270.59 | 2.964 | 71.4 | 1.32 |
| Baseline 125bps | SEI | middle | 7 | 226.87 | 3.148 | 71.4 | 0.53 |
| Baseline 125bps | SOL | early | 11 | -471.45 | 0.253 | 27.3 | 5.18 |
| Baseline 125bps | SOL | latest | 9 | 94.59 | 1.231 | 55.6 | 2.04 |
| Baseline 125bps | SOL | middle | 9 | -177.41 | 0.510 | 33.3 | 1.77 |
| Baseline 125bps | XRP | early | 11 | 431.88 | 2.323 | 63.6 | 2.66 |
| Baseline 125bps | XRP | latest | 7 | -202.79 | 0.584 | 42.9 | 3.91 |
| Baseline 125bps | XRP | middle | 5 | 136.85 | 3.652 | 80.0 | 0.52 |
| Baseline 125bps | ZEC | early | 15 | 708.36 | 6.334 | 80.0 | 0.52 |
| Baseline 125bps | ZEC | latest | 26 | 773.16 | 1.736 | 65.4 | 3.35 |
| Baseline 125bps | ZEC | middle | 16 | 859.66 | 4.498 | 75.0 | 1.10 |
| Quality Score 3 | ADA | early | 15 | 499.61 | 2.838 | 73.3 | 1.05 |
| Quality Score 3 | ADA | latest | 8 | -39.77 | 0.899 | 50.0 | 1.78 |
| Quality Score 3 | ADA | middle | 8 | 238.99 | 3.205 | 75.0 | 0.53 |
| Quality Score 3 | AERO | early | 12 | 359.73 | 2.671 | 75.0 | 1.07 |
| Quality Score 3 | AERO | latest | 16 | -395.58 | 0.609 | 43.8 | 6.66 |
| Quality Score 3 | AERO | middle | 11 | -28.32 | 0.952 | 54.5 | 4.46 |
| Quality Score 3 | ARB | early | 14 | 320.00 | 2.508 | 71.4 | 1.05 |
| Quality Score 3 | ARB | latest | 13 | 146.29 | 1.260 | 53.8 | 1.65 |
| Quality Score 3 | ARB | middle | 5 | 421.60 | n/a | 100.0 | 0.00 |
| Quality Score 3 | BNB | early | 7 | 10.29 | 1.039 | 57.1 | 1.12 |
| Quality Score 3 | BNB | latest | 5 | -364.45 | 0.000 | 0.0 | 3.64 |
| Quality Score 3 | BNB | middle | 2 | -155.53 | 0.000 | 0.0 | 1.56 |
| Quality Score 3 | BTC | early | 3 | 86.34 | 2.626 | 66.7 | 0.53 |
| Quality Score 3 | BTC | middle | 1 | -53.50 | 0.000 | 0.0 | 0.53 |
| Quality Score 3 | DOGE | early | 10 | -97.94 | 0.767 | 30.0 | 4.14 |
| Quality Score 3 | DOGE | latest | 5 | -259.82 | 0.274 | 20.0 | 3.58 |
| Quality Score 3 | DOGE | middle | 13 | 85.89 | 1.164 | 38.5 | 2.53 |
| Quality Score 3 | ETH | early | 17 | -68.41 | 0.883 | 47.1 | 2.99 |
| Quality Score 3 | ETH | latest | 5 | 203.44 | 1.759 | 60.0 | 2.13 |
| Quality Score 3 | ETH | middle | 12 | 177.78 | 1.253 | 50.0 | 4.25 |
| Quality Score 3 | HYPE | early | 16 | -456.45 | 0.451 | 37.5 | 5.30 |
| Quality Score 3 | HYPE | latest | 18 | -108.54 | 0.907 | 50.0 | 6.79 |
| Quality Score 3 | HYPE | middle | 12 | 740.96 | 2.778 | 66.7 | 2.04 |
| Quality Score 3 | LINK | early | 5 | 140.99 | 3.664 | 80.0 | 0.52 |
| Quality Score 3 | LINK | latest | 8 | 218.34 | 1.488 | 62.5 | 3.20 |
| Quality Score 3 | LINK | middle | 1 | 49.11 | n/a | 100.0 | 0.00 |
| Quality Score 3 | LTC | early | 5 | 37.72 | 1.355 | 60.0 | 1.05 |
| Quality Score 3 | LTC | latest | 4 | 80.48 | 1.510 | 50.0 | 1.58 |
| Quality Score 3 | LTC | middle | 3 | 137.47 | 3.648 | 66.7 | 0.51 |
| Quality Score 3 | PYTH | early | 9 | 306.13 | 3.871 | 77.8 | 0.53 |
| Quality Score 3 | PYTH | latest | 9 | 783.42 | 14.459 | 77.8 | 0.55 |
| Quality Score 3 | PYTH | middle | 6 | -305.37 | 0.253 | 33.3 | 3.55 |
| Quality Score 3 | RENDER | early | 20 | -728.72 | 0.397 | 40.0 | 8.53 |
| Quality Score 3 | RENDER | latest | 11 | 237.47 | 1.569 | 54.5 | 2.10 |
| Quality Score 3 | RENDER | middle | 7 | 403.22 | 8.544 | 85.7 | 0.53 |
| Quality Score 3 | SEI | early | 5 | 125.34 | 2.169 | 60.0 | 0.53 |
| Quality Score 3 | SEI | latest | 5 | 273.59 | 3.481 | 80.0 | 1.06 |
| Quality Score 3 | SEI | middle | 7 | 226.87 | 3.148 | 71.4 | 0.53 |
| Quality Score 3 | SOL | early | 11 | -471.45 | 0.253 | 27.3 | 5.18 |
| Quality Score 3 | SOL | latest | 9 | 94.59 | 1.231 | 55.6 | 2.04 |
| Quality Score 3 | SOL | middle | 9 | -177.41 | 0.510 | 33.3 | 1.77 |
| Quality Score 3 | XRP | early | 11 | 431.88 | 2.323 | 63.6 | 2.66 |
| Quality Score 3 | XRP | latest | 7 | -202.79 | 0.584 | 42.9 | 3.91 |
| Quality Score 3 | XRP | middle | 5 | 136.85 | 3.652 | 80.0 | 0.52 |
| Quality Score 3 | ZEC | early | 13 | 710.04 | 7.636 | 84.6 | 0.52 |
| Quality Score 3 | ZEC | latest | 26 | 774.25 | 1.736 | 65.4 | 3.35 |
| Quality Score 3 | ZEC | middle | 15 | 886.16 | 5.030 | 80.0 | 1.10 |
| ATR Regime Filter | ADA | early | 15 | 499.61 | 2.838 | 73.3 | 1.05 |
| ATR Regime Filter | ADA | latest | 9 | -105.55 | 0.767 | 33.3 | 1.78 |
| ATR Regime Filter | ADA | middle | 8 | 238.99 | 3.205 | 75.0 | 0.53 |
| ATR Regime Filter | AERO | early | 12 | 359.73 | 2.671 | 75.0 | 1.07 |
| ATR Regime Filter | AERO | latest | 20 | -431.45 | 0.598 | 40.0 | 6.66 |
| ATR Regime Filter | AERO | middle | 11 | -28.32 | 0.952 | 54.5 | 4.46 |
| ATR Regime Filter | ARB | early | 14 | 320.00 | 2.508 | 71.4 | 1.05 |
| ATR Regime Filter | ARB | latest | 14 | 171.18 | 1.304 | 57.1 | 1.65 |
| ATR Regime Filter | ARB | middle | 5 | 421.60 | n/a | 100.0 | 0.00 |
| ATR Regime Filter | BNB | early | 8 | 34.53 | 1.129 | 62.5 | 1.12 |
| ATR Regime Filter | BNB | latest | 5 | -365.32 | 0.000 | 0.0 | 3.65 |
| ATR Regime Filter | BNB | middle | 2 | -155.88 | 0.000 | 0.0 | 1.56 |
| ATR Regime Filter | BTC | early | 6 | -23.41 | 0.889 | 50.0 | 2.10 |
| ATR Regime Filter | BTC | latest | 4 | -174.82 | 0.343 | 25.0 | 1.75 |
| ATR Regime Filter | BTC | middle | 9 | 57.28 | 1.214 | 55.6 | 1.59 |
| ATR Regime Filter | DOGE | early | 10 | -97.94 | 0.767 | 30.0 | 4.14 |
| ATR Regime Filter | DOGE | latest | 6 | -211.57 | 0.409 | 33.3 | 3.58 |
| ATR Regime Filter | DOGE | middle | 13 | 85.89 | 1.164 | 38.5 | 2.53 |
| ATR Regime Filter | ETH | early | 17 | -12.86 | 0.976 | 52.9 | 2.91 |
| ATR Regime Filter | ETH | latest | 8 | 144.68 | 1.389 | 62.5 | 2.12 |
| ATR Regime Filter | ETH | middle | 14 | 73.23 | 1.091 | 42.9 | 4.29 |
| ATR Regime Filter | HYPE | early | 16 | -456.45 | 0.451 | 37.5 | 5.30 |
| ATR Regime Filter | HYPE | latest | 19 | -64.44 | 0.945 | 52.6 | 6.35 |
| ATR Regime Filter | HYPE | middle | 12 | 740.96 | 2.778 | 66.7 | 2.04 |
| ATR Regime Filter | LINK | early | 5 | 140.99 | 3.664 | 80.0 | 0.52 |
| ATR Regime Filter | LINK | latest | 8 | 218.34 | 1.488 | 62.5 | 3.20 |
| ATR Regime Filter | LINK | middle | 1 | 49.11 | n/a | 100.0 | 0.00 |
| ATR Regime Filter | LTC | early | 5 | 37.72 | 1.355 | 60.0 | 1.05 |
| ATR Regime Filter | LTC | latest | 6 | -29.57 | 0.889 | 33.3 | 2.66 |
| ATR Regime Filter | LTC | middle | 3 | 137.47 | 3.648 | 66.7 | 0.51 |
| ATR Regime Filter | PYTH | early | 9 | 306.13 | 3.871 | 77.8 | 0.53 |
| ATR Regime Filter | PYTH | latest | 9 | 671.01 | 6.782 | 77.8 | 0.56 |
| ATR Regime Filter | PYTH | middle | 6 | -305.37 | 0.253 | 33.3 | 3.55 |
| ATR Regime Filter | RENDER | early | 18 | -726.35 | 0.372 | 38.9 | 8.53 |
| ATR Regime Filter | RENDER | latest | 15 | 201.50 | 1.386 | 53.3 | 2.10 |
| ATR Regime Filter | RENDER | middle | 7 | 403.26 | 8.543 | 85.7 | 0.53 |
| ATR Regime Filter | SEI | early | 5 | 125.34 | 2.169 | 60.0 | 0.53 |
| ATR Regime Filter | SEI | latest | 7 | 270.59 | 2.964 | 71.4 | 1.32 |
| ATR Regime Filter | SEI | middle | 7 | 226.87 | 3.148 | 71.4 | 0.53 |
| ATR Regime Filter | SOL | early | 11 | -471.45 | 0.253 | 27.3 | 5.18 |
| ATR Regime Filter | SOL | latest | 9 | 94.59 | 1.231 | 55.6 | 2.04 |
| ATR Regime Filter | SOL | middle | 9 | -177.41 | 0.510 | 33.3 | 1.77 |
| ATR Regime Filter | XRP | early | 11 | 431.88 | 2.323 | 63.6 | 2.66 |
| ATR Regime Filter | XRP | latest | 7 | -202.79 | 0.584 | 42.9 | 3.91 |
| ATR Regime Filter | XRP | middle | 5 | 136.85 | 3.652 | 80.0 | 0.52 |
| ATR Regime Filter | ZEC | early | 15 | 659.71 | 5.977 | 80.0 | 0.52 |
| ATR Regime Filter | ZEC | latest | 26 | 663.72 | 1.636 | 65.4 | 3.34 |
| ATR Regime Filter | ZEC | middle | 15 | 808.40 | 4.307 | 73.3 | 1.10 |
| Close Confirmed Stop | ADA | early | 15 | 444.06 | 2.361 | 73.3 | 1.20 |
| Close Confirmed Stop | ADA | latest | 9 | -419.31 | 0.449 | 33.3 | 4.31 |
| Close Confirmed Stop | ADA | middle | 8 | 234.53 | 3.113 | 75.0 | 0.55 |
| Close Confirmed Stop | AERO | early | 12 | 324.68 | 2.298 | 75.0 | 1.35 |
| Close Confirmed Stop | AERO | latest | 20 | -570.52 | 0.526 | 40.0 | 7.81 |
| Close Confirmed Stop | AERO | middle | 11 | -93.10 | 0.858 | 54.5 | 5.08 |
| Close Confirmed Stop | ARB | early | 13 | 339.75 | 2.768 | 76.9 | 1.28 |
| Close Confirmed Stop | ARB | latest | 14 | 95.24 | 1.149 | 57.1 | 2.05 |
| Close Confirmed Stop | ARB | middle | 5 | 421.86 | n/a | 100.0 | 0.00 |
| Close Confirmed Stop | BNB | early | 8 | -139.89 | 0.682 | 62.5 | 2.84 |
| Close Confirmed Stop | BNB | latest | 5 | -460.94 | 0.000 | 0.0 | 4.61 |
| Close Confirmed Stop | BNB | middle | 2 | -157.23 | 0.000 | 0.0 | 1.57 |
| Close Confirmed Stop | BTC | early | 6 | -50.96 | 0.786 | 50.0 | 2.37 |
| Close Confirmed Stop | BTC | latest | 4 | -436.48 | 0.169 | 25.0 | 4.36 |
| Close Confirmed Stop | BTC | middle | 9 | 51.58 | 1.160 | 66.7 | 2.61 |
| Close Confirmed Stop | DOGE | early | 10 | 43.41 | 1.116 | 50.0 | 3.67 |
| Close Confirmed Stop | DOGE | latest | 6 | -95.63 | 0.660 | 50.0 | 2.41 |
| Close Confirmed Stop | DOGE | middle | 13 | 23.19 | 1.040 | 38.5 | 2.88 |
| Close Confirmed Stop | ETH | early | 15 | 59.56 | 1.119 | 53.3 | 3.43 |
| Close Confirmed Stop | ETH | latest | 5 | 194.06 | 1.693 | 60.0 | 2.25 |
| Close Confirmed Stop | ETH | middle | 13 | 112.05 | 1.144 | 46.2 | 4.59 |
| Close Confirmed Stop | HYPE | early | 16 | -603.06 | 0.382 | 37.5 | 6.49 |
| Close Confirmed Stop | HYPE | latest | 18 | 217.44 | 1.221 | 61.1 | 5.97 |
| Close Confirmed Stop | HYPE | middle | 12 | 713.54 | 2.638 | 66.7 | 2.18 |
| Close Confirmed Stop | LINK | early | 5 | 139.03 | 3.534 | 80.0 | 0.54 |
| Close Confirmed Stop | LINK | latest | 8 | 334.30 | 1.882 | 75.0 | 2.47 |
| Close Confirmed Stop | LINK | middle | 1 | 98.21 | n/a | 100.0 | 0.00 |
| Close Confirmed Stop | LTC | early | 5 | 32.41 | 1.291 | 60.0 | 1.10 |
| Close Confirmed Stop | LTC | latest | 6 | -33.32 | 0.877 | 33.3 | 2.70 |
| Close Confirmed Stop | LTC | middle | 3 | 136.40 | 3.579 | 66.7 | 0.52 |
| Close Confirmed Stop | PYTH | early | 9 | 293.12 | 3.455 | 77.8 | 0.65 |
| Close Confirmed Stop | PYTH | latest | 9 | 666.93 | 6.583 | 77.8 | 0.58 |
| Close Confirmed Stop | PYTH | middle | 6 | -323.55 | 0.242 | 33.3 | 3.73 |
| Close Confirmed Stop | RENDER | early | 20 | -735.73 | 0.439 | 45.0 | 8.42 |
| Close Confirmed Stop | RENDER | latest | 15 | 113.49 | 1.186 | 53.3 | 2.32 |
| Close Confirmed Stop | RENDER | middle | 7 | 397.29 | 7.656 | 85.7 | 0.59 |
| Close Confirmed Stop | SEI | early | 4 | 175.18 | 4.026 | 75.0 | 0.57 |
| Close Confirmed Stop | SEI | latest | 6 | 287.64 | 3.356 | 83.3 | 1.17 |
| Close Confirmed Stop | SEI | middle | 7 | 222.99 | 3.024 | 71.4 | 0.57 |
| Close Confirmed Stop | SOL | early | 11 | -462.02 | 0.311 | 36.4 | 5.92 |
| Close Confirmed Stop | SOL | latest | 9 | -41.70 | 0.923 | 55.6 | 2.69 |
| Close Confirmed Stop | SOL | middle | 9 | -228.29 | 0.448 | 33.3 | 2.28 |
| Close Confirmed Stop | XRP | early | 11 | 403.75 | 2.139 | 63.6 | 2.88 |
| Close Confirmed Stop | XRP | latest | 7 | -297.82 | 0.489 | 42.9 | 4.86 |
| Close Confirmed Stop | XRP | middle | 5 | 238.04 | n/a | 100.0 | 0.00 |
| Close Confirmed Stop | ZEC | early | 16 | 727.33 | 5.457 | 81.3 | 0.67 |
| Close Confirmed Stop | ZEC | latest | 26 | 961.60 | 1.987 | 69.2 | 3.40 |
| Close Confirmed Stop | ZEC | middle | 15 | 756.44 | 3.561 | 73.3 | 1.22 |
