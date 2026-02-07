CREATE TABLE IF NOT EXISTS raw_telegram_messages (
    id INTEGER PRIMARY KEY,
    ts_ingested TEXT NOT NULL,
    telegram_chat_id TEXT NOT NULL,
    telegram_message_id TEXT NOT NULL,
    sender TEXT,
    text TEXT,
    raw_json TEXT,
    UNIQUE(telegram_chat_id, telegram_message_id)
);

CREATE TABLE IF NOT EXISTS signal_events (
    id INTEGER PRIMARY KEY,
    ts_alert TEXT,
    ts_ingested TEXT NOT NULL,
    venue TEXT,
    market_type TEXT,
    symbol TEXT,
    side TEXT NOT NULL DEFAULT 'unknown' CHECK (side IN ('bid', 'ask', 'unknown')),
    liquidity_side TEXT NOT NULL DEFAULT 'unknown' CHECK (liquidity_side IN ('buy', 'sell', 'unknown')),
    level_price REAL,
    liquidity_size_usd REAL,
    distance_pct REAL,
    strength_emoji_raw TEXT,
    side_emoji_raw TEXT,
    age_raw TEXT,
    age_seconds_min INTEGER,
    raw_text TEXT,
    raw_message_id INTEGER NOT NULL,
    line_index INTEGER NOT NULL,
    FOREIGN KEY(raw_message_id) REFERENCES raw_telegram_messages(id),
    UNIQUE(raw_message_id, line_index)
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('inbox', 'active', 'archived')),
    created_ts TEXT NOT NULL,
    updated_ts TEXT NOT NULL,
    last_signal_ts TEXT,
    score REAL
);

CREATE TABLE IF NOT EXISTS confluences (
    id INTEGER PRIMARY KEY,
    card_id INTEGER NOT NULL,
    ts_first_seen TEXT NOT NULL,
    ts_last_seen TEXT NOT NULL,
    venue TEXT,
    market_type TEXT,
    side TEXT,
    level_price REAL,
    liquidity_size_usd REAL,
    distance_pct REAL,
    strength_emoji_raw TEXT,
    age_raw TEXT,
    source_event_id INTEGER,
    FOREIGN KEY(card_id) REFERENCES cards(id),
    FOREIGN KEY(source_event_id) REFERENCES signal_events(id)
);

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY,
    card_id INTEGER NOT NULL UNIQUE,
    created_ts TEXT NOT NULL,
    updated_ts TEXT NOT NULL,
    entry REAL,
    stop_loss REAL,
    tp_final REAL,
    rr_best REAL,
    status TEXT NOT NULL CHECK (status IN ('planned', 'open', 'won', 'lost', 'canceled')),
    notes TEXT,
    FOREIGN KEY(card_id) REFERENCES cards(id)
);
