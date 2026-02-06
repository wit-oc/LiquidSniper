# Telegram payloads (Mobchart)

This document captures real-world Telegram message shapes so the ingestion + parsing logic stays grounded.

## Sample payloads

### Liquidity Screener signal (single-line message)

Raw text (as received):

```
Binance SPOT: 🌓 GPSUSDT $0.0097 $339.11K 0.1% 🔴 1h 22m
```

Another example:

```
Binance SPOT: 🌒 BTTCUSDT $3.3e-7 $156.44K 0% 🔴 4h 6m
```

### Liquidity Screener signal (multi-line/batch message)

Example raw text (as received):

```
Binance FUTURES: 🌒 DYDXUSDT $0.115 $216.54K 1.8% 🔴 2h 21m
🌒 DOTUSDT $1.354 $263.68K 1.2% 🔴 13h+
🌒 DOTUSDT $1.353 $246.01K 1.1% 🔴 13h+
🌒 DOGEUSDT $0.09766 $2.66M 1.6% 🔴 3h 2m
🌒 CRVUSDT $0.252 $176.37K 2% 🔴 14h+
🌓 CRVUSDT $0.251 $325.02K 1.6% 🔴 13h+
🌒 CRVUSDT $0.25 $235.96K 1.2% 🔴 2h 5m
🌕 ALGOUSDT $0.0975 $118.44K 1.2% 🔴 3h 3m
🌔 HANAUSDT $0.0355 $81.01K 1.3% 🟢 3h 40m
```

Interpretation (per Mobchart UI + user observation):
- First line includes `venue` + `market_type`
- Subsequent lines omit the prefix but share the same venue/market context

## What we can parse reliably (from these examples)

From each line we can extract:

- `venue`: `Binance`
- `market_type`: `SPOT` or `FUTURES`
- `symbol`: e.g. `GPSUSDT`, `BTTCUSDT`, `DOTUSDT`
- `level_price`: e.g. `$0.0097`, `$3.3e-7` (note: scientific notation)
- `liquidity_size_usd`: e.g. `$339.11K`, `$2.66M` (human suffix: K/M/B)
- `distance_pct`: e.g. `0.1%`, `0%`, `1.8%` (distance from current price)
- `side`: derived from dot color
  - `🔴` → `ask` (sell-side liquidity)
  - `🟢` → `bid` (buy-side liquidity)
- `age`: e.g. `1h 22m`, `14h+`, `61h+` (how long the order has existed)
- `strength_bucket`: derived from moon phase emoji (Mobchart strength representation)
  - store the raw emoji and (optionally) map to an ordered bucket

### Notes on multi-line messages

Mobchart can send **multiple lines in a single Telegram message** (a batch). The ingestor should:
- store the raw message as-is
- split into lines and emit one `SignalEvent` per line

Notably still missing in the sample:
- order quantity in coins (not present in Telegram payload; visible in Mobchart UI)
- distribution/updates/touches fields (visible in UI, not in Telegram payload)

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
  "side": "ask",
  "level_price": 0.0097,
  "liquidity_size_usd": 339110,
  "distance_pct": 0.1,
  "side_emoji_raw": "🔴",
  "strength_emoji_raw": "🌓",
  "age_seconds": 4920,
  "raw_text": "Binance SPOT: 🌓 GPSUSDT $0.0097 $339.11K 0.1% 🔴 1h 22m"
}
```

As we get more samples, we can expand the parser and attempt to infer:
- `side` (bid/ask)
- `level_price`
- `strength`
- additional screener filter values (if Mobchart includes them)
