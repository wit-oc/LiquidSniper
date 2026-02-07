# Spec 04 — Mobchart Payload Parsing

## Goal

Parse Mobchart Liquidity Screener Telegram payloads (single-line and multi-line batch) into normalized fields.

## Supported inputs

### Single line

Example:
- `Binance SPOT: 🌓 GPSUSDT $0.0097 $339.11K 0.1% 🔴 1h 22m`

### Multi-line batch

Example:
- First line includes prefix: `Binance FUTURES:`
- Subsequent lines omit prefix but share venue/market context.

## Output fields (per line)

- `venue` (lowercased)
- `market_type` (spot|futures)
- `symbol` (raw, e.g. `DOTUSDT`)
- `level_price` (float)
- `liquidity_size_usd` (float in USD)
- `distance_pct` (float)
- `side_emoji_raw` (`🔴`|`🟢`|unknown)
- `side` (ask|bid|unknown)
- `liquidity_side` (sell|buy|unknown)
- `strength_emoji_raw` (moon emoji)
- `age_raw` (e.g. `13h+`)
- `age_seconds_min` (minimum bound)

## Parsing rules

- Split message by newline; trim; skip empty lines.
- Maintain message-level context:
  - If a line matches `^(<venue>)\s+(SPOT|FUTURES):` it sets the context.
  - If a line lacks venue/market prefix, inherit from last seen within the message.
- Side mapping:
  - `🔴` → `ask` / `sell`
  - `🟢` → `bid` / `buy`

## Error handling

- Never crash ingestion.
- If a line fails parsing:
  - store as `signal_event` with `event_type=parse_error` OR store parse_error separately
  - always keep `raw_text`

## Acceptance criteria

- Parser can handle the samples in `docs/TELEGRAM_PAYLOADS.md`.
- Parser returns structured data for >= 95% of lines in a typical day.
