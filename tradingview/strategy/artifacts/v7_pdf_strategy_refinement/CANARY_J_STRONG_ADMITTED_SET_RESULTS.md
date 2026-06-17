# Canary J Pressure Test Results

Run directory: `tradingview/strategy/artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T04-01-32-075Z-deep-date-window-matrix`

## Harness Proof

- Status: `ok`
- Symbols: `BINANCE:ETHUSDT.P`, `BINANCE:ADAUSDT.P`, `BINANCE:ARBUSDT.P`, `BINANCE:SEIUSDT.P`
- Layout/title/date-range proof is in the harness JSON and per-symbol report text/screenshots.

## Basket

| Trades | Net USDT | Gross Profit | Gross Loss | PF | Win % | Avg USDT |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 2548.21 | 4254.38 | 1706.17 | 2.494 | 75.00 | 39.82 |

## By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:ADAUSDT.P | 12 | 356.52 | 2.111 | 66.67 | 29.71 |
| BINANCE:ARBUSDT.P | 12 | 466.09 | 2.466 | 75.00 | 38.84 |
| BINANCE:ETHUSDT.P | 29 | 1348.21 | 2.576 | 75.86 | 46.49 |
| BINANCE:SEIUSDT.P | 11 | 377.39 | 2.778 | 81.82 | 34.31 |

## By Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long | 42 | 1234.29 | 1.804 | 66.67 | 29.39 |
| short | 22 | 1313.92 | 8.712 | 90.91 | 59.72 |

## By Symbol And Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:ADAUSDT.P long | 5 | -14.86 | 0.929 | 40.00 | -2.97 |
| BINANCE:ADAUSDT.P short | 7 | 371.38 | 4.321 | 85.71 | 53.05 |
| BINANCE:ARBUSDT.P long | 10 | 320.32 | 2.008 | 70.00 | 32.03 |
| BINANCE:ARBUSDT.P short | 2 | 145.77 | n/a | 100.00 | 72.89 |
| BINANCE:ETHUSDT.P long | 19 | 696.89 | 1.875 | 68.42 | 36.68 |
| BINANCE:ETHUSDT.P short | 10 | 651.32 | 12.122 | 90.00 | 65.13 |
| BINANCE:SEIUSDT.P long | 8 | 231.94 | 2.093 | 75.00 | 28.99 |
| BINANCE:SEIUSDT.P short | 3 | 145.45 | n/a | 100.00 | 48.48 |

## By Side And Confluence

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long C3 | 8 | 189.44 | 2.798 | 75.00 | 23.68 |
| long C4 | 34 | 1044.85 | 1.730 | 64.71 | 30.73 |
| short C3 | 17 | 819.86 | 5.812 | 88.24 | 48.23 |
| short C4 | 5 | 494.06 | n/a | 100.00 | 98.81 |

## Short C3 By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:ADAUSDT.P | 5 | 173.79 | 2.554 | 80.00 | 34.76 |
| BINANCE:ARBUSDT.P | 1 | 49.90 | n/a | 100.00 | 49.90 |
| BINANCE:ETHUSDT.P | 8 | 450.72 | 8.697 | 87.50 | 56.34 |
| BINANCE:SEIUSDT.P | 3 | 145.45 | n/a | 100.00 | 48.48 |

## Short C3 By Strength Age

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| S0-2 | 3 | 258.51 | n/a | 100.00 | 86.17 |
| S3-6 | 4 | 199.29 | n/a | 100.00 | 49.82 |
| S7+ | 10 | 362.06 | 3.125 | 80.00 | 36.21 |

## Short C3 Delayed Slope Gate

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| outside S3-6 | 13 | 620.57 | 4.642 | 84.62 | 47.74 |
| S3-6 slope<=-0.70 | 4 | 199.29 | n/a | 100.00 | 49.82 |

## Initial Read

This is a pressure-test artifact, not a final promotion decision. Compare it against the original four-symbol Canary J basket and then run at least one high-beta/failure-control batch before tuning the threshold again.
