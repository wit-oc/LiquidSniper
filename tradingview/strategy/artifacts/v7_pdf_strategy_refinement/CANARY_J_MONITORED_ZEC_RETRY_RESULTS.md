# Canary J Pressure Test Results

Run directory: `tradingview/strategy/artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T04-33-08-609Z-deep-date-window-matrix`

## Harness Proof

- Status: `ok`
- Symbols: `BLOFIN:ZECUSDT.P`
- Layout/title/date-range proof is in the harness JSON and per-symbol report text/screenshots.

## Basket

| Trades | Net USDT | Gross Profit | Gross Loss | PF | Win % | Avg USDT |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 19 | 108.77 | 917.54 | 808.77 | 1.134 | 57.89 | 5.72 |

## By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BLOFIN:ZECUSDT.P | 19 | 108.77 | 1.134 | 57.89 | 5.72 |

## By Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long | 18 | 59.96 | 1.074 | 55.56 | 3.33 |
| short | 1 | 48.81 | n/a | 100.00 | 48.81 |

## By Symbol And Side

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BLOFIN:ZECUSDT.P long | 18 | 59.96 | 1.074 | 55.56 | 3.33 |
| BLOFIN:ZECUSDT.P short | 1 | 48.81 | n/a | 100.00 | 48.81 |

## By Side And Confluence

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| long C3 | 3 | 42.29 | 1.773 | 66.67 | 14.10 |
| long C4 | 15 | 17.67 | 1.023 | 53.33 | 1.18 |
| short C3 | 1 | 48.81 | n/a | 100.00 | 48.81 |

## Short C3 By Symbol

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| BLOFIN:ZECUSDT.P | 1 | 48.81 | n/a | 100.00 | 48.81 |

## Short C3 By Strength Age

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| S7+ | 1 | 48.81 | n/a | 100.00 | 48.81 |

## Short C3 Delayed Slope Gate

| Key | Trades | Net USDT | PF | Win % | Avg USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| outside S3-6 | 1 | 48.81 | n/a | 100.00 | 48.81 |

## Initial Read

This is a pressure-test artifact, not a final promotion decision. Compare it against the original four-symbol Canary J basket and then run at least one high-beta/failure-control batch before tuning the threshold again.
