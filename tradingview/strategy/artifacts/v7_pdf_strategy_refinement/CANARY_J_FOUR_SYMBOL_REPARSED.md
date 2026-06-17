# Canary J Pressure Test Results

Run directory: `tradingview/strategy/artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T00-04-59-648Z-deep-date-window-matrix`

## Harness Proof

- Status: `ok`
- Symbols: unknown
- Layout/title/date-range proof is in the harness JSON and per-symbol report text/screenshots.

## Basket

| Trades | Net USDT | Gross Profit | Gross Loss | PF | Win % | Avg USDT |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 82 | 1962.61 | 5110.43 | 3147.82 | 1.623 | 65.85 | 23.93 |

## By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:ETHUSDT.P | 29 | 1348.21 | 2.576 | 75.86 | 46.49 |
| BINANCE:SOLUSDT.P | 20 | 142.84 | 1.149 | 55.00 | 7.14 |
| BLOFIN:DOGEUSDT.P | 15 | 345.03 | 1.636 | 66.67 | 23.00 |
| BLOFIN:ZECUSDT.P | 18 | 126.53 | 1.160 | 61.11 | 7.03 |

## By Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long | 66 | 1078.54 | 1.361 | 60.61 | 16.34 |
| short | 16 | 884.07 | 6.413 | 87.50 | 55.25 |

## By Symbol And Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:ETHUSDT.P long | 19 | 696.89 | 1.875 | 68.42 | 36.68 |
| BINANCE:ETHUSDT.P short | 10 | 651.32 | 12.122 | 90.00 | 65.13 |
| BINANCE:SOLUSDT.P long | 17 | 106.86 | 1.125 | 52.94 | 6.29 |
| BINANCE:SOLUSDT.P short | 3 | 35.98 | 1.343 | 66.67 | 11.99 |
| BLOFIN:DOGEUSDT.P long | 13 | 197.07 | 1.363 | 61.54 | 15.16 |
| BLOFIN:DOGEUSDT.P short | 2 | 147.96 | n/a | 100.00 | 73.98 |
| BLOFIN:ZECUSDT.P long | 17 | 77.72 | 1.098 | 58.82 | 4.57 |
| BLOFIN:ZECUSDT.P short | 1 | 48.81 | n/a | 100.00 | 48.81 |

## By Side And Confluence

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long C3 | 9 | -23.62 | 0.912 | 55.56 | -2.62 |
| long C4 | 55 | 1431.03 | 1.599 | 63.64 | 26.02 |
| long C5 | 1 | -163.56 | 0.000 | 0.00 | -163.56 |
| long C6 | 1 | -165.31 | 0.000 | 0.00 | -165.31 |
| short C3 | 12 | 689.15 | 12.768 | 91.67 | 57.43 |
| short C4 | 4 | 194.92 | 2.861 | 75.00 | 48.73 |

## Short C3 By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:ETHUSDT.P | 8 | 450.72 | 8.697 | 87.50 | 56.34 |
| BINANCE:SOLUSDT.P | 2 | 140.73 | n/a | 100.00 | 70.37 |
| BLOFIN:DOGEUSDT.P | 1 | 48.89 | n/a | 100.00 | 48.89 |
| BLOFIN:ZECUSDT.P | 1 | 48.81 | n/a | 100.00 | 48.81 |

## Short C3 By Strength Age

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| S0-2 | 4 | 307.40 | n/a | 100.00 | 76.85 |
| S3-6 | 3 | 193.01 | n/a | 100.00 | 64.34 |
| S7+ | 5 | 188.74 | 4.223 | 80.00 | 37.75 |

## Short C3 Delayed Slope Gate

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| outside S3-6 | 9 | 496.14 | 9.472 | 88.89 | 55.13 |
| S3-6 slope<=-0.70 | 3 | 193.01 | n/a | 100.00 | 64.34 |

## Initial Read

This is a pressure-test artifact, not a final promotion decision. Compare it against the original four-symbol Canary J basket and then run at least one high-beta/failure-control batch before tuning the threshold again.
