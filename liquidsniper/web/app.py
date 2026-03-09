"""Streamlit UI for LiquidSniper diagnostics + SR verification."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from liquidsniper.core.db import init_db
from liquidsniper.core.sr_engine_v2 import nearest_sr_levels_v1
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
    params: list[object] = [float(min_final_score)]

    normalized_status = status.strip().lower()
    if normalized_status != "all":
        params.append(normalized_status)

    params.append(int(limit))

    sql = """
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
        WHERE r.final_score >= ?
    """

    if would_alert_only:
        sql += "\n AND d.would_alert = 1"
    if normalized_status != "all":
        sql += "\n AND d.decision = ?"

    sql += "\n ORDER BY r.created_ts DESC, r.id DESC\n LIMIT ?;"

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
    st.subheader("Diagnostic inbox")
    if not cards:
        st.info("No analysis runs matched current filters.")
        return

    total = len(cards)
    would_alert_count = sum(1 for card in cards if card.would_alert)
    st.caption(
        f"Showing {total} run(s) · would-alert candidates: {would_alert_count}"
    )

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
    ordered_timeframes = ("15m", "1h", "4h", "1D", "1W")
    for timeframe in ordered_timeframes:
        href = links.get(timeframe)
        if href:
            st.markdown(f"- {timeframe}: [{href}]({href})")
        else:
            st.markdown(f"- {timeframe}: _(missing)_")


def _query_sr_symbols(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT DISTINCT symbol FROM sr_zones ORDER BY symbol;").fetchall()
    return [str(r[0]) for r in rows]


def _query_sr_tfs(conn: sqlite3.Connection, symbol: str) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT tf FROM sr_zones WHERE symbol = ? ORDER BY tf;",
        (symbol,),
    ).fetchall()
    return [str(r[0]) for r in rows]


def _query_sr_zones(
    conn: sqlite3.Connection,
    *,
    symbol: str,
    tf: str,
    status: str,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    params: list[Any] = [symbol]
    sql = """
        SELECT
            zone_id,
            symbol,
            tf,
            zone_low,
            zone_high,
            zone_mid,
            status,
            touch_count,
            meaningful_touch_count,
            first_retest_result,
            strength_score,
            reaction_score,
            reaction_efficiency_score,
            spent_zone_penalty,
            retest_weight,
            selection_score,
            zone_width_bps,
            carry_score,
            body_respect_score,
            close_inside_rate,
            body_overlap_rate,
            wick_only_rate,
            directional_close_rate,
            counter_close_rate,
            updated_ts
        FROM sr_zones
        WHERE symbol = ?
    """

    if tf != "ALL":
        sql += " AND tf = ?"
        params.append(tf)

    if status != "all":
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY COALESCE(selection_score, strength_score, 0) DESC, updated_ts DESC LIMIT ?"
    params.append(int(limit))

    rows = conn.execute(sql, params).fetchall()
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "zone_id": r[0],
                "symbol": r[1],
                "tf": r[2],
                "zone_low": float(r[3]),
                "zone_high": float(r[4]),
                "zone_mid": float(r[5]),
                "status": r[6],
                "touch_count": int(r[7] or 0),
                "meaningful_touch_count": int(r[8] or 0),
                "first_retest_result": r[9],
                "strength_score": float(r[10] or 0.0),
                "reaction_score": float(r[11] or 0.0),
                "reaction_efficiency_score": float(r[12] or 0.0),
                "spent_zone_penalty": float(r[13] or 0.0),
                "retest_weight": float(r[14] or 0.0),
                "selection_score": float(r[15] or 0.0),
                "zone_width_bps": float(r[16] or 0.0),
                "carry_score": float(r[17] or 0.0),
                "body_respect_score": float(r[18] or 0.0),
                "close_inside_rate": float(r[19] or 0.0),
                "body_overlap_rate": float(r[20] or 0.0),
                "wick_only_rate": float(r[21] or 0.0),
                "directional_close_rate": float(r[22] or 0.0),
                "counter_close_rate": float(r[23] or 0.0),
                "updated_ts": r[24],
            }
        )
    return out


def _load_sr_bootstrap_snapshot(artifact_root: str) -> dict[str, Any] | None:
    path = Path(artifact_root) / "sr" / "bootstrap_snapshot.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_sr_run_status(artifact_root: str) -> dict[str, Any] | None:
    path = Path(artifact_root) / "sr" / "run_status.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _zone_summary_line(label: str, zone: dict[str, Any] | None) -> None:
    st.markdown(f"**{label}**")
    if not zone:
        st.write("(none)")
        return
    bounds = zone.get("bounds") or {}
    st.write(
        {
            "zone_id": zone.get("zone_id"),
            "tf": zone.get("tf"),
            "status": zone.get("status"),
            "distance_bps": zone.get("distance_bps"),
            "bounds": bounds,
            "strength": zone.get("strength"),
            "touch_count": zone.get("touch_count"),
            "meaningful_touch_count": zone.get("meaningful_touch_count"),
            "first_retest_status": zone.get("first_retest_status"),
            "diagnostics": zone.get("diagnostics"),
        }
    )


def _render_sr_verification(conn: sqlite3.Connection, artifact_root: str) -> None:
    st.subheader("S/R Verification (Python source of truth)")

    run_status = _load_sr_run_status(artifact_root)
    if run_status:
        state = str(run_status.get("state", "unknown"))
        run_id = run_status.get("run_id", "-")
        if state == "failed":
            st.error(f"SR bootstrap status: {state} (run_id={run_id}) · {run_status.get('error', '')}")
        elif state == "running":
            st.warning(f"SR bootstrap status: {state} (run_id={run_id})")
        else:
            st.caption(f"SR bootstrap status: {state} (run_id={run_id})")

    snapshot = _load_sr_bootstrap_snapshot(artifact_root)
    if snapshot:
        st.caption(f"Last bootstrap snapshot: {snapshot.get('generated_at', '-')}")

    symbols = _query_sr_symbols(conn)
    if not symbols:
        st.warning("No SR zones found in DB yet. Run: `python -m liquidsniper.ops.sr_bootstrap`." )
        return

    col_a, col_b, col_c, col_d = st.columns([1.1, 1.0, 1.0, 1.0])
    with col_a:
        symbol = st.selectbox("Symbol", options=symbols, index=0)
    with col_b:
        profile = st.selectbox("Profile", options=["S", "I", "C"], index=1)
    with col_c:
        tf_options = ["ALL"] + _query_sr_tfs(conn, symbol)
        tf = st.selectbox("TF filter", options=tf_options, index=0)
    with col_d:
        status = st.selectbox("Status", options=["confirmed", "all", "candidate", "broken", "retired"], index=0)

    default_price = 0.0
    if snapshot and isinstance(snapshot.get("symbols"), dict):
        sym_payload = snapshot["symbols"].get(symbol)
        if isinstance(sym_payload, dict):
            default_price = float(sym_payload.get("last_price") or 0.0)

    if default_price <= 0.0:
        sample = conn.execute(
            "SELECT zone_mid FROM sr_zones WHERE symbol = ? ORDER BY updated_ts DESC LIMIT 1;",
            (symbol,),
        ).fetchone()
        default_price = float(sample[0]) if sample else 0.0

    entry = st.number_input("Entry / current price", min_value=0.0, value=float(default_price), step=max(default_price * 0.001, 1.0))

    zones = _query_sr_zones(conn, symbol=symbol, tf=tf, status=status, limit=1500)
    st.caption(f"Loaded zones: {len(zones)}")
    if not zones:
        st.info("No zones matched current filters.")
        return

    nearest = nearest_sr_levels_v1(profile_id=profile, entry=float(entry), zones=zones)

    c1, c2 = st.columns(2)
    with c1:
        _zone_summary_line("Nearest support", nearest.get("nearest_support"))
        _zone_summary_line("Next support", nearest.get("next_support"))
    with c2:
        _zone_summary_line("Nearest resistance", nearest.get("nearest_resistance"))
        _zone_summary_line("Next resistance", nearest.get("next_resistance"))

    with st.expander("nearest_sr_v1 payload", expanded=False):
        st.json(nearest)

    with st.expander("Historical zones", expanded=False):
        st.dataframe(zones, use_container_width=True)


def run_app(db_path: str, artifact_root: str) -> None:
    """Entry point used by Streamlit."""
    st.set_page_config(page_title="LiquidSniper SR Verification UI", layout="wide")
    st.title("LiquidSniper · SR Verification UI")

    conn = init_db(db_path)
    try:
        tab_sr, tab_diag = st.tabs(["SR Verification", "Diagnostic Inbox"])

        with tab_sr:
            _render_sr_verification(conn, artifact_root)

        with tab_diag:
            would_alert_only = st.checkbox("Would-alert only", value=False)
            min_final_score = st.slider(
                "Minimum final score",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=1.0,
            )
            status = st.selectbox(
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
    artifact_root = os.getenv("LS_ARTIFACT_ROOT", "data/artifacts")
    run_app(db_path, artifact_root)


if __name__ == "__main__":
    main()
