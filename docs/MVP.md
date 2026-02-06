# MVP Definition (Phase 1)

## MVP objective

Create a trustworthy signal stream from Mobchart Liquidity Screener alerts delivered via Telegram.

The MVP succeeds if:
- We can reliably ingest and store alerts 24/7
- We can browse/search/export them easily
- We can start labeling and analyzing what alerts correlate with useful price action

## Inputs

- Telegram messages (Mobchart notifications)

## Outputs

- `events.jsonl` (or equivalent): append-only event log
- Viewer UI: table + filters

## Requirements

### Functional

- Ingest raw Telegram message text + timestamp
- Store message metadata (chat/message id)
- Parse basic fields when possible (symbol, side, price level)
- Expose event list in a simple UI

### Non-functional

- No secrets required
- Runs locally (laptop/server) in a container
- Crash-safe append-only writes
- Simple backup/export

## Explicit exclusions

- No trading / no order placement
- No PnL calculations (until we add enrichment)
- No strategy optimization

## Next milestone (Phase 2 preview)

- Add price-series enrichment so each event can be evaluated:
  - MFE/MAE over N-minute windows
  - slippage/fee assumptions
  - candidate TP/SL templates
