# V7 Fixed Percent Stop Sidebar Metrics

Generated from 48 selected TradingView strategy exports on 2026-05-28.

## Coverage

| Expected slots | Selected slots | Missing | Rejected reports | Invalid full-close rows | Parent/report mismatches |
|---:|---:|---:|---:|---:|---:|
| 48 | 48 | 0 | 0 | 0 | 0 |

Raw aggregate JSON is intentionally local-only at `.telemetry/outputs/v7_fixed_percent_stop_sidebar/fixed_percent_stop_metrics.json`.

## Basket Summary

| System | Stop model | Rows | Trades | Total P&L | PF | Win % | Max row DD % | Positive rows | Verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Structural Control 100bps | Structural control | 6 | 132 | 2190.22 | 1.377 | 59.8 | 6.15 | 4 | Fails DD guard |
| Structural Control 125bps | Structural control | 6 | 111 | 2416.10 | 1.622 | 60.4 | 4.52 | 4 | Passes sidebar bar |
| Fixed 100x / 1.0% | Fixed percent | 6 | 189 | -260.13 | 0.982 | 55.6 | 12.28 | 2 | Reject |
| Fixed 50x / 2.0% | Fixed percent | 6 | 170 | 512.62 | 1.086 | 54.1 | 5.35 | 4 | Reject |
| Fixed 20x / 5.0% | Fixed percent | 6 | 135 | 91.15 | 1.025 | 45.9 | 3.86 | 4 | Reject |
| Fixed 10x / 10.0% | Fixed percent | 6 | 116 | 269.69 | 1.134 | 42.2 | 3.12 | 3 | Reject |
| Fixed Profile BTC100 ETH200 ZEC500 | Fixed percent profile | 6 | 154 | -1070.82 | 0.855 | 49.4 | 12.28 | 4 | Reject |
| Fixed Profile BTC125 ETH500 ZEC1000 | Fixed percent profile | 6 | 131 | -761.00 | 0.861 | 45.0 | 8.45 | 3 | Reject |

Decision bar for the sidebar was PF >= 1.35, DD <= 5%, meaningful trade count, and not solely ZEC-carried. The only passing row was the 125bps structural control.

## Symbol Rollup

| System | BTC P&L / PF / DD | ETH P&L / PF / DD | ZEC P&L / PF / DD |
|---|---:|---:|---:|
| Structural Control 100bps | -504.24 / 0.669 / 6.15 | 582.14 / 1.261 / 4.63 | 2112.32 / 2.030 / 4.79 |
| Structural Control 125bps | -140.95 / 0.811 / 2.80 | 287.44 / 1.182 / 4.52 | 2269.61 / 2.458 / 2.67 |
| Fixed 100x / 1.0% | -1624.02 / 0.547 / 12.28 | 466.39 / 1.110 / 9.09 | 897.50 / 1.134 / 10.15 |
| Fixed 50x / 2.0% | -619.98 / 0.615 / 4.43 | 185.81 / 1.116 / 3.77 | 946.79 / 1.344 / 5.35 |
| Fixed 20x / 5.0% | -135.47 / 0.784 / 1.86 | -140.77 / 0.840 / 3.58 | 367.39 / 1.168 / 3.86 |
| Fixed 10x / 10.0% | -19.70 / 0.936 / 1.07 | -301.35 / 0.412 / 3.12 | 590.74 / 1.494 / 2.26 |
| Fixed Profile BTC100 ETH200 ZEC500 | -1624.02 / 0.547 / 12.28 | 185.81 / 1.116 / 3.77 | 367.39 / 1.168 / 3.86 |
| Fixed Profile BTC125 ETH500 ZEC1000 | -1140.85 / 0.660 / 8.45 | -139.52 / 0.841 / 3.58 | 519.37 / 1.411 / 2.01 |

## Exit Telemetry

| System | TP1 first % | Stop first % | MaxHold % | Avg MFE R | Avg MAE R | Avg risk bps | Avg stop/ATR |
|---|---:|---:|---:|---:|---:|---:|---:|
| Structural Control 100bps | 59.8 | 40.2 | 0.0 | 0.74 | -0.67 | 193.8 | 4.19 |
| Structural Control 125bps | 60.4 | 39.6 | 0.0 | 0.74 | -0.67 | 212.8 | 4.34 |
| Fixed 100x / 1.0% | 53.4 | 43.9 | 0.0 | 0.77 | -0.73 | 100.0 | 3.26 |
| Fixed 50x / 2.0% | 54.1 | 44.1 | 1.8 | 0.71 | -0.71 | 200.0 | 6.15 |
| Fixed 20x / 5.0% | 34.1 | 31.9 | 33.3 | 0.61 | -0.60 | 500.0 | 14.94 |
| Fixed 10x / 10.0% | 19.8 | 13.8 | 65.5 | 0.43 | -0.43 | 1000.0 | 31.47 |
| Fixed Profile BTC100 ETH200 ZEC500 | 49.4 | 49.4 | 1.3 | 0.70 | -0.70 | 290.3 | 7.20 |
| Fixed Profile BTC125 ETH500 ZEC1000 | 36.6 | 33.6 | 29.0 | 0.60 | -0.63 | 565.8 | 13.92 |

The wider fixed-percent stops did reduce stop-outs, but mostly by moving exits into max-hold behavior. They did not convert enough trades into TP1 winners to improve PF.
