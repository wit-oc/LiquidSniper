"""Minimal diagnostic Streamlit UI for hybrid analysis decisions."""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass

from liquidsniper.core.db import init_db
from liquidsniper.core.tv_artifacts import query_ui_artifact_links

try:
    import streamlit as st
except Exception:  # pragma: no cover - streamlit runtime import guard
    st = None


@dataclass(frozen=True)
class DiagnosticCard:
    """One UI row representing an analysis run + decision."""

    analysis_run_id: int
    created_ts: str
    symbol: str
    side: str
    run_mode: str
    decision: str
    would_alert: bool
    final_score: float
    pre_score: float
    zone_priority_score: float
    context_score: float
    agent_confidence_score: float
    rationale: str


def query_diagnostic_cards(
    conn: sqlite3.Connection,
    *,
    would_alert_only: bool = False,
    min_final_score: float = 0.0,
    status: str = "all",
    limit: int = 200,
) -> list[DiagnosticCard]:
    """Return candidate decision cards with debug filters."""
    where: list[str] = ["r.final_score >= ?"]
    params: list[object] = [float(min_final_score)]

    if would_alert_only:
        where.append("d.would_alert = 1")

    normalized_status = status.strip().lower()
    if normalized_status != "all":
        where.append("d.decision = ?")
        params.append(normalized_status)

    params.append(int(limit))

    sql = f"""
        SELECT
            r.id,
            r.created_ts,
            r.symbol,
            r.side,
            r.run_mode,
            d.decision,
            d.would_alert,
            COALESCE(r.final_score, 0),
            COALESCE(r.pre_score, 0),
            COALESCE(r.zone_priority_score, 0),
            COALESCE(r.context_score, 0),
            COALESCE(r.agent_confidence_score, 0),
            COALESCE(d.rationale, '')
        FROM analysis_runs r
        JOIN candidate_decisions d ON d.analysis_run_id = r.id
        WHERE {' AND '.join(where)}
        ORDER BY r.created_ts DESC, r.id DESC
        LIMIT ?;
    """

    rows = conn.execute(sql, params).fetchall()
    return [
        DiagnosticCard(
            analysis_run_id=int(row[0]),
            created_ts=str(row[1]),
            symbol=str(row[2]),
            side=str(row[3]),
            run_mode=str(row[4]),
            decision=str(row[5]),
            would_alert=bool(row[6]),
            final_score=float(row[7]),
            pre_score=float(row[8]),
            zone_priority_score=float(row[9]),
            context_score=float(row[10]),
            agent_confidence_score=float(row[11]),
            rationale=str(row[12]),
        )
        for row in rows
    ]


def _render_card_list(cards: list[DiagnosticCard]) -> None:
    st.subheader("Inbox")
    if not cards:
        st.info("No analysis runs matched current filters.")
        return

    for card in cards:
        badge = "! " if card.would_alert else ""
        st.markdown(
            f"**{badge}{card.symbol} · {card.decision} · score {card.final_score:.1f}**  "
            f"`{card.created_ts}` · `{card.side}` · `{card.run_mode}`"
        )


def _render_card_detail(conn: sqlite3.Connection, cards: list[DiagnosticCard]) -> None:
    st.subheader("Card detail")
    if not cards:
        return

    selected = st.selectbox(
        "Select analysis run",
        options=cards,
        format_func=lambda c: (
            f"#{c.analysis_run_id} {c.symbol} {c.decision} "
            f"({c.final_score:.1f})"
        ),
    )

    st.markdown("**Why this was flagged**")
    st.write(selected.rationale or "(no rationale recorded)")

    st.markdown("**Confluence breakdown**")
    st.write(
        {
            "zone_priority_score": selected.zone_priority_score,
            "context_score": selected.context_score,
            "pre_score": selected.pre_score,
            "agent_confidence_score": selected.agent_confidence_score,
            "final_score": selected.final_score,
            "decision": selected.decision,
            "would_alert": selected.would_alert,
        }
    )

    st.markdown("**Screenshot links**")
    links = query_ui_artifact_links(conn, analysis_run_id=selected.analysis_run_id)
    for timeframe, href in links.items():
        if href:
            st.markdown(f"- {timeframe}: [{href}]({href})")
        else:
            st.markdown(f"- {timeframe}: _(missing)_")


def run_app(db_path: str) -> None:
    """Entry point used by Streamlit."""
    st.set_page_config(page_title="LiquidSniper Diagnostic UI", layout="wide")
    st.title("LiquidSniper · Diagnostic UI")

    conn = init_db(db_path)
    try:
        would_alert_only = st.sidebar.checkbox("Would-alert only", value=False)
        min_final_score = st.sidebar.slider(
            "Minimum final score",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=1.0,
        )
        status = st.sidebar.selectbox(
            "Status",
            options=["all", "publish_candidate", "watch_only", "reject"],
            index=0,
        )

        cards = query_diagnostic_cards(
            conn,
            would_alert_only=would_alert_only,
            min_final_score=min_final_score,
            status=status,
        )

        _render_card_list(cards)
        st.divider()
        _render_card_detail(conn, cards)
    finally:
        conn.close()


def main() -> None:
    if st is None:
        raise RuntimeError("Streamlit is required to run the diagnostic UI.")

    db_path = os.getenv("LIQUIDSNIPER_DB_PATH", "data/liquidsniper.sqlite")
    run_app(db_path)


if __name__ == "__main__":
    main()
