CREATE INDEX IF NOT EXISTS idx_raw_telegram_messages_ts_ingested
    ON raw_telegram_messages(ts_ingested);

CREATE INDEX IF NOT EXISTS idx_signal_events_symbol
    ON signal_events(symbol);

CREATE INDEX IF NOT EXISTS idx_signal_events_ts_ingested
    ON signal_events(ts_ingested);

CREATE INDEX IF NOT EXISTS idx_signal_events_raw_message_id
    ON signal_events(raw_message_id);

CREATE INDEX IF NOT EXISTS idx_confluences_card_id
    ON confluences(card_id);

CREATE INDEX IF NOT EXISTS idx_confluences_card_level
    ON confluences(card_id, venue, market_type, side, level_price);
