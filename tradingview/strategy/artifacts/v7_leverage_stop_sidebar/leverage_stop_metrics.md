# V7 Leverage Stop Sidebar Metrics

Generated from 42 selected TradingView Strategy Tester exports on 2026-05-28.
Raw JSON telemetry was moved to ignored local storage at `.telemetry/outputs/v7_leverage_stop_sidebar/leverage_stop_metrics.json`.

## Coverage

| Expected slots | Selected slots | Missing | Rejected reports | Invalid full-close rows | Parent/report mismatches |
|---:|---:|---:|---:|---:|---:|
| 42 | 42 | 0 | 0 | 0 | 0 |

## Basket Results

| Variant | Trades | Total P&L | PF | Win % | Max DD % | Positive Rows | NED Rows | Read |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Uniform 100x / 100bps | 128 | 2282.55 | 1.413 | 60.2 | 4.91 | 4 | 0 | Current in-run control. |
| Control 125bps | 111 | 2416.10 | 1.622 | 60.4 | 4.52 | 4 | 0 | Best broad control in this sidebar run. |
| Uniform 50x / 200bps | 68 | 733.86 | 1.345 | 51.5 | 6.30 | 3 | 0 | Fails DD target and hurts BTC/ETH. |
| Uniform 20x / 500bps | 13 | 563.54 | 4.142 | 61.5 | 0.76 | 2 | 3 | Sparse and ZEC-carried. |
| Uniform 10x / 1000bps | 0 | 0.00 | n/a | n/a | 0.00 | 0 | 6 | No trades. |
| Profile BTC100 ETH200 ZEC500 | 58 | -302.39 | 0.877 | 44.8 | 6.30 | 3 | 0 | Negative basket result. |
| Profile BTC125 ETH500 ZEC1000 | 20 | -191.77 | 0.759 | 45.0 | 2.80 | 1 | 3 | Negative and sparse. |

## Symbol Rollup

| Variant | BTCUSDT | ETHUSDT | ZECUSDT |
|---|---|---|---|
| Uniform 100x / 100bps | 23 trades, -411.91 P&L, PF 0.669 | 45 trades, 582.14 P&L, PF 1.261 | 60 trades, 2112.32 P&L, PF 2.030 |
| Control 125bps | 19 trades, -140.95 P&L, PF 0.811 | 35 trades, 287.44 P&L, PF 1.182 | 57 trades, 2269.61 P&L, PF 2.458 |
| Uniform 50x / 200bps | 8 trades, -131.51 P&L, PF 0.520 | 19 trades, -412.51 P&L, PF 0.482 | 41 trades, 1277.88 P&L, PF 2.206 |
| Uniform 20x / 500bps | 0 trades, 0.00 P&L, PF n/a | 1 trade, -50.82 P&L, PF 0.000 | 12 trades, 614.36 P&L, PF 5.780 |
| Uniform 10x / 1000bps | 0 trades, 0.00 P&L, PF n/a | 0 trades, 0.00 P&L, PF n/a | 0 trades, 0.00 P&L, PF n/a |
| Profile BTC100 ETH200 ZEC500 | 27 trades, -504.24 P&L, PF 0.669 | 19 trades, -412.51 P&L, PF 0.482 | 12 trades, 614.36 P&L, PF 5.780 |
| Profile BTC125 ETH500 ZEC1000 | 19 trades, -140.95 P&L, PF 0.811 | 1 trade, -50.82 P&L, PF 0.000 | 0 trades, 0.00 P&L, PF n/a |

## Decision Read

The sidebar does not produce a stronger implementation path than the current 100-125bps hard-floor direction. The only variants that clear the PF/DD screen are either the existing controls or a 500bps run with only 13 trades, three no-trade rows, and performance carried by ZEC. BTC does not improve under wider floors, ETH deteriorates sharply at 200bps+, and the symbol-profile variants are negative.

This does not fully disprove the creator's exact fixed-percent stop model, because this sidebar tested leverage-scaled floors on top of structural stops. It does reject using leverage-scaled structural stop floors as the next Unity Trading Model implementation path.
