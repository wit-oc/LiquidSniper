# Canary J Pressure Test Results

Run directory: `tradingview/strategy/artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T04-17-32-227Z-deep-date-window-matrix`

## Harness Proof

- Status: `failed`
- Symbols: `BINANCE:SOLUSDT.P`, `BLOFIN:DOGEUSDT.P`, `BLOFIN:ZECUSDT.P`
- Layout/title/date-range proof is in the harness JSON and per-symbol report text/screenshots.

## Basket

| Trades | Net USDT | Gross Profit | Gross Loss | PF | Win % | Avg USDT |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 35 | 487.87 | 1989.44 | 1501.57 | 1.325 | 60.00 | 13.94 |

## By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:SOLUSDT.P | 20 | 142.84 | 1.149 | 55.00 | 7.14 |
| BLOFIN:DOGEUSDT.P | 15 | 345.03 | 1.636 | 66.67 | 23.00 |

## By Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long | 30 | 303.93 | 1.218 | 56.67 | 10.13 |
| short | 5 | 183.94 | 2.756 | 80.00 | 36.79 |

## By Symbol And Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:SOLUSDT.P long | 17 | 106.86 | 1.125 | 52.94 | 6.29 |
| BINANCE:SOLUSDT.P short | 3 | 35.98 | 1.343 | 66.67 | 11.99 |
| BLOFIN:DOGEUSDT.P long | 13 | 197.07 | 1.363 | 61.54 | 15.16 |
| BLOFIN:DOGEUSDT.P short | 2 | 147.96 | n/a | 100.00 | 73.98 |

## By Side And Confluence

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long C3 | 4 | -164.40 | 0.225 | 25.00 | -41.10 |
| long C4 | 24 | 797.20 | 1.932 | 66.67 | 33.22 |
| long C5 | 1 | -163.56 | 0.000 | 0.00 | -163.56 |
| long C6 | 1 | -165.31 | 0.000 | 0.00 | -165.31 |
| short C3 | 3 | 189.62 | n/a | 100.00 | 63.21 |
| short C4 | 2 | -5.68 | 0.946 | 50.00 | -2.84 |

## Short C3 By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:SOLUSDT.P | 2 | 140.73 | n/a | 100.00 | 70.37 |
| BLOFIN:DOGEUSDT.P | 1 | 48.89 | n/a | 100.00 | 48.89 |

## Short C3 By Strength Age

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| S0-2 | 1 | 48.89 | n/a | 100.00 | 48.89 |
| S3-6 | 2 | 140.73 | n/a | 100.00 | 70.37 |

## Short C3 Delayed Slope Gate

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| outside S3-6 | 1 | 48.89 | n/a | 100.00 | 48.89 |
| S3-6 slope<=-0.70 | 2 | 140.73 | n/a | 100.00 | 70.37 |

## Initial Read

This is a pressure-test artifact, not a final promotion decision. Compare it against the original four-symbol Canary J basket and then run at least one high-beta/failure-control batch before tuning the threshold again.
