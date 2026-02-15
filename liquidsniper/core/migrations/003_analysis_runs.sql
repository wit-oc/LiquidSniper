CREATE TABLE IF NOT EXISTS analysis_runs (
    id INTEGER PRIMARY KEY,
    created_ts TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL DEFAULT 'unknown' CHECK (side IN ('bid', 'ask', 'unknown')),
    zone_priority_score REAL NOT NULL,
    context_score REAL,
    pre_score REAL,
    agent_confidence_score REAL,
    final_score REAL,
    score_version TEXT,
    rulebook_ref TEXT,
    run_mode TEXT NOT NULL DEFAULT 'simulation' CHECK (run_mode IN ('simulation', 'live'))
);

CREATE TABLE IF NOT EXISTS candidate_decisions (
    id INTEGER PRIMARY KEY,
    analysis_run_id INTEGER NOT NULL UNIQUE,
    created_ts TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('publish_candidate', 'watch_only', 'reject')),
    rationale TEXT,
    would_alert INTEGER NOT NULL DEFAULT 0 CHECK (would_alert IN (0, 1)),
    FOREIGN KEY(analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS screenshot_artifacts (
    id INTEGER PRIMARY KEY,
    analysis_run_id INTEGER NOT NULL,
    timeframe TEXT NOT NULL,
    captured_ts TEXT NOT NULL,
    source_chart_url TEXT,
    artifact_path TEXT NOT NULL,
    artifact_hash TEXT,
    FOREIGN KEY(analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_symbol_created
    ON analysis_runs(symbol, created_ts);

CREATE INDEX IF NOT EXISTS idx_candidate_decisions_decision
    ON candidate_decisions(decision);

CREATE INDEX IF NOT EXISTS idx_screenshot_artifacts_run_id
    ON screenshot_artifacts(analysis_run_id);
