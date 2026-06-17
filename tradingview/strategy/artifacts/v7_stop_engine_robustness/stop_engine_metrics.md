# V7 Stop Engine Robustness Metrics

Generated from 36 selected strategy exports. Expected slots: 36. Missing slots: 0.

## Coverage
| Missing | Rejected report candidates | Invalid full-close rows | Parent/report mismatches |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |

## Basket Backtest Summary
| System | Stop | Rows | Trades | Total P&L | Closed Net | PF | Win % | Max Row DD % | Positive Rows | NED Rows |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Stop Engine Current | Sweep Wick | 6 | 176 | 789.15 | 789.15 | 1.082 | 57.4 | 12.19 | 3 | 0 |
| Stop Floor 75bps | Sweep Wick | 6 | 155 | 914.34 | 914.34 | 1.111 | 56.8 | 10.75 | 3 | 0 |
| Stop Floor 100bps | Sweep Wick | 6 | 138 | 1798.94 | 1798.94 | 1.300 | 59.4 | 4.91 | 4 | 0 |
| Stop Floor 125bps | Sweep Wick | 6 | 114 | 1803.79 | 1803.79 | 1.428 | 57.9 | 4.52 | 4 | 0 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | 6 | 144 | -312.35 | -312.35 | 0.959 | 54.2 | 10.56 | 3 | 0 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | 6 | 132 | 1461.23 | 1461.23 | 1.220 | 61.4 | 8.52 | 4 | 0 |

## Basket Telemetry
| System | Stop | Parents | TP1 First % | Stop First % | CloseStop % | MaxHold % | Avg MFE R | Avg MAE R | Avg Risk bps | Avg Min Floor bps | Avg Buffer bps | Avg Range/ATR | Avg Stop/ATR | Avg TP1 R | Avg Alert Age | Avg Strength Slope | Long | Short |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Stop Engine Current | Sweep Wick | 176 | 56.8 | 42.6 | 0.0 | 0.0 | 0.72 | -0.70 | 157.7 | 15.0 | 4.0 | 2.22 | 3.96 | 1.00 | 1.8 | 0.023 | 95 | 81 |
| Stop Floor 75bps | Sweep Wick | 155 | 56.1 | 43.2 | 0.0 | 0.0 | 0.73 | -0.69 | 181.6 | 75.0 | 4.0 | 2.23 | 4.10 | 1.00 | 1.8 | 0.047 | 82 | 73 |
| Stop Floor 100bps | Sweep Wick | 138 | 59.4 | 40.6 | 0.0 | 0.0 | 0.74 | -0.68 | 199.3 | 100.0 | 4.0 | 2.31 | 4.14 | 1.00 | 1.7 | -0.117 | 69 | 69 |
| Stop Floor 125bps | Sweep Wick | 114 | 57.9 | 42.1 | 0.0 | 0.0 | 0.73 | -0.68 | 217.8 | 125.0 | 4.0 | 2.26 | 4.26 | 1.00 | 2.3 | -0.047 | 57 | 57 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | 144 | 53.5 | 45.8 | 0.0 | 0.0 | 0.73 | -0.69 | 204.8 | 100.0 | 20.0 | 2.23 | 4.49 | 1.00 | 1.2 | -0.035 | 75 | 69 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | 132 | 61.4 | 37.9 | 37.9 | 0.8 | 0.76 | -0.82 | 200.3 | 100.0 | 4.0 | 2.29 | 4.17 | 1.00 | 1.9 | -0.073 | 68 | 64 |

## Symbol/Timeframe Backtest
| System | Stop | Symbol | TF | Trades | Total P&L | PF | Win % | DD % | NED | Source |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| Stop Engine Current | Sweep Wick | BINANCE:BTCUSDT | 15m | 18 | -183.23 | 0.791 | 50.0 | 4.98 | no | tradingview/automation/v7-stop-engine-current/2026-05-28T12-41-14-114Z-pine-text-matrix/BINANCE_BTCUSDT/15m/BINANCE_BTCUSDT_15m_strategy.csv |
| Stop Engine Current | Sweep Wick | BINANCE:BTCUSDT | 5m | 25 | -556.31 | 0.700 | 52.0 | 12.19 | no | tradingview/automation/v7-stop-engine-current/2026-05-28T12-41-14-114Z-pine-text-matrix/BINANCE_BTCUSDT/5m/BINANCE_BTCUSDT_5m_strategy.csv |
| Stop Engine Current | Sweep Wick | BINANCE:ETHUSDT | 15m | 33 | 706.33 | 1.553 | 57.6 | 2.75 | no | tradingview/automation/v7-stop-engine-current/2026-05-28T12-41-14-114Z-pine-text-matrix/BINANCE_ETHUSDT/15m/BINANCE_ETHUSDT_15m_strategy.csv |
| Stop Engine Current | Sweep Wick | BINANCE:ETHUSDT | 5m | 30 | -771.47 | 0.702 | 46.7 | 10.99 | no | tradingview/automation/v7-stop-engine-current/2026-05-28T12-41-14-114Z-pine-text-matrix/BINANCE_ETHUSDT/5m/BINANCE_ETHUSDT_5m_strategy.csv |
| Stop Engine Current | Sweep Wick | BINANCE:ZECUSDT | 15m | 26 | 708.68 | 2.095 | 65.4 | 1.13 | no | tradingview/automation/v7-stop-engine-current/2026-05-28T12-41-14-114Z-pine-text-matrix/BINANCE_ZECUSDT/15m/BINANCE_ZECUSDT_15m_strategy.csv |
| Stop Engine Current | Sweep Wick | BINANCE:ZECUSDT | 5m | 44 | 885.15 | 1.378 | 65.9 | 4.79 | no | tradingview/automation/v7-stop-engine-current/2026-05-28T12-41-14-114Z-pine-text-matrix/BINANCE_ZECUSDT/5m/BINANCE_ZECUSDT_5m_strategy.csv |
| Stop Floor 75bps | Sweep Wick | BINANCE:BTCUSDT | 15m | 18 | -318.10 | 0.653 | 44.4 | 4.98 | no | tradingview/automation/v7-stop-engine-floor-75bps/2026-05-28T02-10-00-073Z-pine-text-matrix/BINANCE_BTCUSDT/15m/BINANCE_BTCUSDT_15m_strategy.csv |
| Stop Floor 75bps | Sweep Wick | BINANCE:BTCUSDT | 5m | 13 | -675.52 | 0.449 | 38.5 | 10.75 | no | tradingview/automation/v7-stop-engine-floor-75bps/2026-05-28T02-10-00-073Z-pine-text-matrix/BINANCE_BTCUSDT/5m/BINANCE_BTCUSDT_5m_strategy.csv |
| Stop Floor 75bps | Sweep Wick | BINANCE:ETHUSDT | 15m | 35 | 659.40 | 1.490 | 57.1 | 2.77 | no | tradingview/automation/v7-stop-engine-floor-75bps/2026-05-28T02-10-00-073Z-pine-text-matrix/BINANCE_ETHUSDT/15m/BINANCE_ETHUSDT_15m_strategy.csv |
| Stop Floor 75bps | Sweep Wick | BINANCE:ETHUSDT | 5m | 23 | -311.31 | 0.842 | 47.8 | 7.72 | no | tradingview/automation/v7-stop-engine-floor-75bps/2026-05-28T02-10-00-073Z-pine-text-matrix/BINANCE_ETHUSDT/5m/BINANCE_ETHUSDT_5m_strategy.csv |
| Stop Floor 75bps | Sweep Wick | BINANCE:ZECUSDT | 15m | 28 | 491.23 | 1.587 | 60.7 | 2.03 | no | tradingview/automation/v7-stop-engine-floor-75bps/2026-05-28T02-10-00-073Z-pine-text-matrix/BINANCE_ZECUSDT/15m/BINANCE_ZECUSDT_15m_strategy.csv |
| Stop Floor 75bps | Sweep Wick | BINANCE:ZECUSDT | 5m | 38 | 1068.64 | 1.543 | 71.1 | 5.73 | no | tradingview/automation/v7-stop-engine-floor-75bps/2026-05-28T02-10-00-073Z-pine-text-matrix/BINANCE_ZECUSDT/5m/BINANCE_ZECUSDT_5m_strategy.csv |
| Stop Floor 100bps | Sweep Wick | BINANCE:BTCUSDT | 15m | 18 | -309.41 | 0.660 | 44.4 | 4.91 | no | tradingview/automation/v7-stop-engine-floor-100bps/2026-05-28T02-23-59-604Z-pine-text-matrix/BINANCE_BTCUSDT/15m/BINANCE_BTCUSDT_15m_strategy.csv |
| Stop Floor 100bps | Sweep Wick | BINANCE:BTCUSDT | 5m | 6 | -153.83 | 0.599 | 50.0 | 2.38 | no | tradingview/automation/v7-stop-engine-floor-100bps/2026-05-28T02-23-59-604Z-pine-text-matrix/BINANCE_BTCUSDT/5m/BINANCE_BTCUSDT_5m_strategy.csv |
| Stop Floor 100bps | Sweep Wick | BINANCE:ETHUSDT | 15m | 35 | 29.70 | 1.022 | 54.3 | 4.22 | no | tradingview/automation/v7-stop-engine-floor-100bps/2026-05-28T02-23-59-604Z-pine-text-matrix/BINANCE_ETHUSDT/15m/BINANCE_ETHUSDT_15m_strategy.csv |
| Stop Floor 100bps | Sweep Wick | BINANCE:ETHUSDT | 5m | 17 | 337.61 | 1.305 | 58.8 | 4.63 | no | tradingview/automation/v7-stop-engine-floor-100bps/2026-05-28T02-23-59-604Z-pine-text-matrix/BINANCE_ETHUSDT/5m/BINANCE_ETHUSDT_5m_strategy.csv |
| Stop Floor 100bps | Sweep Wick | BINANCE:ZECUSDT | 15m | 28 | 491.23 | 1.587 | 60.7 | 2.03 | no | tradingview/automation/v7-stop-engine-floor-100bps/2026-05-28T02-23-59-604Z-pine-text-matrix/BINANCE_ZECUSDT/15m/BINANCE_ZECUSDT_15m_strategy.csv |
| Stop Floor 100bps | Sweep Wick | BINANCE:ZECUSDT | 5m | 34 | 1403.64 | 2.000 | 73.5 | 4.79 | no | tradingview/automation/v7-stop-engine-floor-100bps/2026-05-28T02-23-59-604Z-pine-text-matrix/BINANCE_ZECUSDT/5m/BINANCE_ZECUSDT_5m_strategy.csv |
| Stop Floor 125bps | Sweep Wick | BINANCE:BTCUSDT | 15m | 16 | -225.56 | 0.672 | 43.8 | 2.80 | no | tradingview/automation/v7-stop-engine-floor-125bps/2026-05-28T02-39-07-057Z-pine-text-matrix/BINANCE_BTCUSDT/15m/BINANCE_BTCUSDT_15m_strategy.csv |
| Stop Floor 125bps | Sweep Wick | BINANCE:BTCUSDT | 5m | 4 | 32.84 | 1.308 | 50.0 | 0.53 | no | tradingview/automation/v7-stop-engine-floor-125bps/2026-05-28T02-39-07-057Z-pine-text-matrix/BINANCE_BTCUSDT/5m/BINANCE_BTCUSDT_5m_strategy.csv |
| Stop Floor 125bps | Sweep Wick | BINANCE:ETHUSDT | 15m | 24 | -230.64 | 0.763 | 41.7 | 4.52 | no | tradingview/automation/v7-stop-engine-floor-125bps/2026-05-28T02-39-07-057Z-pine-text-matrix/BINANCE_ETHUSDT/15m/BINANCE_ETHUSDT_15m_strategy.csv |
| Stop Floor 125bps | Sweep Wick | BINANCE:ETHUSDT | 5m | 11 | 174.99 | 1.250 | 54.5 | 4.25 | no | tradingview/automation/v7-stop-engine-floor-125bps/2026-05-28T02-39-07-057Z-pine-text-matrix/BINANCE_ETHUSDT/5m/BINANCE_ETHUSDT_5m_strategy.csv |
| Stop Floor 125bps | Sweep Wick | BINANCE:ZECUSDT | 15m | 28 | 491.23 | 1.587 | 60.7 | 2.03 | no | tradingview/automation/v7-stop-engine-floor-125bps/2026-05-28T02-39-07-057Z-pine-text-matrix/BINANCE_ZECUSDT/15m/BINANCE_ZECUSDT_15m_strategy.csv |
| Stop Floor 125bps | Sweep Wick | BINANCE:ZECUSDT | 5m | 31 | 1560.93 | 2.716 | 77.4 | 2.67 | no | tradingview/automation/v7-stop-engine-floor-125bps/2026-05-28T02-39-07-057Z-pine-text-matrix/BINANCE_ZECUSDT/5m/BINANCE_ZECUSDT_5m_strategy.csv |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:BTCUSDT | 15m | 18 | -201.96 | 0.765 | 50.0 | 4.86 | no | tradingview/automation/v7-stop-engine-buffer-20bps-floor-100bps/2026-05-28T03-38-31-049Z-pine-text-matrix/BINANCE_BTCUSDT/15m/BINANCE_BTCUSDT_15m_strategy.csv |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:BTCUSDT | 5m | 10 | -977.54 | 0.192 | 30.0 | 10.56 | no | tradingview/automation/v7-stop-engine-buffer-20bps-floor-100bps/2026-05-28T03-38-31-049Z-pine-text-matrix/BINANCE_BTCUSDT/5m/BINANCE_BTCUSDT_5m_strategy.csv |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:ETHUSDT | 15m | 34 | 613.18 | 1.550 | 55.9 | 2.14 | no | tradingview/automation/v7-stop-engine-buffer-20bps-floor-100bps/2026-05-28T03-38-31-049Z-pine-text-matrix/BINANCE_ETHUSDT/15m/BINANCE_ETHUSDT_15m_strategy.csv |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:ETHUSDT | 5m | 18 | -333.56 | 0.777 | 38.9 | 4.71 | no | tradingview/automation/v7-stop-engine-buffer-20bps-floor-100bps/2026-05-28T03-38-31-049Z-pine-text-matrix/BINANCE_ETHUSDT/5m/BINANCE_ETHUSDT_5m_strategy.csv |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:ZECUSDT | 15m | 28 | 241.44 | 1.259 | 57.1 | 2.29 | no | tradingview/automation/v7-stop-engine-buffer-20bps-floor-100bps/2026-05-28T03-38-31-049Z-pine-text-matrix/BINANCE_ZECUSDT/15m/BINANCE_ZECUSDT_15m_strategy.csv |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:ZECUSDT | 5m | 36 | 346.09 | 1.165 | 66.7 | 6.63 | no | tradingview/automation/v7-stop-engine-buffer-20bps-floor-100bps/2026-05-28T03-38-31-049Z-pine-text-matrix/BINANCE_ZECUSDT/5m/BINANCE_ZECUSDT_5m_strategy.csv |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:BTCUSDT | 15m | 18 | -599.67 | 0.519 | 50.0 | 8.52 | no | tradingview/automation/v7-stop-engine-close-confirm-floor-100bps/2026-05-28T03-50-40-650Z-pine-text-matrix/BINANCE_BTCUSDT/15m/BINANCE_BTCUSDT_15m_strategy.csv |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:BTCUSDT | 5m | 6 | -338.21 | 0.404 | 50.0 | 4.09 | no | tradingview/automation/v7-stop-engine-close-confirm-floor-100bps/2026-05-28T03-50-40-650Z-pine-text-matrix/BINANCE_BTCUSDT/5m/BINANCE_BTCUSDT_5m_strategy.csv |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:ETHUSDT | 15m | 29 | 173.77 | 1.136 | 51.7 | 3.57 | no | tradingview/automation/v7-stop-engine-close-confirm-floor-100bps/2026-05-28T03-50-40-650Z-pine-text-matrix/BINANCE_ETHUSDT/15m/BINANCE_ETHUSDT_15m_strategy.csv |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:ETHUSDT | 5m | 17 | 459.35 | 1.420 | 64.7 | 4.93 | no | tradingview/automation/v7-stop-engine-close-confirm-floor-100bps/2026-05-28T03-50-40-650Z-pine-text-matrix/BINANCE_ETHUSDT/5m/BINANCE_ETHUSDT_5m_strategy.csv |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:ZECUSDT | 15m | 28 | 404.10 | 1.441 | 60.7 | 2.21 | no | tradingview/automation/v7-stop-engine-close-confirm-floor-100bps/2026-05-28T03-50-40-650Z-pine-text-matrix/BINANCE_ZECUSDT/15m/BINANCE_ZECUSDT_15m_strategy.csv |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:ZECUSDT | 5m | 34 | 1361.89 | 1.886 | 76.5 | 5.47 | no | tradingview/automation/v7-stop-engine-close-confirm-floor-100bps/2026-05-28T03-50-40-650Z-pine-text-matrix/BINANCE_ZECUSDT/5m/BINANCE_ZECUSDT_5m_strategy.csv |

## Symbol/Timeframe Telemetry
| System | Stop | Symbol | TF | Side | Parents | TP1 First % | Stop First % | CloseStop % | Avg MFE R | Avg MAE R | Avg Risk bps | Avg Min Floor bps | Avg Buffer bps | Avg MSS Age | Avg Alert Age | Avg Strength Age | Avg Strength Slope |
|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Stop Engine Current | Sweep Wick | BINANCE:BTCUSDT | 15m | all | 18 | 50.0 | 50.0 | 0.0 | 0.62 | -0.77 | 153.1 | 15.0 | 4.0 | 0.2 | 0.0 | 3.9 | -0.610 |
| Stop Engine Current | Sweep Wick | BINANCE:BTCUSDT | 5m | all | 25 | 52.0 | 48.0 | 0.0 | 0.65 | -0.71 | 78.2 | 15.0 | 4.0 | 2.5 | 0.9 | 19.1 | 0.153 |
| Stop Engine Current | Sweep Wick | BINANCE:ETHUSDT | 15m | all | 33 | 54.5 | 42.4 | 0.0 | 0.70 | -0.65 | 180.0 | 15.0 | 4.0 | 0.2 | 0.0 | 5.2 | -0.717 |
| Stop Engine Current | Sweep Wick | BINANCE:ETHUSDT | 5m | all | 30 | 46.7 | 53.3 | 0.0 | 0.65 | -0.84 | 104.7 | 15.0 | 4.0 | 4.2 | 4.8 | 17.3 | 0.117 |
| Stop Engine Current | Sweep Wick | BINANCE:ZECUSDT | 15m | all | 26 | 65.4 | 34.6 | 0.0 | 0.87 | -0.64 | 274.9 | 15.0 | 4.0 | 0.3 | 0.0 | 4.8 | -0.005 |
| Stop Engine Current | Sweep Wick | BINANCE:ZECUSDT | 5m | all | 44 | 65.9 | 34.1 | 0.0 | 0.76 | -0.64 | 155.0 | 15.0 | 4.0 | 2.8 | 4.3 | 13.4 | 0.715 |
| Stop Floor 75bps | Sweep Wick | BINANCE:BTCUSDT | 15m | all | 18 | 44.4 | 55.6 | 0.0 | 0.57 | -0.80 | 159.7 | 75.0 | 4.0 | 0.2 | 0.0 | 4.2 | -0.576 |
| Stop Floor 75bps | Sweep Wick | BINANCE:BTCUSDT | 5m | all | 13 | 38.5 | 61.5 | 0.0 | 0.59 | -0.79 | 109.9 | 75.0 | 4.0 | 3.6 | 2.0 | 15.3 | 0.420 |
| Stop Floor 75bps | Sweep Wick | BINANCE:ETHUSDT | 15m | all | 35 | 54.3 | 42.9 | 0.0 | 0.71 | -0.66 | 182.1 | 75.0 | 4.0 | 0.1 | 0.0 | 4.6 | -0.557 |
| Stop Floor 75bps | Sweep Wick | BINANCE:ETHUSDT | 5m | all | 23 | 47.8 | 52.2 | 0.0 | 0.68 | -0.83 | 121.2 | 75.0 | 4.0 | 5.5 | 7.4 | 17.0 | 0.106 |
| Stop Floor 75bps | Sweep Wick | BINANCE:ZECUSDT | 15m | all | 28 | 60.7 | 39.3 | 0.0 | 0.85 | -0.67 | 290.1 | 75.0 | 4.0 | 0.3 | 0.0 | 4.5 | 0.029 |
| Stop Floor 75bps | Sweep Wick | BINANCE:ZECUSDT | 5m | all | 38 | 71.1 | 28.9 | 0.0 | 0.81 | -0.55 | 172.6 | 75.0 | 4.0 | 2.7 | 3.6 | 12.7 | 0.748 |
| Stop Floor 100bps | Sweep Wick | BINANCE:BTCUSDT | 15m | all | 18 | 44.4 | 55.6 | 0.0 | 0.55 | -0.81 | 162.5 | 100.0 | 4.0 | 0.3 | 0.1 | 4.3 | -0.658 |
| Stop Floor 100bps | Sweep Wick | BINANCE:BTCUSDT | 5m | all | 6 | 50.0 | 50.0 | 0.0 | 0.66 | -0.70 | 134.0 | 100.0 | 4.0 | 5.0 | 0.0 | 11.3 | -0.361 |
| Stop Floor 100bps | Sweep Wick | BINANCE:ETHUSDT | 15m | all | 35 | 54.3 | 45.7 | 0.0 | 0.67 | -0.68 | 200.7 | 100.0 | 4.0 | 0.3 | 0.0 | 5.0 | -0.748 |
| Stop Floor 100bps | Sweep Wick | BINANCE:ETHUSDT | 5m | all | 17 | 58.8 | 41.2 | 0.0 | 0.74 | -0.78 | 139.6 | 100.0 | 4.0 | 6.6 | 7.9 | 18.0 | -0.033 |
| Stop Floor 100bps | Sweep Wick | BINANCE:ZECUSDT | 15m | all | 28 | 60.7 | 39.3 | 0.0 | 0.85 | -0.67 | 290.1 | 100.0 | 4.0 | 0.3 | 0.0 | 4.5 | 0.029 |
| Stop Floor 100bps | Sweep Wick | BINANCE:ZECUSDT | 5m | all | 34 | 73.5 | 26.5 | 0.0 | 0.83 | -0.54 | 184.0 | 100.0 | 4.0 | 2.2 | 4.4 | 12.1 | 0.702 |
| Stop Floor 125bps | Sweep Wick | BINANCE:BTCUSDT | 15m | all | 16 | 43.8 | 56.3 | 0.0 | 0.56 | -0.80 | 172.5 | 125.0 | 4.0 | 0.5 | 0.2 | 4.2 | -0.620 |
| Stop Floor 125bps | Sweep Wick | BINANCE:BTCUSDT | 5m | all | 4 | 50.0 | 50.0 | 0.0 | 0.65 | -0.67 | 160.8 | 125.0 | 4.0 | 3.5 | n/a | 7.3 | -0.815 |
| Stop Floor 125bps | Sweep Wick | BINANCE:ETHUSDT | 15m | all | 24 | 41.7 | 58.3 | 0.0 | 0.58 | -0.78 | 227.1 | 125.0 | 4.0 | 0.3 | 0.0 | 4.1 | -0.722 |
| Stop Floor 125bps | Sweep Wick | BINANCE:ETHUSDT | 5m | all | 11 | 54.5 | 45.5 | 0.0 | 0.69 | -0.80 | 156.8 | 125.0 | 4.0 | 7.5 | 9.4 | 19.6 | 0.201 |
| Stop Floor 125bps | Sweep Wick | BINANCE:ZECUSDT | 15m | all | 28 | 60.7 | 39.3 | 0.0 | 0.85 | -0.67 | 290.1 | 125.0 | 4.0 | 0.3 | 0.0 | 4.5 | 0.029 |
| Stop Floor 125bps | Sweep Wick | BINANCE:ZECUSDT | 5m | all | 31 | 77.4 | 22.6 | 0.0 | 0.85 | -0.53 | 197.6 | 125.0 | 4.0 | 2.5 | 5.9 | 12.9 | 0.712 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:BTCUSDT | 15m | all | 18 | 50.0 | 50.0 | 0.0 | 0.59 | -0.78 | 177.8 | 100.0 | 20.0 | 0.3 | 0.1 | 4.3 | -0.657 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:BTCUSDT | 5m | all | 10 | 30.0 | 70.0 | 0.0 | 0.54 | -0.83 | 135.3 | 100.0 | 20.0 | 3.5 | 0.5 | 12.4 | 0.043 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:ETHUSDT | 15m | all | 34 | 52.9 | 44.1 | 0.0 | 0.71 | -0.64 | 205.1 | 100.0 | 20.0 | 0.1 | 0.0 | 4.8 | -0.644 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:ETHUSDT | 5m | all | 18 | 38.9 | 61.1 | 0.0 | 0.73 | -0.86 | 131.8 | 100.0 | 20.0 | 5.3 | 6.0 | 18.4 | 0.122 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:ZECUSDT | 15m | all | 28 | 57.1 | 42.9 | 0.0 | 0.83 | -0.66 | 306.0 | 100.0 | 20.0 | 0.3 | 0.0 | 4.5 | 0.029 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:ZECUSDT | 5m | all | 36 | 66.7 | 33.3 | 0.0 | 0.80 | -0.61 | 195.0 | 100.0 | 20.0 | 2.3 | 3.6 | 12.5 | 0.703 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:BTCUSDT | 15m | all | 18 | 50.0 | 50.0 | 50.0 | 0.59 | -1.11 | 162.5 | 100.0 | 4.0 | 0.3 | 0.1 | 4.3 | -0.658 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:BTCUSDT | 5m | all | 6 | 50.0 | 50.0 | 50.0 | 0.66 | -0.83 | 134.0 | 100.0 | 4.0 | 5.0 | 0.0 | 11.3 | -0.361 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:ETHUSDT | 15m | all | 29 | 51.7 | 44.8 | 44.8 | 0.68 | -0.83 | 205.3 | 100.0 | 4.0 | 0.2 | 0.0 | 4.4 | -0.679 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:ETHUSDT | 5m | all | 17 | 64.7 | 35.3 | 35.3 | 0.78 | -0.86 | 139.6 | 100.0 | 4.0 | 6.6 | 7.9 | 18.0 | -0.033 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:ZECUSDT | 15m | all | 28 | 60.7 | 39.3 | 39.3 | 0.85 | -0.80 | 290.1 | 100.0 | 4.0 | 0.3 | 0.0 | 4.5 | 0.029 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:ZECUSDT | 5m | all | 34 | 76.5 | 23.5 | 23.5 | 0.85 | -0.63 | 184.0 | 100.0 | 4.0 | 2.2 | 4.4 | 12.1 | 0.702 |
| Stop Engine Current | Sweep Wick | BINANCE:BTCUSDT | 15m | short | 14 | 57.1 | 42.9 | 0.0 | 0.65 | -0.75 | 162.2 | 15.0 | 4.0 | 0.1 | 0.0 | 3.3 | -1.161 |
| Stop Engine Current | Sweep Wick | BINANCE:BTCUSDT | 15m | long | 4 | 25.0 | 75.0 | 0.0 | 0.50 | -0.83 | 121.5 | 15.0 | 4.0 | 0.3 | n/a | 6.0 | 1.322 |
| Stop Engine Current | Sweep Wick | BINANCE:BTCUSDT | 5m | long | 18 | 44.4 | 55.6 | 0.0 | 0.60 | -0.76 | 70.5 | 15.0 | 4.0 | 1.6 | 1.0 | 20.0 | 0.764 |
| Stop Engine Current | Sweep Wick | BINANCE:BTCUSDT | 5m | short | 7 | 71.4 | 28.6 | 0.0 | 0.79 | -0.57 | 97.9 | 15.0 | 4.0 | 4.9 | 0.5 | 16.9 | -1.418 |
| Stop Engine Current | Sweep Wick | BINANCE:ETHUSDT | 15m | short | 29 | 51.7 | 44.8 | 0.0 | 0.69 | -0.66 | 186.6 | 15.0 | 4.0 | 0.2 | 0.0 | 5.2 | -1.075 |
| Stop Engine Current | Sweep Wick | BINANCE:ETHUSDT | 15m | long | 4 | 75.0 | 25.0 | 0.0 | 0.78 | -0.55 | 132.7 | 15.0 | 4.0 | 0.0 | 0.0 | 4.5 | 1.878 |
| Stop Engine Current | Sweep Wick | BINANCE:ETHUSDT | 5m | long | 19 | 47.4 | 52.6 | 0.0 | 0.63 | -0.86 | 106.1 | 15.0 | 4.0 | 5.5 | 7.0 | 18.4 | 0.640 |
| Stop Engine Current | Sweep Wick | BINANCE:ETHUSDT | 5m | short | 11 | 45.5 | 54.5 | 0.0 | 0.67 | -0.80 | 102.4 | 15.0 | 4.0 | 2.1 | 1.0 | 15.5 | -0.786 |
| Stop Engine Current | Sweep Wick | BINANCE:ZECUSDT | 15m | long | 15 | 73.3 | 26.7 | 0.0 | 0.87 | -0.58 | 285.2 | 15.0 | 4.0 | 0.4 | 0.0 | 4.2 | 0.690 |
| Stop Engine Current | Sweep Wick | BINANCE:ZECUSDT | 15m | short | 11 | 54.5 | 45.5 | 0.0 | 0.85 | -0.72 | 260.8 | 15.0 | 4.0 | 0.1 | 0.0 | 5.5 | -0.952 |
| Stop Engine Current | Sweep Wick | BINANCE:ZECUSDT | 5m | long | 35 | 65.7 | 34.3 | 0.0 | 0.78 | -0.64 | 150.6 | 15.0 | 4.0 | 1.6 | 1.5 | 11.3 | 1.154 |
| Stop Engine Current | Sweep Wick | BINANCE:ZECUSDT | 5m | short | 9 | 66.7 | 33.3 | 0.0 | 0.71 | -0.65 | 172.1 | 15.0 | 4.0 | 7.7 | 11.7 | 21.9 | -0.993 |
| Stop Floor 75bps | Sweep Wick | BINANCE:BTCUSDT | 15m | short | 14 | 50.0 | 50.0 | 0.0 | 0.59 | -0.80 | 170.6 | 75.0 | 4.0 | 0.1 | 0.0 | 3.6 | -1.118 |
| Stop Floor 75bps | Sweep Wick | BINANCE:BTCUSDT | 15m | long | 4 | 25.0 | 75.0 | 0.0 | 0.50 | -0.83 | 121.5 | 75.0 | 4.0 | 0.3 | n/a | 6.0 | 1.322 |
| Stop Floor 75bps | Sweep Wick | BINANCE:BTCUSDT | 5m | long | 10 | 30.0 | 70.0 | 0.0 | 0.50 | -0.86 | 100.3 | 75.0 | 4.0 | 2.1 | 2.0 | 16.2 | 1.073 |
| Stop Floor 75bps | Sweep Wick | BINANCE:BTCUSDT | 5m | short | 3 | 66.7 | 33.3 | 0.0 | 0.89 | -0.56 | 142.0 | 75.0 | 4.0 | 8.7 | n/a | 12.3 | -1.756 |
| Stop Floor 75bps | Sweep Wick | BINANCE:ETHUSDT | 15m | long | 6 | 50.0 | 50.0 | 0.0 | 0.65 | -0.71 | 138.2 | 75.0 | 4.0 | 0.0 | 0.0 | 3.3 | 1.658 |
| Stop Floor 75bps | Sweep Wick | BINANCE:ETHUSDT | 15m | short | 29 | 55.2 | 41.4 | 0.0 | 0.72 | -0.65 | 191.1 | 75.0 | 4.0 | 0.1 | 0.0 | 4.9 | -1.016 |
| Stop Floor 75bps | Sweep Wick | BINANCE:ETHUSDT | 5m | long | 15 | 46.7 | 53.3 | 0.0 | 0.67 | -0.87 | 122.3 | 75.0 | 4.0 | 7.5 | 9.6 | 18.4 | 0.624 |
| Stop Floor 75bps | Sweep Wick | BINANCE:ETHUSDT | 5m | short | 8 | 50.0 | 50.0 | 0.0 | 0.69 | -0.75 | 119.3 | 75.0 | 4.0 | 1.8 | 2.0 | 14.5 | -0.864 |
| Stop Floor 75bps | Sweep Wick | BINANCE:ZECUSDT | 15m | long | 17 | 64.7 | 35.3 | 0.0 | 0.84 | -0.63 | 309.1 | 75.0 | 4.0 | 0.4 | 0.0 | 3.8 | 0.663 |
| Stop Floor 75bps | Sweep Wick | BINANCE:ZECUSDT | 15m | short | 11 | 54.5 | 45.5 | 0.0 | 0.85 | -0.72 | 260.8 | 75.0 | 4.0 | 0.1 | 0.0 | 5.5 | -0.952 |
| Stop Floor 75bps | Sweep Wick | BINANCE:ZECUSDT | 5m | long | 30 | 70.0 | 30.0 | 0.0 | 0.82 | -0.54 | 169.4 | 75.0 | 4.0 | 1.4 | 0.1 | 10.4 | 1.245 |
| Stop Floor 75bps | Sweep Wick | BINANCE:ZECUSDT | 5m | short | 8 | 75.0 | 25.0 | 0.0 | 0.78 | -0.59 | 184.7 | 75.0 | 4.0 | 7.9 | 15.5 | 21.3 | -1.117 |
| Stop Floor 100bps | Sweep Wick | BINANCE:BTCUSDT | 15m | short | 14 | 50.0 | 50.0 | 0.0 | 0.59 | -0.80 | 170.6 | 100.0 | 4.0 | 0.1 | 0.0 | 3.6 | -1.118 |
| Stop Floor 100bps | Sweep Wick | BINANCE:BTCUSDT | 15m | long | 4 | 25.0 | 75.0 | 0.0 | 0.39 | -0.86 | 134.1 | 100.0 | 4.0 | 1.0 | 1.0 | 6.8 | 0.955 |
| Stop Floor 100bps | Sweep Wick | BINANCE:BTCUSDT | 5m | long | 3 | 33.3 | 66.7 | 0.0 | 0.43 | -0.85 | 126.1 | 100.0 | 4.0 | 1.3 | 0.0 | 10.3 | 1.034 |
| Stop Floor 100bps | Sweep Wick | BINANCE:BTCUSDT | 5m | short | 3 | 66.7 | 33.3 | 0.0 | 0.89 | -0.56 | 142.0 | 100.0 | 4.0 | 8.7 | n/a | 12.3 | -1.756 |
| Stop Floor 100bps | Sweep Wick | BINANCE:ETHUSDT | 15m | long | 7 | 57.1 | 42.9 | 0.0 | 0.70 | -0.64 | 149.8 | 100.0 | 4.0 | 0.4 | 0.0 | 5.1 | 1.905 |
| Stop Floor 100bps | Sweep Wick | BINANCE:ETHUSDT | 15m | short | 28 | 53.6 | 46.4 | 0.0 | 0.66 | -0.70 | 213.4 | 100.0 | 4.0 | 0.2 | 0.0 | 5.0 | -1.412 |
| Stop Floor 100bps | Sweep Wick | BINANCE:ETHUSDT | 5m | long | 11 | 54.5 | 45.5 | 0.0 | 0.70 | -0.84 | 137.8 | 100.0 | 4.0 | 8.9 | 9.8 | 21.7 | 0.630 |
| Stop Floor 100bps | Sweep Wick | BINANCE:ETHUSDT | 5m | short | 6 | 66.7 | 33.3 | 0.0 | 0.83 | -0.67 | 142.8 | 100.0 | 4.0 | 2.5 | 3.0 | 11.2 | -1.248 |
| Stop Floor 100bps | Sweep Wick | BINANCE:ZECUSDT | 15m | long | 17 | 64.7 | 35.3 | 0.0 | 0.84 | -0.63 | 309.1 | 100.0 | 4.0 | 0.4 | 0.0 | 3.8 | 0.663 |
| Stop Floor 100bps | Sweep Wick | BINANCE:ZECUSDT | 15m | short | 11 | 54.5 | 45.5 | 0.0 | 0.85 | -0.72 | 260.8 | 100.0 | 4.0 | 0.1 | 0.0 | 5.5 | -0.952 |
| Stop Floor 100bps | Sweep Wick | BINANCE:ZECUSDT | 5m | long | 27 | 74.1 | 25.9 | 0.0 | 0.85 | -0.52 | 179.9 | 100.0 | 4.0 | 1.3 | 0.0 | 10.0 | 1.207 |
| Stop Floor 100bps | Sweep Wick | BINANCE:ZECUSDT | 5m | short | 7 | 71.4 | 28.6 | 0.0 | 0.75 | -0.64 | 199.8 | 100.0 | 4.0 | 5.6 | 15.5 | 19.9 | -1.246 |
| Stop Floor 125bps | Sweep Wick | BINANCE:BTCUSDT | 15m | short | 13 | 46.2 | 53.8 | 0.0 | 0.56 | -0.82 | 178.2 | 125.0 | 4.0 | 0.4 | 0.2 | 3.8 | -1.024 |
| Stop Floor 125bps | Sweep Wick | BINANCE:BTCUSDT | 15m | long | 3 | 33.3 | 66.7 | 0.0 | 0.52 | -0.71 | 147.6 | 125.0 | 4.0 | 1.0 | n/a | 5.7 | 1.133 |
| Stop Floor 125bps | Sweep Wick | BINANCE:BTCUSDT | 5m | long | 2 | 0.0 | 100.0 | 0.0 | 0.32 | -1.03 | 161.1 | 125.0 | 4.0 | 3.0 | n/a | 8.5 | 0.775 |
| Stop Floor 125bps | Sweep Wick | BINANCE:BTCUSDT | 5m | short | 2 | 100.0 | 0.0 | 0.0 | 0.97 | -0.31 | 160.5 | 125.0 | 4.0 | 4.0 | n/a | 6.0 | -2.406 |
| Stop Floor 125bps | Sweep Wick | BINANCE:ETHUSDT | 15m | long | 4 | 50.0 | 50.0 | 0.0 | 0.72 | -0.74 | 149.5 | 125.0 | 4.0 | 0.0 | 0.0 | 3.5 | 2.248 |
| Stop Floor 125bps | Sweep Wick | BINANCE:ETHUSDT | 15m | short | 20 | 40.0 | 60.0 | 0.0 | 0.55 | -0.78 | 242.6 | 125.0 | 4.0 | 0.3 | 0.0 | 4.3 | -1.316 |
| Stop Floor 125bps | Sweep Wick | BINANCE:ETHUSDT | 5m | long | 7 | 57.1 | 42.9 | 0.0 | 0.75 | -0.84 | 151.0 | 125.0 | 4.0 | 9.1 | 11.0 | 23.4 | 0.661 |
| Stop Floor 125bps | Sweep Wick | BINANCE:ETHUSDT | 5m | short | 4 | 50.0 | 50.0 | 0.0 | 0.57 | -0.74 | 166.8 | 125.0 | 4.0 | 4.8 | 3.0 | 13.0 | -0.603 |
| Stop Floor 125bps | Sweep Wick | BINANCE:ZECUSDT | 15m | long | 17 | 64.7 | 35.3 | 0.0 | 0.84 | -0.63 | 309.1 | 125.0 | 4.0 | 0.4 | 0.0 | 3.8 | 0.663 |
| Stop Floor 125bps | Sweep Wick | BINANCE:ZECUSDT | 15m | short | 11 | 54.5 | 45.5 | 0.0 | 0.85 | -0.72 | 260.8 | 125.0 | 4.0 | 0.1 | 0.0 | 5.5 | -0.952 |
| Stop Floor 125bps | Sweep Wick | BINANCE:ZECUSDT | 5m | long | 24 | 79.2 | 20.8 | 0.0 | 0.88 | -0.49 | 196.0 | 125.0 | 4.0 | 1.5 | 2.5 | 10.8 | 1.256 |
| Stop Floor 125bps | Sweep Wick | BINANCE:ZECUSDT | 5m | short | 7 | 71.4 | 28.6 | 0.0 | 0.76 | -0.65 | 203.2 | 125.0 | 4.0 | 5.7 | 10.3 | 20.0 | -1.154 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:BTCUSDT | 15m | short | 14 | 57.1 | 42.9 | 0.0 | 0.65 | -0.77 | 186.9 | 100.0 | 20.0 | 0.1 | 0.0 | 3.6 | -1.118 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:BTCUSDT | 15m | long | 4 | 25.0 | 75.0 | 0.0 | 0.38 | -0.81 | 146.0 | 100.0 | 20.0 | 0.8 | 1.0 | 6.5 | 0.958 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:BTCUSDT | 5m | long | 7 | 14.3 | 85.7 | 0.0 | 0.41 | -0.95 | 125.4 | 100.0 | 20.0 | 1.3 | 0.5 | 12.4 | 0.814 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:BTCUSDT | 5m | short | 3 | 66.7 | 33.3 | 0.0 | 0.86 | -0.53 | 158.2 | 100.0 | 20.0 | 8.7 | n/a | 12.3 | -1.756 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:ETHUSDT | 15m | long | 6 | 50.0 | 50.0 | 0.0 | 0.78 | -0.69 | 154.0 | 100.0 | 20.0 | 0.0 | 0.0 | 3.3 | 1.658 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:ETHUSDT | 15m | short | 28 | 53.6 | 42.9 | 0.0 | 0.69 | -0.63 | 216.0 | 100.0 | 20.0 | 0.2 | 0.0 | 5.1 | -1.137 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:ETHUSDT | 5m | long | 12 | 33.3 | 66.7 | 0.0 | 0.69 | -0.92 | 132.3 | 100.0 | 20.0 | 7.1 | 7.7 | 20.3 | 0.583 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:ETHUSDT | 5m | short | 6 | 50.0 | 50.0 | 0.0 | 0.80 | -0.74 | 130.9 | 100.0 | 20.0 | 1.7 | 1.0 | 14.7 | -0.801 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:ZECUSDT | 15m | long | 17 | 58.8 | 41.2 | 0.0 | 0.83 | -0.64 | 324.6 | 100.0 | 20.0 | 0.4 | 0.0 | 3.8 | 0.663 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:ZECUSDT | 15m | short | 11 | 54.5 | 45.5 | 0.0 | 0.84 | -0.70 | 277.1 | 100.0 | 20.0 | 0.1 | 0.0 | 5.5 | -0.952 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:ZECUSDT | 5m | long | 29 | 65.5 | 34.5 | 0.0 | 0.81 | -0.61 | 190.0 | 100.0 | 20.0 | 1.4 | 0.1 | 10.8 | 1.173 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | BINANCE:ZECUSDT | 5m | short | 7 | 71.4 | 28.6 | 0.0 | 0.75 | -0.61 | 216.1 | 100.0 | 20.0 | 5.6 | 15.5 | 19.9 | -1.246 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:BTCUSDT | 15m | short | 14 | 57.1 | 42.9 | 42.9 | 0.65 | -1.14 | 170.6 | 100.0 | 4.0 | 0.1 | 0.0 | 3.6 | -1.118 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:BTCUSDT | 15m | long | 4 | 25.0 | 75.0 | 75.0 | 0.39 | -1.01 | 134.1 | 100.0 | 4.0 | 1.0 | 1.0 | 6.8 | 0.955 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:BTCUSDT | 5m | long | 3 | 33.3 | 66.7 | 66.7 | 0.43 | -1.05 | 126.1 | 100.0 | 4.0 | 1.3 | 0.0 | 10.3 | 1.034 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:BTCUSDT | 5m | short | 3 | 66.7 | 33.3 | 33.3 | 0.89 | -0.60 | 142.0 | 100.0 | 4.0 | 8.7 | n/a | 12.3 | -1.756 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:ETHUSDT | 15m | long | 6 | 66.7 | 33.3 | 33.3 | 0.80 | -0.76 | 138.2 | 100.0 | 4.0 | 0.0 | 0.0 | 3.3 | 1.658 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:ETHUSDT | 15m | short | 23 | 47.8 | 47.8 | 47.8 | 0.65 | -0.85 | 222.8 | 100.0 | 4.0 | 0.3 | 0.0 | 4.7 | -1.288 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:ETHUSDT | 5m | long | 11 | 54.5 | 45.5 | 45.5 | 0.70 | -0.93 | 137.8 | 100.0 | 4.0 | 8.9 | 9.8 | 21.7 | 0.630 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:ETHUSDT | 5m | short | 6 | 83.3 | 16.7 | 16.7 | 0.93 | -0.73 | 142.8 | 100.0 | 4.0 | 2.5 | 3.0 | 11.2 | -1.248 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:ZECUSDT | 15m | long | 17 | 64.7 | 35.3 | 35.3 | 0.84 | -0.70 | 309.1 | 100.0 | 4.0 | 0.4 | 0.0 | 3.8 | 0.663 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:ZECUSDT | 15m | short | 11 | 54.5 | 45.5 | 45.5 | 0.85 | -0.96 | 260.8 | 100.0 | 4.0 | 0.1 | 0.0 | 5.5 | -0.952 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:ZECUSDT | 5m | long | 27 | 77.8 | 22.2 | 22.2 | 0.87 | -0.60 | 179.9 | 100.0 | 4.0 | 1.3 | 0.0 | 10.0 | 1.207 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | BINANCE:ZECUSDT | 5m | short | 7 | 71.4 | 28.6 | 28.6 | 0.75 | -0.75 | 199.8 | 100.0 | 4.0 | 5.6 | 15.5 | 19.9 | -1.246 |

## Regime Telemetry
| System | Stop | Regime Type | Regime | Parents | P&L | TP1 First % | Stop First % | CloseStop % | Avg MFE R | Avg MAE R | Avg Risk bps | Avg Min Floor bps | Avg Buffer bps | Avg ATR bps | Avg Range bps | Avg Range/ATR | Avg Stop/ATR | Avg TP1 R | Long | Short |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Stop Engine Current | Sweep Wick | risk_bps | risk>175 | 55 | 1190.48 | 61.8 | 38.2 | 0.0 | 0.78 | -0.64 | 274.6 | 15.0 | 4.0 | 69.7 | 156.6 | 2.34 | 4.39 | 1.00 | 26 | 29 |
| Stop Engine Current | Sweep Wick | risk_bps | risk100-175 | 64 | 1244.07 | 60.9 | 39.1 | 0.0 | 0.73 | -0.69 | 136.2 | 15.0 | 4.0 | 39.2 | 83.3 | 2.19 | 3.93 | 1.00 | 32 | 32 |
| Stop Engine Current | Sweep Wick | risk_bps | risk<=100 | 57 | -1645.40 | 47.4 | 50.9 | 0.0 | 0.64 | -0.77 | 69.2 | 15.0 | 4.0 | 23.3 | 49.1 | 2.14 | 3.59 | 1.00 | 37 | 20 |
| Stop Floor 75bps | Sweep Wick | risk_bps | risk>175 | 58 | 932.68 | 58.6 | 41.4 | 0.0 | 0.76 | -0.66 | 280.4 | 75.0 | 4.0 | 74.3 | 162.4 | 2.31 | 4.31 | 1.00 | 28 | 30 |
| Stop Floor 75bps | Sweep Wick | risk_bps | risk100-175 | 68 | 846.59 | 58.8 | 41.2 | 0.0 | 0.72 | -0.71 | 136.5 | 75.0 | 4.0 | 39.7 | 84.7 | 2.20 | 3.88 | 1.00 | 35 | 33 |
| Stop Floor 75bps | Sweep Wick | risk_bps | risk<=100 | 29 | -864.93 | 44.8 | 51.7 | 0.0 | 0.68 | -0.71 | 89.5 | 75.0 | 4.0 | 24.3 | 52.4 | 2.15 | 4.18 | 1.00 | 19 | 10 |
| Stop Floor 100bps | Sweep Wick | risk_bps | risk>175 | 63 | 938.59 | 58.7 | 41.3 | 0.0 | 0.76 | -0.65 | 274.8 | 100.0 | 4.0 | 72.2 | 163.0 | 2.42 | 4.33 | 1.00 | 29 | 34 |
| Stop Floor 100bps | Sweep Wick | risk_bps | risk100-175 | 75 | 860.35 | 60.0 | 40.0 | 0.0 | 0.72 | -0.70 | 135.9 | 100.0 | 4.0 | 38.5 | 82.8 | 2.22 | 3.99 | 1.00 | 40 | 35 |
| Stop Floor 125bps | Sweep Wick | risk_bps | risk>175 | 62 | 916.32 | 56.5 | 43.5 | 0.0 | 0.74 | -0.68 | 276.5 | 125.0 | 4.0 | 72.2 | 159.9 | 2.36 | 4.39 | 1.00 | 29 | 33 |
| Stop Floor 125bps | Sweep Wick | risk_bps | risk100-175 | 52 | 887.47 | 59.6 | 40.4 | 0.0 | 0.71 | -0.69 | 147.7 | 125.0 | 4.0 | 41.0 | 85.1 | 2.13 | 4.10 | 1.00 | 28 | 24 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | risk_bps | risk>175 | 71 | 605.87 | 54.9 | 45.1 | 0.0 | 0.72 | -0.68 | 274.7 | 100.0 | 20.0 | 70.3 | 154.1 | 2.32 | 4.45 | 1.00 | 33 | 38 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | risk_bps | risk100-175 | 73 | -918.22 | 52.1 | 46.6 | 0.0 | 0.74 | -0.71 | 136.7 | 100.0 | 20.0 | 34.1 | 72.5 | 2.15 | 4.52 | 1.00 | 42 | 31 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | risk_bps | risk>175 | 60 | 902.88 | 58.3 | 40.0 | 40.0 | 0.76 | -0.78 | 278.4 | 100.0 | 4.0 | 73.1 | 162.4 | 2.38 | 4.36 | 1.00 | 28 | 32 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | risk_bps | risk100-175 | 72 | 558.35 | 63.9 | 36.1 | 36.1 | 0.75 | -0.84 | 135.1 | 100.0 | 4.0 | 37.9 | 82.1 | 2.22 | 4.01 | 1.00 | 40 | 32 |
| Stop Engine Current | Sweep Wick | atr_bps | atr<=75 | 152 | 594.13 | 58.6 | 40.8 | 0.0 | 0.73 | -0.69 | 132.2 | 15.0 | 4.0 | 34.6 | 77.3 | 2.25 | 4.08 | 1.00 | 84 | 68 |
| Stop Engine Current | Sweep Wick | atr_bps | atr75-150 | 23 | 97.03 | 43.5 | 56.5 | 0.0 | 0.62 | -0.75 | 311.1 | 15.0 | 4.0 | 93.6 | 192.9 | 2.06 | 3.31 | 1.00 | 10 | 13 |
| Stop Engine Current | Sweep Wick | atr_bps | atr>150 | 1 | 97.99 | 100.0 | 0.0 | 0.0 | 0.99 | -0.29 | 510.2 | 15.0 | 4.0 | 253.8 | 556.9 | 2.19 | 2.01 | 1.00 | 1 | 0 |
| Stop Floor 75bps | Sweep Wick | atr_bps | atr<=75 | 129 | 928.06 | 58.9 | 40.3 | 0.0 | 0.75 | -0.67 | 151.2 | 75.0 | 4.0 | 37.8 | 85.2 | 2.27 | 4.28 | 1.00 | 69 | 60 |
| Stop Floor 75bps | Sweep Wick | atr_bps | atr75-150 | 23 | 93.33 | 43.5 | 56.5 | 0.0 | 0.62 | -0.75 | 311.1 | 75.0 | 4.0 | 93.6 | 192.9 | 2.06 | 3.31 | 1.00 | 10 | 13 |
| Stop Floor 75bps | Sweep Wick | atr_bps | atr>150 | 3 | -107.05 | 33.3 | 66.7 | 0.0 | 0.72 | -0.77 | 495.5 | 75.0 | 4.0 | 227.7 | 423.6 | 1.85 | 2.24 | 1.00 | 3 | 0 |
| Stop Floor 100bps | Sweep Wick | atr_bps | atr<=75 | 112 | 1839.34 | 63.4 | 36.6 | 0.0 | 0.76 | -0.66 | 168.4 | 100.0 | 4.0 | 41.1 | 96.2 | 2.38 | 4.37 | 1.00 | 56 | 56 |
| Stop Floor 100bps | Sweep Wick | atr_bps | atr75-150 | 23 | 66.65 | 43.5 | 56.5 | 0.0 | 0.62 | -0.75 | 311.1 | 100.0 | 4.0 | 93.6 | 192.9 | 2.06 | 3.31 | 1.00 | 10 | 13 |
| Stop Floor 100bps | Sweep Wick | atr_bps | atr>150 | 3 | -107.05 | 33.3 | 66.7 | 0.0 | 0.72 | -0.77 | 495.5 | 100.0 | 4.0 | 227.7 | 423.6 | 1.85 | 2.24 | 1.00 | 3 | 0 |
| Stop Floor 125bps | Sweep Wick | atr_bps | atr<=75 | 88 | 1808.45 | 62.5 | 37.5 | 0.0 | 0.76 | -0.66 | 183.9 | 125.0 | 4.0 | 42.9 | 98.1 | 2.32 | 4.58 | 1.00 | 44 | 44 |
| Stop Floor 125bps | Sweep Wick | atr_bps | atr75-150 | 23 | 102.39 | 43.5 | 56.5 | 0.0 | 0.62 | -0.75 | 311.1 | 125.0 | 4.0 | 93.6 | 192.9 | 2.06 | 3.31 | 1.00 | 10 | 13 |
| Stop Floor 125bps | Sweep Wick | atr_bps | atr>150 | 3 | -107.05 | 33.3 | 66.7 | 0.0 | 0.72 | -0.77 | 495.5 | 125.0 | 4.0 | 227.7 | 423.6 | 1.85 | 2.24 | 1.00 | 3 | 0 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | atr_bps | atr<=75 | 118 | -89.40 | 56.8 | 42.4 | 0.0 | 0.75 | -0.68 | 173.1 | 100.0 | 20.0 | 39.4 | 89.2 | 2.28 | 4.74 | 1.00 | 62 | 56 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | atr_bps | atr75-150 | 23 | -116.06 | 39.1 | 60.9 | 0.0 | 0.61 | -0.76 | 327.2 | 100.0 | 20.0 | 93.6 | 192.9 | 2.06 | 3.48 | 1.00 | 10 | 13 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | atr_bps | atr>150 | 3 | -106.89 | 33.3 | 66.7 | 0.0 | 0.71 | -0.77 | 510.5 | 100.0 | 20.0 | 227.7 | 423.6 | 1.85 | 2.31 | 1.00 | 3 | 0 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | atr_bps | atr<=75 | 107 | 1523.35 | 65.4 | 34.6 | 34.6 | 0.78 | -0.79 | 167.8 | 100.0 | 4.0 | 40.7 | 94.2 | 2.35 | 4.39 | 1.00 | 55 | 52 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | atr_bps | atr75-150 | 22 | 62.66 | 45.5 | 50.0 | 50.0 | 0.64 | -0.92 | 318.1 | 100.0 | 4.0 | 94.4 | 195.9 | 2.08 | 3.36 | 1.00 | 10 | 12 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | atr_bps | atr>150 | 3 | -124.78 | 33.3 | 66.7 | 66.7 | 0.72 | -0.89 | 495.5 | 100.0 | 4.0 | 227.7 | 423.6 | 1.85 | 2.24 | 1.00 | 3 | 0 |
| Stop Engine Current | Sweep Wick | entry_range_bps | range>90 | 76 | 1499.82 | 59.2 | 39.5 | 0.0 | 0.73 | -0.69 | 221.1 | 15.0 | 4.0 | 65.0 | 150.3 | 2.48 | 3.61 | 1.00 | 38 | 38 |
| Stop Engine Current | Sweep Wick | entry_range_bps | range40-90 | 70 | -37.74 | 57.1 | 42.9 | 0.0 | 0.72 | -0.70 | 127.2 | 15.0 | 4.0 | 32.6 | 64.1 | 2.09 | 4.06 | 1.00 | 38 | 32 |
| Stop Engine Current | Sweep Wick | entry_range_bps | range<=40 | 30 | -672.93 | 50.0 | 50.0 | 0.0 | 0.67 | -0.74 | 68.6 | 15.0 | 4.0 | 15.1 | 27.6 | 1.85 | 4.62 | 1.00 | 19 | 11 |
| Stop Floor 75bps | Sweep Wick | entry_range_bps | range>90 | 79 | 1163.18 | 57.0 | 41.8 | 0.0 | 0.74 | -0.67 | 232.0 | 75.0 | 4.0 | 68.1 | 154.7 | 2.48 | 3.69 | 1.00 | 40 | 39 |
| Stop Floor 75bps | Sweep Wick | entry_range_bps | range40-90 | 64 | -224.33 | 56.3 | 43.8 | 0.0 | 0.71 | -0.69 | 135.3 | 75.0 | 4.0 | 33.7 | 64.4 | 1.98 | 4.17 | 1.00 | 35 | 29 |
| Stop Floor 75bps | Sweep Wick | entry_range_bps | range<=40 | 12 | -24.51 | 50.0 | 50.0 | 0.0 | 0.75 | -0.75 | 96.6 | 75.0 | 4.0 | 15.5 | 30.1 | 1.99 | 6.38 | 1.00 | 7 | 5 |
| Stop Floor 100bps | Sweep Wick | entry_range_bps | range>90 | 82 | 695.67 | 57.3 | 42.7 | 0.0 | 0.73 | -0.67 | 236.0 | 100.0 | 4.0 | 67.6 | 156.6 | 2.54 | 3.84 | 1.00 | 40 | 42 |
| Stop Floor 100bps | Sweep Wick | entry_range_bps | range40-90 | 50 | 891.07 | 62.0 | 38.0 | 0.0 | 0.76 | -0.67 | 148.8 | 100.0 | 4.0 | 35.6 | 68.9 | 2.01 | 4.39 | 1.00 | 25 | 25 |
| Stop Floor 100bps | Sweep Wick | entry_range_bps | range<=40 | 6 | 212.20 | 66.7 | 33.3 | 0.0 | 0.77 | -0.72 | 119.3 | 100.0 | 4.0 | 19.6 | 32.6 | 1.66 | 6.25 | 1.00 | 4 | 2 |
| Stop Floor 125bps | Sweep Wick | entry_range_bps | range>90 | 72 | 546.58 | 55.6 | 44.4 | 0.0 | 0.72 | -0.71 | 250.7 | 125.0 | 4.0 | 71.1 | 160.6 | 2.46 | 3.91 | 1.00 | 36 | 36 |
| Stop Floor 125bps | Sweep Wick | entry_range_bps | range40-90 | 40 | 890.01 | 60.0 | 40.0 | 0.0 | 0.72 | -0.65 | 162.4 | 125.0 | 4.0 | 36.3 | 67.6 | 1.92 | 4.72 | 1.00 | 20 | 20 |
| Stop Floor 125bps | Sweep Wick | entry_range_bps | range<=40 | 2 | 367.20 | 100.0 | 0.0 | 0.0 | 0.96 | -0.56 | 138.4 | 125.0 | 4.0 | 18.6 | 34.0 | 1.81 | 7.45 | 1.00 | 1 | 1 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | entry_range_bps | range>90 | 78 | -107.01 | 51.3 | 47.4 | 0.0 | 0.72 | -0.69 | 250.4 | 100.0 | 20.0 | 68.7 | 156.2 | 2.46 | 3.97 | 1.00 | 40 | 38 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | entry_range_bps | range40-90 | 57 | 137.90 | 57.9 | 42.1 | 0.0 | 0.75 | -0.69 | 155.3 | 100.0 | 20.0 | 34.6 | 66.2 | 1.97 | 4.70 | 1.00 | 30 | 27 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | entry_range_bps | range<=40 | 9 | -343.24 | 44.4 | 55.6 | 0.0 | 0.66 | -0.77 | 122.9 | 100.0 | 20.0 | 16.5 | 30.9 | 1.88 | 7.56 | 1.00 | 5 | 4 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | entry_range_bps | range>90 | 77 | 616.85 | 58.4 | 40.3 | 40.3 | 0.74 | -0.85 | 239.2 | 100.0 | 4.0 | 68.2 | 157.2 | 2.53 | 3.87 | 1.00 | 39 | 38 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | entry_range_bps | range40-90 | 49 | 662.46 | 65.3 | 34.7 | 34.7 | 0.78 | -0.76 | 149.1 | 100.0 | 4.0 | 35.6 | 68.5 | 1.99 | 4.39 | 1.00 | 25 | 24 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | entry_range_bps | range<=40 | 6 | 181.92 | 66.7 | 33.3 | 33.3 | 0.77 | -0.77 | 119.3 | 100.0 | 4.0 | 19.6 | 32.6 | 1.66 | 6.25 | 1.00 | 4 | 2 |
| Stop Engine Current | Sweep Wick | entry_range_atr | disp>1.5atr | 175 | 895.49 | 57.1 | 42.3 | 0.0 | 0.72 | -0.70 | 157.5 | 15.0 | 4.0 | 43.6 | 95.3 | 2.22 | 3.96 | 1.00 | 95 | 80 |
| Stop Engine Current | Sweep Wick | entry_range_atr | disp1.25-1.5atr | 1 | -106.34 | 0.0 | 100.0 | 0.0 | 0.57 | -1.02 | 207.1 | 15.0 | 4.0 | 42.9 | 64.4 | 1.50 | 4.82 | 1.00 | 0 | 1 |
| Stop Floor 75bps | Sweep Wick | entry_range_atr | disp>1.5atr | 154 | 1020.12 | 56.5 | 42.9 | 0.0 | 0.73 | -0.69 | 181.4 | 75.0 | 4.0 | 49.8 | 108.0 | 2.24 | 4.09 | 1.00 | 82 | 72 |
| Stop Floor 75bps | Sweep Wick | entry_range_atr | disp1.25-1.5atr | 1 | -105.78 | 0.0 | 100.0 | 0.0 | 0.57 | -1.02 | 207.1 | 75.0 | 4.0 | 42.9 | 64.4 | 1.50 | 4.82 | 1.00 | 0 | 1 |
| Stop Floor 100bps | Sweep Wick | entry_range_atr | disp>1.5atr | 137 | 1904.72 | 59.9 | 40.1 | 0.0 | 0.74 | -0.67 | 199.3 | 100.0 | 4.0 | 54.0 | 119.8 | 2.32 | 4.14 | 1.00 | 69 | 68 |
| Stop Floor 100bps | Sweep Wick | entry_range_atr | disp1.25-1.5atr | 1 | -105.78 | 0.0 | 100.0 | 0.0 | 0.57 | -1.02 | 207.1 | 100.0 | 4.0 | 42.9 | 64.4 | 1.50 | 4.82 | 1.00 | 0 | 1 |
| Stop Floor 125bps | Sweep Wick | entry_range_atr | disp>1.5atr | 113 | 1908.60 | 58.4 | 41.6 | 0.0 | 0.73 | -0.68 | 217.9 | 125.0 | 4.0 | 58.1 | 126.3 | 2.26 | 4.25 | 1.00 | 57 | 56 |
| Stop Floor 125bps | Sweep Wick | entry_range_atr | disp1.25-1.5atr | 1 | -104.81 | 0.0 | 100.0 | 0.0 | 0.57 | -1.02 | 207.1 | 125.0 | 4.0 | 42.9 | 64.4 | 1.50 | 4.82 | 1.00 | 0 | 1 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | entry_range_atr | disp>1.5atr | 143 | -206.92 | 53.8 | 45.5 | 0.0 | 0.73 | -0.69 | 204.6 | 100.0 | 20.0 | 52.0 | 113.1 | 2.24 | 4.48 | 1.00 | 75 | 68 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | entry_range_atr | disp1.25-1.5atr | 1 | -105.43 | 0.0 | 100.0 | 0.0 | 0.53 | -1.02 | 223.4 | 100.0 | 20.0 | 42.9 | 64.4 | 1.50 | 5.21 | 1.00 | 0 | 1 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | entry_range_atr | disp>1.5atr | 131 | 1580.97 | 61.8 | 37.4 | 37.4 | 0.76 | -0.81 | 200.2 | 100.0 | 4.0 | 54.0 | 119.0 | 2.30 | 4.17 | 1.00 | 68 | 63 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | entry_range_atr | disp1.25-1.5atr | 1 | -119.74 | 0.0 | 100.0 | 100.0 | 0.57 | -1.26 | 207.1 | 100.0 | 4.0 | 42.9 | 64.4 | 1.50 | 4.82 | 1.00 | 0 | 1 |
| Stop Engine Current | Sweep Wick | stop_floor_bps | floor_baseline | 176 | 789.15 | 56.8 | 42.6 | 0.0 | 0.72 | -0.70 | 157.7 | 15.0 | 4.0 | 43.6 | 95.1 | 2.22 | 3.96 | 1.00 | 95 | 81 |
| Stop Floor 75bps | Sweep Wick | stop_floor_bps | floor75 | 155 | 914.34 | 56.1 | 43.2 | 0.0 | 0.73 | -0.69 | 181.6 | 75.0 | 4.0 | 49.8 | 107.8 | 2.23 | 4.10 | 1.00 | 82 | 73 |
| Stop Floor 100bps | Sweep Wick | stop_floor_bps | floor100 | 138 | 1798.94 | 59.4 | 40.6 | 0.0 | 0.74 | -0.68 | 199.3 | 100.0 | 4.0 | 53.9 | 119.4 | 2.31 | 4.14 | 1.00 | 69 | 69 |
| Stop Floor 125bps | Sweep Wick | stop_floor_bps | floor125plus | 114 | 1803.79 | 57.9 | 42.1 | 0.0 | 0.73 | -0.68 | 217.8 | 125.0 | 4.0 | 58.0 | 125.8 | 2.26 | 4.26 | 1.00 | 57 | 57 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | stop_floor_bps | floor100 | 144 | -312.35 | 53.5 | 45.8 | 0.0 | 0.73 | -0.69 | 204.8 | 100.0 | 20.0 | 52.0 | 112.7 | 2.23 | 4.49 | 1.00 | 75 | 69 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | stop_floor_bps | floor100 | 132 | 1461.23 | 61.4 | 37.9 | 37.9 | 0.76 | -0.82 | 200.3 | 100.0 | 4.0 | 53.9 | 118.6 | 2.29 | 4.17 | 1.00 | 68 | 64 |
| Stop Engine Current | Sweep Wick | exit_reason | tp1 | 100 | 10245.15 | 100.0 | 0.0 | 0.0 | 0.96 | -0.43 | 158.2 | 15.0 | 4.0 | 43.8 | 95.2 | 2.24 | 4.00 | 1.00 | 55 | 45 |
| Stop Engine Current | Sweep Wick | exit_reason | stop | 75 | -9591.83 | 0.0 | 100.0 | 0.0 | 0.38 | -1.07 | 157.9 | 15.0 | 4.0 | 43.6 | 95.0 | 2.18 | 3.91 | 1.00 | 40 | 35 |
| Stop Engine Current | Sweep Wick | exit_reason | unknown | 1 | 135.83 | 0.0 | 0.0 | 0.0 | 1.62 | -0.07 | 95.1 | 15.0 | 4.0 | 25.9 | 91.3 | 3.52 | 3.67 | 1.00 | 0 | 1 |
| Stop Floor 75bps | Sweep Wick | exit_reason | stop | 67 | -8263.47 | 0.0 | 100.0 | 0.0 | 0.40 | -1.03 | 190.1 | 75.0 | 4.0 | 52.6 | 111.9 | 2.18 | 4.08 | 1.00 | 36 | 31 |
| Stop Floor 75bps | Sweep Wick | exit_reason | tp1 | 87 | 9045.74 | 100.0 | 0.0 | 0.0 | 0.97 | -0.43 | 176.1 | 75.0 | 4.0 | 47.9 | 104.8 | 2.26 | 4.11 | 1.00 | 46 | 41 |
| Stop Floor 75bps | Sweep Wick | exit_reason | unknown | 1 | 132.07 | 0.0 | 0.0 | 0.0 | 1.62 | -0.07 | 95.1 | 75.0 | 4.0 | 25.9 | 91.3 | 3.52 | 3.67 | 1.00 | 0 | 1 |
| Stop Floor 100bps | Sweep Wick | exit_reason | stop | 56 | -5987.48 | 0.0 | 100.0 | 0.0 | 0.40 | -1.03 | 215.0 | 100.0 | 4.0 | 59.1 | 129.8 | 2.29 | 4.04 | 1.00 | 26 | 30 |
| Stop Floor 100bps | Sweep Wick | exit_reason | tp1 | 82 | 7786.42 | 100.0 | 0.0 | 0.0 | 0.97 | -0.44 | 188.6 | 100.0 | 4.0 | 50.3 | 112.4 | 2.33 | 4.22 | 1.00 | 43 | 39 |
| Stop Floor 125bps | Sweep Wick | exit_reason | stop | 48 | -4212.81 | 0.0 | 100.0 | 0.0 | 0.39 | -1.03 | 236.0 | 125.0 | 4.0 | 63.8 | 138.8 | 2.25 | 4.14 | 1.00 | 20 | 28 |
| Stop Floor 125bps | Sweep Wick | exit_reason | tp1 | 66 | 6016.60 | 100.0 | 0.0 | 0.0 | 0.98 | -0.44 | 204.5 | 125.0 | 4.0 | 53.7 | 116.3 | 2.26 | 4.34 | 1.00 | 37 | 29 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | exit_reason | stop | 66 | -7700.12 | 0.0 | 100.0 | 0.0 | 0.44 | -1.03 | 212.5 | 100.0 | 20.0 | 55.1 | 118.4 | 2.20 | 4.43 | 1.00 | 37 | 29 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | exit_reason | tp1 | 77 | 7273.48 | 100.0 | 0.0 | 0.0 | 0.97 | -0.42 | 199.4 | 100.0 | 20.0 | 49.6 | 108.1 | 2.25 | 4.54 | 1.00 | 38 | 39 |
| Wide Buffer 20bps + Floor 100bps | Sweep Wide Buffer | exit_reason | unknown | 1 | 114.29 | 0.0 | 0.0 | 0.0 | 1.39 | -0.06 | 111.3 | 100.0 | 20.0 | 25.9 | 91.3 | 3.52 | 4.29 | 1.00 | 0 | 1 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | exit_reason | close_stop | 50 | -6594.28 | 0.0 | 100.0 | 100.0 | 0.41 | -1.38 | 216.5 | 100.0 | 4.0 | 59.6 | 130.1 | 2.30 | 4.05 | 1.00 | 24 | 26 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | exit_reason | tp1 | 81 | 8100.27 | 100.0 | 0.0 | 0.0 | 0.97 | -0.46 | 186.6 | 100.0 | 4.0 | 49.8 | 109.0 | 2.28 | 4.24 | 1.00 | 44 | 37 |
| Close Confirmed + Floor 100bps | Sweep Close Confirmed | exit_reason | max_hold | 1 | -44.76 | 0.0 | 0.0 | 0.0 | 0.57 | -1.16 | 494.8 | 100.0 | 4.0 | 104.1 | 321.2 | 3.08 | 4.75 | 1.00 | 0 | 1 |
