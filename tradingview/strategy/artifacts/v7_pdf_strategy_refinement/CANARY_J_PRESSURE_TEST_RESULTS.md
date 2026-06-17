# Canary J Pressure Test Results

Run directory: `tradingview/strategy/artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T01-49-46-255Z-deep-date-window-matrix`

## Harness Proof

- Status: `ok`
- Symbols: `BINANCE:ADAUSDT.P`, `BINANCE:LINKUSDT.P`, `BINANCE:XRPUSDT.P`
- Layout/title/date-range proof is in the harness JSON and per-symbol report text/screenshots.

## Basket

| Trades | Net USDT | Gross Profit | Gross Loss | PF | Win % | Avg USDT |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 43 | -614.94 | 1621.42 | 2236.36 | 0.725 | 39.53 | -14.30 |

## By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:ADAUSDT.P | 12 | 356.52 | 2.111 | 66.67 | 29.71 |
| BINANCE:LINKUSDT.P | 16 | -744.05 | 0.269 | 18.75 | -46.50 |
| BINANCE:XRPUSDT.P | 15 | -227.41 | 0.747 | 40.00 | -15.16 |

## By Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long | 32 | -824.21 | 0.570 | 31.25 | -25.76 |
| short | 11 | 209.27 | 1.655 | 63.64 | 19.02 |

## By Symbol And Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:ADAUSDT.P long | 5 | -14.86 | 0.929 | 40.00 | -2.97 |
| BINANCE:ADAUSDT.P short | 7 | 371.38 | 4.321 | 85.71 | 53.05 |
| BINANCE:LINKUSDT.P long | 13 | -536.32 | 0.338 | 23.08 | -41.26 |
| BINANCE:LINKUSDT.P short | 3 | -207.73 | 0.000 | 0.00 | -69.24 |
| BINANCE:XRPUSDT.P long | 14 | -273.03 | 0.696 | 35.71 | -19.50 |
| BINANCE:XRPUSDT.P short | 1 | 45.62 | n/a | 100.00 | 45.62 |

## By Side And Confluence

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long C3 | 11 | -281.93 | 0.320 | 18.18 | -25.63 |
| long C4 | 19 | -530.42 | 0.606 | 36.84 | -27.92 |
| long C5 | 2 | -11.86 | 0.924 | 50.00 | -5.93 |
| short C3 | 9 | 11.68 | 1.037 | 55.56 | 1.30 |
| short C4 | 2 | 197.59 | n/a | 100.00 | 98.80 |

## Short C3 By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:ADAUSDT.P | 5 | 173.79 | 2.554 | 80.00 | 34.76 |
| BINANCE:LINKUSDT.P | 3 | -207.73 | 0.000 | 0.00 | -69.24 |
| BINANCE:XRPUSDT.P | 1 | 45.62 | n/a | 100.00 | 45.62 |

## Short C3 By Strength Age

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| S3-6 | 3 | -106.85 | 0.312 | 33.33 | -35.62 |
| S7+ | 6 | 118.53 | 1.722 | 66.67 | 19.75 |

## Short C3 Delayed Slope Gate

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| outside S3-6 | 6 | 118.53 | 1.722 | 66.67 | 19.75 |
| S3-6 slope<=-0.70 | 3 | -106.85 | 0.312 | 33.33 | -35.62 |

## Initial Read

This is a pressure-test artifact, not a final promotion decision. Compare it against the original four-symbol Canary J basket and then run at least one high-beta/failure-control batch before tuning the threshold again.
