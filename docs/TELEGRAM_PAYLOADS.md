# Telegram payloads (Mobchart)

This document captures real-world Telegram message shapes so the ingestion + parsing logic stays grounded.

## Sample payloads

### Liquidity Screener signal (example)

Raw text (as received):

```
Binance SPOT: 🌓 GPSUSDT $0.0097 $339.11K 0.1% 🔴 1h 22m
```

Another example:

```
Binance SPOT: 🌒 BTTCUSDT $3.3e-7 $156.44K 0% 🔴 4h 6m
```

## What we can parse reliably (from these examples)

From each line we can extract:

- `venue`: `Binance`
- `market_type`: `SPOT`
- `symbol`: `GPSUSDT` / `BTTCUSDT`
- `price`: `$0.0097` / `$3.3e-7` (note: scientific notation)
- `liquidity_size_usd`: `$339.11K` / `$156.44K` (human suffix: K/M/B)
- `distance_pct`: `0.1%` / `0%` (likely “order distance to current price”)
- `status_icon`: `🔴` (meaning TBD; could be side, urgency, or other)
- `age`: `1h 22m` / `4h 6m` (likely order lifespan)
- `phase_icon`: `🌓` / `🌒` (meaning TBD; could encode strength bucket, distribution group, or bid/ask)

Notably missing (in the sample):
- explicit `side` (bid/ask)
- explicit `level_price` separate from `price`
- explicit `strength` / distribution groups

## Parsing notes

- Treat emoji as **opaque tokens** at first; store them raw.
- Keep `raw_text` always.
- Parse numeric fields with a tolerant lexer:
  - prices may be decimal or scientific notation
  - sizes may be `$<num><suffix>` where suffix ∈ {K, M, B}
  - percent may be `0%` or `0.1%`
- Parse duration as a structured object:
  - `age_seconds` derived from `Xd Yh Zm` forms

## Proposed derived `SignalEvent` (v0)

Minimum fields we can populate now:

```json
{
  "source": "mobchart",
  "event_type": "liquidity_screener_alert",
  "venue": "binance",
  "market_type": "spot",
  "symbol": "GPSUSDT",
  "price": 0.0097,
  "liquidity_size_usd": 339110,
  "distance_pct": 0.1,
  "status_emoji": "🔴",
  "phase_emoji": "🌓",
  "age_seconds": 4920,
  "raw_text": "Binance SPOT: 🌓 GPSUSDT $0.0097 $339.11K 0.1% 🔴 1h 22m"
}
```

As we get more samples, we can expand the parser and attempt to infer:
- `side` (bid/ask)
- `level_price`
- `strength`
- additional screener filter values (if Mobchart includes them)
