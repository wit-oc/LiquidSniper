# V7 Robustness Verdict Metrics

Generated from 12 selected structural-control Strategy Tester exports. Expected slots: 12. Missing: 0. Rejected candidates: 0.

## Source Ranges

| System | Symbol | TF | Report range | Trades | P&L | PF | Win % | DD % |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Structural Control 100bps | BTCUSDT | 15m | Oct 31, 2025 — May 28, 2026 | 21 | -350.41 | 0.693 | 47.6 | 6.15 |
| Structural Control 100bps | BTCUSDT | 5m | Mar 15, 2026 — May 28, 2026 | 6 | -153.83 | 0.599 | 50.0 | 2.38 |
| Structural Control 100bps | ETHUSDT | 15m | Oct 31, 2025 — May 28, 2026 | 28 | 244.53 | 1.218 | 50.0 | 3.09 |
| Structural Control 100bps | ETHUSDT | 5m | Mar 15, 2026 — May 28, 2026 | 17 | 337.61 | 1.305 | 58.8 | 4.63 |
| Structural Control 100bps | ZECUSDT | 15m | Oct 31, 2025 — May 28, 2026 | 26 | 708.68 | 2.095 | 65.4 | 1.13 |
| Structural Control 100bps | ZECUSDT | 5m | Mar 15, 2026 — May 28, 2026 | 34 | 1403.64 | 2.000 | 73.5 | 4.79 |
| Structural Control 125bps | BTCUSDT | 15m | Oct 31, 2025 — May 28, 2026 | 15 | -173.79 | 0.728 | 46.7 | 2.80 |
| Structural Control 125bps | BTCUSDT | 5m | Mar 15, 2026 — May 28, 2026 | 4 | 32.84 | 1.308 | 50.0 | 0.53 |
| Structural Control 125bps | ETHUSDT | 15m | Oct 31, 2025 — May 28, 2026 | 22 | -172.51 | 0.802 | 40.9 | 4.52 |
| Structural Control 125bps | ETHUSDT | 5m | Mar 15, 2026 — May 28, 2026 | 13 | 459.95 | 1.648 | 61.5 | 4.25 |
| Structural Control 125bps | ZECUSDT | 15m | Oct 31, 2025 — May 28, 2026 | 26 | 708.68 | 2.095 | 65.4 | 1.13 |
| Structural Control 125bps | ZECUSDT | 5m | Mar 15, 2026 — May 28, 2026 | 31 | 1560.93 | 2.716 | 77.4 | 2.67 |

## Full-History Control Check

| System | Trades | P&L | PF | Win % | DD % | TP1 first % | Stop first % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Structural Control 100bps | 132 | 2190.22 | 1.377 | 59.8 | 5.92 | 59.8 | 40.2 |
| Structural Control 125bps | 111 | 2416.10 | 1.622 | 60.4 | 3.85 | 60.4 | 39.6 |

## Windowed Robustness

Windows are calendar thirds of each symbol/timeframe report range, then basketed by relative window. 15m reports cover Oct 31, 2025 to May 28, 2026; 5m reports cover Mar 15, 2026 to May 28, 2026.

| System | Window | Trades | P&L | PF | Win % | DD % |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Structural Control 100bps | early | 45 | 832.87 | 1.654 | 62.2 | 3.46 |
| Structural Control 100bps | latest | 45 | 479.53 | 1.167 | 57.8 | 5.76 |
| Structural Control 100bps | middle | 42 | 877.82 | 1.529 | 59.5 | 6.17 |
| Structural Control 125bps | early | 38 | 616.54 | 1.664 | 60.5 | 3.88 |
| Structural Control 125bps | latest | 36 | 914.53 | 1.534 | 61.1 | 3.37 |
| Structural Control 125bps | middle | 37 | 885.03 | 1.712 | 59.5 | 4.10 |

## Candidate Symbol Windows

| Window | Symbol | Trades | P&L | PF | Win % | DD % |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| early | BTCUSDT | 6 | -23.41 | 0.889 | 50.0 | 2.10 |
| early | ETHUSDT | 17 | -68.41 | 0.883 | 47.1 | 2.99 |
| early | ZECUSDT | 15 | 708.36 | 6.334 | 80.0 | 0.52 |
| latest | BTCUSDT | 4 | -174.82 | 0.343 | 25.0 | 1.75 |
| latest | ETHUSDT | 6 | 387.76 | 2.451 | 66.7 | 2.12 |
| latest | ZECUSDT | 26 | 701.59 | 1.596 | 65.4 | 3.35 |
| middle | BTCUSDT | 9 | 57.28 | 1.214 | 55.6 | 1.59 |
| middle | ETHUSDT | 12 | -31.91 | 0.956 | 41.7 | 4.26 |
| middle | ZECUSDT | 16 | 859.66 | 4.498 | 75.0 | 1.10 |

## Candidate Timeframe Windows

| Window | TF | Trades | P&L | PF | Win % | DD % |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| early | 15m | 19 | 140.79 | 1.281 | 52.6 | 3.63 |
| early | 5m | 19 | 475.75 | 2.115 | 68.4 | 1.61 |
| latest | 15m | 22 | 151.97 | 1.149 | 54.5 | 2.31 |
| latest | 5m | 14 | 762.56 | 2.105 | 71.4 | 2.91 |
| middle | 15m | 22 | 69.62 | 1.110 | 50.0 | 2.03 |
| middle | 5m | 15 | 815.41 | 2.337 | 73.3 | 4.13 |

## Candidate Long/Short Windows

| Window | Side | Trades | P&L | PF | Win % | DD % |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| early | long | 10 | 503.37 | 4.133 | 80.0 | 1.56 |
| early | short | 28 | 113.17 | 1.147 | 53.6 | 4.74 |
| latest | long | 29 | 700.43 | 1.467 | 62.1 | 3.35 |
| latest | short | 7 | 214.10 | 2.004 | 57.1 | 2.12 |
| middle | long | 16 | 906.49 | 2.487 | 75.0 | 4.09 |
| middle | short | 21 | -21.46 | 0.966 | 47.6 | 2.31 |

## Symbol-Scope Test

| Scope | Trades | P&L | PF | Win % | DD % |
| --- | ---: | ---: | ---: | ---: | ---: |
| All symbols | 111 | 2416.10 | 1.622 | 60.4 | 3.85 |
| BTC+ETH only | 54 | 146.49 | 1.063 | 48.1 | 6.31 |
| ETH+ZEC only | 92 | 2557.05 | 1.815 | 63.0 | 3.84 |
| ZEC only | 57 | 2269.61 | 2.458 | 71.9 | 2.92 |
| BTC only | 19 | -140.95 | 0.811 | 47.4 | 2.66 |
| ETH only | 35 | 287.44 | 1.182 | 48.6 | 6.29 |

## Timeframe Contribution Test

| Scope | Trades | P&L | PF | Win % | DD % |
| --- | ---: | ---: | ---: | ---: | ---: |
| 15m+5m | 111 | 2416.10 | 1.622 | 60.4 | 3.85 |
| 15m only | 63 | 362.38 | 1.168 | 52.4 | 3.68 |
| 5m only | 48 | 2053.72 | 2.190 | 70.8 | 3.95 |

## Overfit Sanity Verdict

Fail / conditional. Abort further refinement optimization from this pass.

- ZEC explains most of the edge while BTC+ETH are weak.

Recommendation: Reject broad 125bps V7 as overfit/symbol-concentrated; keep only as symbol-scoped diagnostic unless a follow-up proves non-ZEC robustness.
