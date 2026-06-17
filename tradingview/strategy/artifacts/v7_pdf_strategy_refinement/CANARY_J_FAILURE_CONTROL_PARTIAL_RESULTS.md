# Canary J Pressure Test Results

Run directory: `tradingview/strategy/artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T03-20-28-923Z-deep-date-window-matrix`

## Harness Proof

- Status: `failed`
- Symbols: `BINANCE:SUIUSDT.P`, `BINANCE:WIFUSDT.P`, `BINANCE:ENAUSDT.P`
- Layout/title/date-range proof is in the harness JSON and per-symbol report text/screenshots.

## Basket

| Trades | Net USDT | Gross Profit | Gross Loss | PF | Win % | Avg USDT |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 15 | -725.83 | 283.50 | 1009.33 | 0.281 | 26.67 | -48.39 |

## By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:SUIUSDT.P | 15 | -725.83 | 0.281 | 26.67 | -48.39 |

## By Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long | 11 | -521.90 | 0.314 | 27.27 | -47.45 |
| short | 4 | -203.93 | 0.181 | 25.00 | -50.98 |

## By Symbol And Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:SUIUSDT.P long | 11 | -521.90 | 0.314 | 27.27 | -47.45 |
| BINANCE:SUIUSDT.P short | 4 | -203.93 | 0.181 | 25.00 | -50.98 |

## By Side And Confluence

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long C3 | 2 | -1.79 | 0.964 | 50.00 | -0.89 |
| long C4 | 9 | -520.11 | 0.268 | 22.22 | -57.79 |
| short C3 | 3 | -57.68 | 0.438 | 33.33 | -19.23 |
| short C5 | 1 | -146.25 | 0.000 | 0.00 | -146.25 |

## Short C3 By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BINANCE:SUIUSDT.P | 3 | -57.68 | 0.438 | 33.33 | -19.23 |

## Short C3 By Strength Age

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| S7+ | 3 | -57.68 | 0.438 | 33.33 | -19.23 |

## Short C3 Delayed Slope Gate

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| outside S3-6 | 3 | -57.68 | 0.438 | 33.33 | -19.23 |

## Initial Read

This is a pressure-test artifact, not a final promotion decision. Compare it against the original four-symbol Canary J basket and then run at least one high-beta/failure-control batch before tuning the threshold again.
