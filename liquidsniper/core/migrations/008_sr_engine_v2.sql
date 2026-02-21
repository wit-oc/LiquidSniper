CREATE TABLE IF NOT EXISTS sr_zones (
    zone_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    tf TEXT NOT NULL,
    zone_low REAL NOT NULL,
    zone_high REAL NOT NULL,
    zone_mid REAL NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('candidate', 'confirmed', 'broken', 'retired')),
    touch_count INTEGER NOT NULL DEFAULT 0,
    meaningful_touch_count INTEGER NOT NULL DEFAULT 0,
    first_retest_pending INTEGER NOT NULL DEFAULT 1 CHECK (first_retest_pending IN (0,1)),
    first_retest_ts TEXT,
    first_retest_result TEXT,
    strength_score REAL,
    reaction_score REAL,
    created_ts TEXT NOT NULL,
    updated_ts TEXT NOT NULL,
    source_version TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sr_zone_touches (
    touch_id TEXT PRIMARY KEY,
    zone_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    tf TEXT NOT NULL,
    candle_ts TEXT NOT NULL,
    touch_type TEXT NOT NULL,
    reaction_type TEXT,
    reaction_magnitude_atr REAL,
    is_meaningful INTEGER NOT NULL DEFAULT 0 CHECK (is_meaningful IN (0,1)),
    FOREIGN KEY(zone_id) REFERENCES sr_zones(zone_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sr_zones_symbol_tf_status
    ON sr_zones(symbol, tf, status);

CREATE INDEX IF NOT EXISTS idx_sr_zones_updated_ts
    ON sr_zones(updated_ts DESC);

CREATE INDEX IF NOT EXISTS idx_sr_zone_touches_zone_ts
    ON sr_zone_touches(zone_id, candle_ts DESC);

CREATE INDEX IF NOT EXISTS idx_sr_zone_touches_symbol_tf_ts
    ON sr_zone_touches(symbol, tf, candle_ts DESC);
