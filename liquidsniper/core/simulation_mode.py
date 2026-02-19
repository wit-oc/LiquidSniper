"""Simulation-first alerting helpers for hybrid analysis runs."""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from .analysis_engine import Decision


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AlertingConfig:
    """Feature flags controlling simulation vs live alert behavior."""

    alerts_enabled: bool = False
    alerts_simulation: bool = True

    @classmethod
    def from_env(cls) -> "AlertingConfig":
        return cls(
            alerts_enabled=_env_bool("ALERTS_ENABLED", default=False),
            alerts_simulation=_env_bool("ALERTS_SIMULATION", default=True),
        )

    @property
    def run_mode(self) -> str:
        if self.alerts_enabled and not self.alerts_simulation:
            return "live"
        return "simulation"


def should_send_alert(decision: Decision, config: AlertingConfig) -> bool:
    """Gate outbound send behavior behind explicit live-enable flags."""
    return (
        decision == Decision.PUBLISH_CANDIDATE
        and config.alerts_enabled
        and not config.alerts_simulation
    )


def persist_decision(
    conn: sqlite3.Connection,
    *,
    symbol: str,
    side: str,
    zone_priority_score: float,
    context_score: float,
    pre_score: float,
    agent_confidence_score: float,
    final_score: float,
    decision: Decision,
    rationale: str,
    config: AlertingConfig,
    score_version: str = "v0",
    rulebook_ref: str = "rulebook://default/v1",
) -> int:
    """Persist run + decision in simulation or live mode.

    Returns created analysis_run_id.
    """
    now = _utc_now_iso()
    with conn:
        cur = conn.execute(
            """
            INSERT INTO analysis_runs(
                created_ts, symbol, side, zone_priority_score, context_score, pre_score,
                agent_confidence_score, final_score, score_version, rulebook_ref, run_mode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                now,
                symbol,
                side,
                float(zone_priority_score),
                float(context_score),
                float(pre_score),
                float(agent_confidence_score),
                float(final_score),
                score_version,
                rulebook_ref,
                config.run_mode,
            ),
        )
        run_id = int(cur.lastrowid)

        conn.execute(
            """
            INSERT INTO candidate_decisions(
                analysis_run_id, created_ts, decision, rationale, would_alert
            ) VALUES (?, ?, ?, ?, ?);
            """,
            (
                run_id,
                now,
                str(decision),
                rationale,
                1 if decision == Decision.PUBLISH_CANDIDATE else 0,
            ),
        )

    return run_id


def query_candidates_per_day(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    """Return publish-candidate volume grouped by UTC day."""
    rows = conn.execute(
        """
        SELECT substr(created_ts, 1, 10) AS day, COUNT(*) AS candidates
        FROM candidate_decisions
        WHERE decision = 'publish_candidate'
        GROUP BY day
        ORDER BY day DESC;
        """
    ).fetchall()
    return [(str(day), int(count)) for day, count in rows]


def query_high_priority_per_day(
    conn: sqlite3.Connection,
    *,
    final_score_threshold: float = 80.0,
) -> list[tuple[str, int]]:
    """Return high-priority publish-candidate counts grouped by UTC day."""
    rows = conn.execute(
        """
        SELECT substr(r.created_ts, 1, 10) AS day, COUNT(*) AS high_priority
        FROM analysis_runs r
        JOIN candidate_decisions d ON d.analysis_run_id = r.id
        WHERE d.decision = 'publish_candidate' AND r.final_score >= ?
        GROUP BY day
        ORDER BY day DESC;
        """,
        (float(final_score_threshold),),
    ).fetchall()
    return [(str(day), int(count)) for day, count in rows]


def query_symbol_concentration(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    """Return publish-candidate counts by symbol for concentration checks."""
    rows = conn.execute(
        """
        SELECT r.symbol, COUNT(*) AS candidates
        FROM analysis_runs r
        JOIN candidate_decisions d ON d.analysis_run_id = r.id
        WHERE d.decision = 'publish_candidate'
        GROUP BY r.symbol
        ORDER BY candidates DESC, r.symbol ASC;
        """
    ).fetchall()
    return [(str(symbol), int(count)) for symbol, count in rows]
