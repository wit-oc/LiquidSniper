# Canary J Pressure Test Results

Run directory: `tradingview/strategy/artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T03-04-55-520Z-deep-date-window-matrix`

## Harness Proof

- Status: `ok`
- Symbols: `BINANCE:ARBUSDT.P`, `BINANCE:PYTHUSDT.P`, `BINANCE:SEIUSDT.P`
- Layout/title/date-range proof is in the harness JSON and per-symbol report text/screenshots.

## Basket

| Trades | Net USDT | Gross Profit | Gross Loss | PF | Win % | Avg USDT |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 32 | 672.10 | 1613.64 | 941.54 | 1.714 | 68.75 | 21.00 |

## By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:ARBUSDT.P | 12 | 466.09 | 2.466 | 75.00 | 38.84 |
| BINANCE:PYTHUSDT.P | 9 | -171.38 | 0.583 | 44.44 | -19.04 |
| BINANCE:SEIUSDT.P | 11 | 377.39 | 2.778 | 81.82 | 34.31 |

## By Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long | 27 | 380.88 | 1.405 | 62.96 | 14.11 |
| short | 5 | 291.22 | n/a | 100.00 | 58.24 |

## By Symbol And Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:ARBUSDT.P long | 10 | 320.32 | 2.008 | 70.00 | 32.03 |
| BINANCE:ARBUSDT.P short | 2 | 145.77 | n/a | 100.00 | 72.89 |
| BINANCE:PYTHUSDT.P long | 9 | -171.38 | 0.583 | 44.44 | -19.04 |
| BINANCE:SEIUSDT.P long | 8 | 231.94 | 2.093 | 75.00 | 28.99 |
| BINANCE:SEIUSDT.P short | 3 | 145.45 | n/a | 100.00 | 48.48 |

## By Side And Confluence

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long C3 | 9 | 238.91 | 3.330 | 77.78 | 26.55 |
| long C4 | 18 | 141.97 | 1.169 | 55.56 | 7.89 |
| short C3 | 4 | 195.35 | n/a | 100.00 | 48.84 |
| short C4 | 1 | 95.87 | n/a | 100.00 | 95.87 |

## Short C3 By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:ARBUSDT.P | 1 | 49.90 | n/a | 100.00 | 49.90 |
| BINANCE:SEIUSDT.P | 3 | 145.45 | n/a | 100.00 | 48.48 |

## Short C3 By Strength Age

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| S3-6 | 2 | 98.57 | n/a | 100.00 | 49.28 |
| S7+ | 2 | 96.78 | n/a | 100.00 | 48.39 |

## Short C3 Delayed Slope Gate

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| outside S3-6 | 2 | 96.78 | n/a | 100.00 | 48.39 |
| S3-6 slope<=-0.70 | 2 | 98.57 | n/a | 100.00 | 49.28 |

## Initial Read

This is a pressure-test artifact, not a final promotion decision. Compare it against the original four-symbol Canary J basket and then run at least one high-beta/failure-control batch before tuning the threshold again.
