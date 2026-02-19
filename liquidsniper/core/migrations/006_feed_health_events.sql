CREATE TABLE IF NOT EXISTS feed_health_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id TEXT NOT NULL,
    venue TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    state TEXT NOT NULL,
    reason_codes_json TEXT NOT NULL,
    as_of_ms INTEGER NOT NULL,
    trace_id TEXT,
    created_ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feed_health_events_lookup
ON feed_health_events(provider_id, venue, symbol, timeframe, as_of_ms DESC);
