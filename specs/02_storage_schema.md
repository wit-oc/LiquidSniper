# Spec 02 — Storage Schema (SQLite)

## Goal

Define the SQLite schema to support:
- immutable ingest history (raw + parsed)
- mutable card workflow (inbox/active/archive)
- manual trade tracking

## DB location

- Default path: `/data/liquidsniper.sqlite`

## Versioning

- Table: `schema_migrations(version TEXT PRIMARY KEY, applied_ts TEXT)`

## Tables

### `raw_telegram_messages` (append-only)

Fields:
- `id` INTEGER PK
- `ts_ingested` TEXT (ISO)
- `telegram_chat_id` TEXT
- `telegram_message_id` TEXT
- `sender` TEXT
- `text` TEXT
- `raw_json` TEXT (optional: dump of Telethon message)

Indexes:
- `(telegram_chat_id, telegram_message_id)` unique
- `ts_ingested`

### `signal_events` (append-only)

Fields:
- `id` INTEGER PK
- `ts_alert` TEXT (ISO, best effort)
- `ts_ingested` TEXT (ISO)
- `venue` TEXT
- `market_type` TEXT
- `symbol` TEXT
- `side` TEXT (bid|ask|unknown)
- `liquidity_side` TEXT (buy|sell|unknown)
- `level_price` REAL
- `liquidity_size_usd` REAL
- `distance_pct` REAL
- `strength_emoji_raw` TEXT
- `side_emoji_raw` TEXT
- `age_raw` TEXT
- `age_seconds_min` INTEGER
- `raw_text` TEXT
- `raw_message_id` INTEGER FK → raw_telegram_messages(id)
- `line_index` INTEGER (for multi-line messages)

Indexes:
- `symbol`
- `ts_ingested`
- `raw_message_id`

### `cards` (mutable)

One row per symbol.

Fields:
- `id` INTEGER PK
- `symbol` TEXT UNIQUE
- `status` TEXT (inbox|active|archived)
- `created_ts` TEXT
- `updated_ts` TEXT
- `last_signal_ts` TEXT
- `score` REAL (nullable; placeholder)

### `confluences` (append-only-ish)

We can treat confluences as append-only rows (never rewrite), but may later dedupe.

Fields:
- `id` INTEGER PK
- `card_id` INTEGER FK → cards(id)
- `ts_first_seen` TEXT
- `ts_last_seen` TEXT
- `venue` TEXT
- `market_type` TEXT
- `side` TEXT
- `level_price` REAL
- `liquidity_size_usd` REAL
- `distance_pct` REAL
- `strength_emoji_raw` TEXT
- `age_raw` TEXT
- `source_event_id` INTEGER FK → signal_events(id)

Indexes:
- `card_id`
- `(card_id, venue, market_type, side, level_price)` (optional unique if we want)

### `trades` (mutable)

Fields:
- `id` INTEGER PK
- `card_id` INTEGER UNIQUE FK → cards(id)
- `created_ts` TEXT
- `updated_ts` TEXT
- `entry` REAL (nullable)
- `stop_loss` REAL (nullable)
- `tp_final` REAL (nullable)
- `rr_best` REAL (nullable)
- `status` TEXT (planned|open|won|lost|canceled)
- `notes` TEXT

## Acceptance criteria

- Schema supports:
  - storing every raw message
  - storing 1+ signal events per message
  - grouping to symbol cards
  - moving cards across statuses
  - storing trade fields
