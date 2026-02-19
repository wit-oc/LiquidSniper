CREATE TABLE IF NOT EXISTS market_candles (
    id INTEGER PRIMARY KEY,
    provider_id TEXT NOT NULL,
    venue TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    ts_open_ms INTEGER NOT NULL,
    ts_close_ms INTEGER NOT NULL,
    open NUMERIC NOT NULL,
    high NUMERIC NOT NULL,
    low NUMERIC NOT NULL,
    close NUMERIC NOT NULL,
    volume NUMERIC NOT NULL,
    ingest_ts_ms INTEGER NOT NULL,
    dataset_version TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    UNIQUE(provider_id, venue, symbol, timeframe, ts_open_ms)
);

CREATE INDEX IF NOT EXISTS idx_market_candles_symbol_timeframe_open
    ON market_candles(symbol, timeframe, ts_open_ms);

CREATE INDEX IF NOT EXISTS idx_market_candles_trace_id
    ON market_candles(trace_id);
