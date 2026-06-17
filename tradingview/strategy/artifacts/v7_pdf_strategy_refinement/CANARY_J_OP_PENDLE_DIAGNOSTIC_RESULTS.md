# Canary J Pressure Test Results

Run directory: `tradingview/strategy/artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T03-50-01-446Z-deep-date-window-matrix`

## Harness Proof

- Status: `ok`
- Symbols: `BINANCE:OPUSDT.P`, `BINANCE:PENDLEUSDT.P`
- Layout/title/date-range proof is in the harness JSON and per-symbol report text/screenshots.

## Basket

| Trades | Net USDT | Gross Profit | Gross Loss | PF | Win % | Avg USDT |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 32 | -605.37 | 1233.71 | 1839.08 | 0.671 | 40.63 | -18.92 |

## By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:OPUSDT.P | 14 | -147.10 | 0.794 | 42.86 | -10.51 |
| BINANCE:PENDLEUSDT.P | 18 | -458.27 | 0.592 | 38.89 | -25.46 |

## By Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long | 26 | -441.14 | 0.703 | 42.31 | -16.97 |
| short | 6 | -164.23 | 0.537 | 33.33 | -27.37 |

## By Symbol And Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:OPUSDT.P long | 10 | -184.09 | 0.672 | 40.00 | -18.41 |
| BINANCE:OPUSDT.P short | 4 | 36.99 | 1.241 | 50.00 | 9.25 |
| BINANCE:PENDLEUSDT.P long | 16 | -257.05 | 0.721 | 43.75 | -16.07 |
| BINANCE:PENDLEUSDT.P short | 2 | -201.22 | 0.000 | 0.00 | -100.61 |

## By Side And Confluence

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long C3 | 3 | -153.66 | 0.000 | 0.00 | -51.22 |
| long C4 | 21 | 16.92 | 1.016 | 52.38 | 0.81 |
| long C5 | 2 | -304.40 | 0.000 | 0.00 | -152.20 |
| short C3 | 2 | -5.22 | 0.899 | 50.00 | -2.61 |
| short C4 | 3 | -303.13 | 0.000 | 0.00 | -101.04 |
| short C5 | 1 | 144.12 | n/a | 100.00 | 144.12 |

## Short C3 By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:OPUSDT.P | 2 | -5.22 | 0.899 | 50.00 | -2.61 |

## Short C3 By Strength Age

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| S3-6 | 1 | 46.64 | n/a | 100.00 | 46.64 |
| S7+ | 1 | -51.86 | 0.000 | 0.00 | -51.86 |

## Short C3 Delayed Slope Gate

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| outside S3-6 | 1 | -51.86 | 0.000 | 0.00 | -51.86 |
| S3-6 slope<=-0.70 | 1 | 46.64 | n/a | 100.00 | 46.64 |

## Initial Read

This is a pressure-test artifact, not a final promotion decision. Compare it against the original four-symbol Canary J basket and then run at least one high-beta/failure-control batch before tuning the threshold again.
