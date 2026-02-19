CREATE TABLE IF NOT EXISTS feed_checkpoints (
    provider_id TEXT NOT NULL,
    venue TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    last_ts_open_ms INTEGER,
    last_success_ms INTEGER,
    last_attempt_ms INTEGER,
    failure_count INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL DEFAULT 'ok',
    last_reason_code TEXT,
    trace_id TEXT,
    PRIMARY KEY (provider_id, venue, symbol, timeframe)
);

CREATE INDEX IF NOT EXISTS idx_feed_checkpoints_state
ON feed_checkpoints(state);
