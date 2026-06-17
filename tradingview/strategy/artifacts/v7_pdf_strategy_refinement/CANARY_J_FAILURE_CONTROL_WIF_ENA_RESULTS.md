# Canary J Pressure Test Results

Run directory: `tradingview/strategy/artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T03-32-06-743Z-deep-date-window-matrix`

## Harness Proof

- Status: `ok`
- Symbols: `BINANCE:WIFUSDT.P`, `BINANCE:ENAUSDT.P`
- Layout/title/date-range proof is in the harness JSON and per-symbol report text/screenshots.

## Basket

| Trades | Net USDT | Gross Profit | Gross Loss | PF | Win % | Avg USDT |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 19 | 258.39 | 781.04 | 522.65 | 1.494 | 57.89 | 13.60 |

## By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:ENAUSDT.P | 7 | 185.78 | 2.187 | 71.43 | 26.54 |
| BINANCE:WIFUSDT.P | 12 | 72.61 | 1.198 | 50.00 | 6.05 |

## By Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long | 16 | 370.03 | 2.020 | 62.50 | 23.13 |
| short | 3 | -111.64 | 0.302 | 33.33 | -37.21 |

## By Symbol And Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:ENAUSDT.P long | 5 | 243.12 | 5.780 | 80.00 | 48.62 |
| BINANCE:ENAUSDT.P short | 2 | -57.34 | 0.457 | 50.00 | -28.67 |
| BINANCE:WIFUSDT.P long | 11 | 126.91 | 1.407 | 54.55 | 11.54 |
| BINANCE:WIFUSDT.P short | 1 | -54.30 | 0.000 | 0.00 | -54.30 |

## By Side And Confluence

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long C3 | 10 | -14.18 | 0.945 | 50.00 | -1.42 |
| long C4 | 6 | 384.21 | 4.679 | 83.33 | 64.04 |
| short C3 | 2 | -5.95 | 0.890 | 50.00 | -2.97 |
| short C4 | 1 | -105.69 | 0.000 | 0.00 | -105.69 |

## Short C3 By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:ENAUSDT.P | 1 | 48.35 | n/a | 100.00 | 48.35 |
| BINANCE:WIFUSDT.P | 1 | -54.30 | 0.000 | 0.00 | -54.30 |

## Short C3 By Strength Age

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| S7+ | 2 | -5.95 | 0.890 | 50.00 | -2.97 |

## Short C3 Delayed Slope Gate

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| outside S3-6 | 2 | -5.95 | 0.890 | 50.00 | -2.97 |

## Initial Read

This is a pressure-test artifact, not a final promotion decision. Compare it against the original four-symbol Canary J basket and then run at least one high-beta/failure-control batch before tuning the threshold again.
