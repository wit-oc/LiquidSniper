CREATE TABLE IF NOT EXISTS strategy_accounts (
    id INTEGER PRIMARY KEY,
    account_id TEXT NOT NULL,
    strategy TEXT NOT NULL CHECK (strategy IN ('scalp', 'intraday', 'swing')),
    enabled INTEGER NOT NULL DEFAULT 0 CHECK (enabled IN (0,1)),
    created_ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(account_id, strategy)
);

CREATE TABLE IF NOT EXISTS strategy_account_configs (
    id INTEGER PRIMARY KEY,
    account_id TEXT NOT NULL,
    strategy TEXT NOT NULL CHECK (strategy IN ('scalp', 'intraday', 'swing')),
    max_daily_drawdown_usd REAL,
    max_open_positions INTEGER,
    throttle_ms INTEGER,
    created_ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(account_id, strategy)
);

-- Backfill legacy single paper account as intraday-on/scalp-off/swing-off.
INSERT OR IGNORE INTO strategy_accounts(account_id, strategy, enabled)
VALUES
    ('paper_default', 'intraday', 1),
    ('paper_default', 'scalp', 0),
    ('paper_default', 'swing', 0);
