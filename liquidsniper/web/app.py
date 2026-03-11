"""Streamlit UI for LiquidSniper diagnostics + SR verification."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from liquidsniper.core.db import init_db
from liquidsniper.core.pair_analytics import build_pair_analytics_snapshot, load_candles_from_csv
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


def _normalize_structure_tf_key(tf: str) -> str:
    normalized = str(tf or "").strip().upper()
    if normalized in {"1D", "D", "DAILY"}:
        return "1d"
    if normalized in {"4H", "H4"}:
        return "4h"
    if normalized in {"1H", "H1"}:
        return "1h"
    if normalized in {"15M", "M15"}:
        return "15m"
    return normalized.lower()


def _find_market_structure_csv(symbol: str, tf: str) -> Path | None:
    asset = "".join(ch for ch in symbol.split("USDT")[0].lower() if ch.isalnum())
    tf_key = _normalize_structure_tf_key(tf)
    data_dir = Path(__file__).resolve().parents[2] / "IntradayTrading" / "data"
    if not data_dir.exists() or not asset:
        return None
    candidates = sorted(data_dir.glob(f"{asset}_{tf_key}_*.csv"))
    return candidates[0] if candidates else None


def _format_zone_badges(zone: dict[str, Any] | None) -> str:
    if not zone:
        return ""
    badges: list[str] = []
    kind = str(zone.get("kind") or zone.get("zone_kind") or "").strip()
    tf = str(zone.get("tf") or "").strip()
    source = str(zone.get("source_family") or "").strip()
    families = [str(item).strip() for item in (zone.get("candidate_families") or []) if str(item).strip()]
    if kind:
        badges.append(kind.upper())
    if tf:
        badges.append(tf.upper())
    if source:
        badges.append(f"SRC:{source}")
    for family in families:
        tag = f"FAM:{family}"
        if tag not in badges:
            badges.append(tag)
    return " ".join(f"[{badge}]" for badge in badges)


def _format_anchor_summary(zone: dict[str, Any] | None) -> str:
    if not zone:
        return "n/a"
    anchor = zone.get("price_anchor") if isinstance(zone.get("price_anchor"), dict) else {}
    kind = str(anchor.get("kind") or "zone_mid")
    zone_mid = anchor.get("zone_mid")
    if zone_mid is not None:
        return f"{kind} @ {float(zone_mid):,.4f}"
    return kind


def _format_zone_summary(zone: dict[str, Any] | None) -> str:
    if not zone:
        return "(none)"
    bounds = zone.get("bounds") if isinstance(zone.get("bounds"), dict) else {}
    low = bounds.get("low")
    mid = bounds.get("mid")
    high = bounds.get("high")
    distance = zone.get("distance_bps")
    selection = zone.get("selection_score")
    retest = zone.get("first_retest_status") or "n/a"
    touches = zone.get("meaningful_touch_count") if zone.get("meaningful_touch_count") is not None else zone.get("touch_count")
    span = f"{float(low):,.4f} -> {float(high):,.4f}" if low is not None and high is not None else "n/a"
    mid_text = f"{float(mid):,.4f}" if mid is not None else "n/a"
    pieces = [
        f"mid {mid_text}",
        f"band {span}",
        f"dist {float(distance):.1f}bps" if distance is not None else "dist n/a",
        f"sel {float(selection):.1f}" if selection is not None else "sel n/a",
        f"retest {retest}",
        f"touches {touches if touches is not None else 'n/a'}",
        f"anchor {_format_anchor_summary(zone)}",
    ]
    return " · ".join(pieces)


def _format_arbitration_summary(zone: dict[str, Any] | None) -> str:
    if not zone:
        return ""
    arbitration = zone.get("arbitration") if isinstance(zone.get("arbitration"), dict) else {}
    if not arbitration:
        return ""
    score = arbitration.get("score_components") if isinstance(arbitration.get("score_components"), dict) else {}
    families = ", ".join(str(item) for item in arbitration.get("families") or []) or "n/a"
    return (
        f"kept={arbitration.get('kept_zone_id') or zone.get('zone_id')} · "
        f"cluster={arbitration.get('cluster_size', 0)} · "
        f"families={families} · "
        f"base={float(score.get('winner_base_score') or 0.0):.1f} + "
        f"bonus={float(score.get('family_confluence_bonus') or 0.0):.1f} => "
        f"final={float(score.get('final_selection_score') or 0.0):.1f}"
    )


def _render_zone_block(label: str, zone: dict[str, Any] | None) -> None:
    st.markdown(f"**{label}**")
    if not zone:
        st.write("(none)")
        return
    st.caption(_format_zone_badges(zone))
    st.write(_format_zone_summary(zone))
    arbitration_summary = _format_arbitration_summary(zone)
    if arbitration_summary:
        st.caption(f"Arbitration: {arbitration_summary}")


def _build_ui_pair_analytics(symbol: str, profile: str, entry: float, zones: list[dict[str, Any]]) -> dict[str, Any]:
    requested_tfs = ("1H", "4H", "1D")
    candles_by_tf: dict[str, list[dict[str, Any]]] = {}
    availability: dict[str, dict[str, Any]] = {}
    for tf in requested_tfs:
        path = _find_market_structure_csv(symbol, tf)
        if path is None:
            availability[tf] = {
                "timeframe": tf,
                "status": "missing_source",
                "reason": "no matching candle csv found",
            }
            continue
        try:
            candles = load_candles_from_csv(path, limit=600)
        except Exception as exc:
            availability[tf] = {
                "timeframe": tf,
                "status": "load_failed",
                "reason": str(exc),
                "path": str(path),
            }
            continue
        candles_by_tf[tf] = candles
        availability[tf] = {
            "timeframe": tf,
            "status": "ready",
            "path": str(path),
            "candle_count": len(candles),
        }
    return build_pair_analytics_snapshot(
        symbol=symbol,
        profile_id=profile,
        entry=float(entry),
        zones=zones,
        candles_by_tf=candles_by_tf,
        timeframe_availability=availability,
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

    analytics = _build_ui_pair_analytics(symbol=symbol, profile=profile, entry=float(entry), zones=zones)
    sr_levels = analytics.get("sr", {}).get("nearest_levels", {})

    st.markdown("**Nearest / next ladder**")
    c1, c2 = st.columns(2)
    with c1:
        _render_zone_block("Nearest support", sr_levels.get("nearest_support"))
        _render_zone_block("Next support", sr_levels.get("next_support"))
    with c2:
        _render_zone_block("Nearest resistance", sr_levels.get("nearest_resistance"))
        _render_zone_block("Next resistance", sr_levels.get("next_resistance"))

    st.markdown("**Majors vs operational**")
    majors = analytics.get("sr", {}).get("majors", [])
    operational = analytics.get("sr", {}).get("operational", [])
    left, right = st.columns(2)
    with left:
        st.caption("Daily / major levels")
        for zone in majors[:4]:
            st.caption(_format_zone_badges(zone))
            st.write(_format_zone_summary(zone))
    with right:
        st.caption("Operational / closer-in levels")
        for zone in operational[:4]:
            st.caption(_format_zone_badges(zone))
            st.write(_format_zone_summary(zone))

    with st.expander("nearest_sr_v1 payload", expanded=False):
        st.json(nearest)

    with st.expander("Per-pair analytics contract", expanded=False):
        st.json(analytics)

    availability_rows = analytics.get("market_structure", {}).get("availability", [])
    if availability_rows:
        st.markdown("**Market structure coverage**")
        for row in availability_rows:
            tf_name = row.get("timeframe") or "?"
            status_label = row.get("status") or "unknown"
            if status_label == "ready":
                payload = analytics.get("market_structure", {}).get("timeframes", {}).get(str(tf_name).upper(), {})
                st.write(
                    f"{tf_name}: {status_label} · candles {row.get('candle_count', 0)} · "
                    f"trend {payload.get('trend') or 'n/a'} · conf {payload.get('confidence') or 'n/a'} · "
                    f"reason {payload.get('last_transition_reason') or 'n/a'}"
                )
                st.caption(
                    f"CHOCH {payload.get('active_choch_level') or 'n/a'} · "
                    f"events {payload.get('event_counts') or {}}"
                )
            else:
                st.write(f"{tf_name}: {status_label} · {row.get('reason') or row.get('path') or 'unavailable'}")

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
