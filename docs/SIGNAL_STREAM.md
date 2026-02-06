# Signal stream (canonical)

This doc defines the event stream produced by the Phase-1 ingestor.

## Principles

- **Append-only**: never rewrite history.
- **Two layers**:
  1) store the raw Telegram message (`RawTelegramMessage`)
  2) emit parsed, normalized events (`SignalEvent`) derived from the raw message
- **Untrusted input**: parsing must be defensive; always retain `raw_text`.

## Storage format

**JSONL** (one JSON object per line) is the default for MVP.

Suggested files:
- `data/raw_telegram_messages.jsonl`
- `data/signal_events.jsonl`

## RawTelegramMessage (MVP)

```json
{
  "kind": "raw_telegram_message",
  "source": "telegram",
  "ts_ingested": "2026-02-06T15:02:00.123Z",
  "chat_id": "<string>",
  "message_id": "<string>",
  "sender": "MobChartBot",
  "text": "<raw message text>",
  "attachments": []
}
```

## SignalEvent (MVP)

### Core fields

```json
{
  "kind": "signal_event",
  "source": "mobchart",
  "event_type": "liquidity_screener_alert",

  "ts_alert": "2026-02-06T15:02:00.123Z",
  "ts_ingested": "2026-02-06T15:02:01.456Z",

  "venue": "binance",
  "market_type": "spot",

  "symbol": "DOTUSDT",

  "liquidity_side": "sell",
  "side": "ask",

  "level_price": 1.353,
  "liquidity_size_usd": 246010,
  "distance_pct": 1.1,

  "strength_emoji_raw": "🌒",
  "side_emoji_raw": "🔴",

  "age_seconds": 46800,
  "age_raw": "13h+",

  "raw_ref": {
    "chat_id": "<string>",
    "message_id": "<string>",
    "line_index": 2
  },

  "raw_text": "🌒 DOTUSDT $1.353 $246.01K 1.1% 🔴 13h+"
}
```

### Notes

- `side`/`liquidity_side` are derived from the dot emoji:
  - `🔴` → `side=ask`, `liquidity_side=sell`
  - `🟢` → `side=bid`, `liquidity_side=buy`
- `strength_emoji_raw` is the moon phase emoji; it encodes Mobchart’s strength bucket.
- `ts_alert` is the best-effort “alert time.” If Telegram doesn’t expose an explicit timestamp in payload, use message timestamp.
- `age_raw` is preserved because `13h+` / `61h+` are not exact; `age_seconds` should reflect a minimum bound.

## Parsing multi-line messages

Mobchart may send batches:

- The first line often includes the prefix: `"<Venue> <SPOT|FUTURES>:"`
- Subsequent lines omit the prefix and should inherit `venue/market_type` within that message.

Rule:
- Always store the full raw message.
- Split on newlines.
- Emit one `SignalEvent` per non-empty line.

## Future fields (Phase 2)

Once we enrich with market data, we’ll add (separately, as derived records):
- `current_price` at `ts_alert`
- candles / returns over windows (30s, 2m, 5m, 15m)
- MFE/MAE
- volatility proxy
- candidate TP/SL templates (not execution)
