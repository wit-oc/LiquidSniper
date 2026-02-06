# MVP Template (Mobchart thresholds + workflow)

This document defines a starting **Mobchart Liquidity Screener** configuration and a lightweight workflow for evaluating signals.

## Goals

- Preserve Mobchart **100 alerts/day** budget
- Focus on Top 100 market cap coins with **USDT pairs**
- Bias toward higher-quality liquidity levels
- Capture enough metadata to evaluate TP/SL addendum analysis later

## Universe

- Use `docs/UNIVERSE.md` (Top 100 by market cap + USDT)
- Enforce upstream (Mobchart whitelist) + ingest-time safety net

## Threshold template (starting hypothesis)

These are placeholders to iterate on; the system should record the configured values alongside signals.

- Distance to current price (%): `<= 1–2%` (tune)
- Lifespan: `>= 60–120 min` (avoid newborn levels)
- Strength: `>= 80%` (or higher)
- Quantity distribution groups: `>= 6` (if exposed)
- Size ($): **>= $250k** (strict-first to preserve the 100/day cap; dial down to $150k/$100k if too quiet)
- Exclude unstable quantities: `ON`
- Estimated fill rate: prefer low fill (avoid mostly-consumed walls)
- Touches (current order): prefer low-to-moderate (avoid chewed-through levels)

We should test separate streams:
- Spot vs Futures
- Buy-side (🟢) vs Sell-side (🔴)

## What we track per signal (Phase 1)

- parsed signal fields (see `docs/SIGNAL_STREAM.md`)
- a snapshot of the template name/version used

## Human evaluation workflow (pre-automation)

For each signal you decide to review/trade (paper or live later):

1) Mark a label (see `docs/OUTCOMES.md`)
2) Add notes:
   - why you took it / skipped it
   - proposed entry/stop/TP idea
   - any regime notes (volatility, trend, news)

This creates a dataset we can later analyze:
- which template settings produced the best outcomes
- which symbols/venues are noisy
- whether TP/SL templates need adjustment
