"""Streamlit UI for LiquidSniper diagnostics + SR verification."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

_LIQUIDSNIPER_ROOT = Path(__file__).resolve().parents[2]
if str(_LIQUIDSNIPER_ROOT) not in sys.path:
    sys.path.append(str(_LIQUIDSNIPER_ROOT))

from IntradayTrading.engine.phase1_contract import (
    PHASE1_STRUCTURE_PROFILE_CANONICAL,
    PHASE1_STRUCTURE_PROFILE_LEGACY,
)
from liquidsniper.core.db import init_db
from liquidsniper.core.pair_analytics import build_pair_analytics_snapshot, load_candles_from_csv
from liquidsniper.core.surveyor_snapshot import build_surveyor_packet_snapshot
from liquidsniper.core.sr_engine_v2 import nearest_sr_levels_v1
from liquidsniper.core.sr_universe import resolve_market_structure_csv
from liquidsniper.core.tv_artifacts import query_ui_artifact_links
from liquidsniper.core.zone_engine_v3 import (
    build_base_candidates,
    build_reaction_candidates,
    build_structure_candidates,
    merge_candidate_zones,
    score_zone as score_zone_v3,
)
from liquidsniper.core.zone_selectors import select_daily_majors as select_daily_majors_v3, select_operational_zones as select_operational_zones_v3

try:
    import plotly.graph_objects as go
except Exception:  # pragma: no cover - optional dependency for audit charting
    go = None

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


_PHASE1_COMPARISON_TUNING: dict[str, dict[str, float | int | bool]] = {
    "1D": {
        "cluster_eps": 1.25,
        "reaction_atr_min": 0.60,
        "min_meaningful_touches": 5,
        "min_zone_separation_bps": 250.0,
        "max_zones": 8,
        "min_strength": 70.0,
        "require_first_retest_quality": True,
    },
    "4H": {
        "cluster_eps": 1.10,
        "reaction_atr_min": 0.45,
        "min_meaningful_touches": 4,
        "min_zone_separation_bps": 180.0,
        "max_zones": 12,
        "min_strength": 65.0,
        "require_first_retest_quality": False,
    },
}

_PHASE1_COMPARISON_CANDLE_LIMITS = {
    "1D": 20000,
    "4H": 800,
}


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


def _load_json_artifact(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_sr_bootstrap_snapshot(artifact_root: str) -> dict[str, Any] | None:
    return _load_json_artifact(Path(artifact_root) / "sr" / "bootstrap_snapshot.json")


def _load_sr_run_status(artifact_root: str) -> dict[str, Any] | None:
    return _load_json_artifact(Path(artifact_root) / "sr" / "run_status.json")


def _load_sr_shadow_bootstrap_snapshot(artifact_root: str) -> dict[str, Any] | None:
    return _load_json_artifact(Path(artifact_root) / "sr" / "shadow" / "v3" / "bootstrap_snapshot.json")


def _load_sr_shadow_run_status(artifact_root: str) -> dict[str, Any] | None:
    return _load_json_artifact(Path(artifact_root) / "sr" / "shadow" / "v3" / "run_status.json")


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
    return resolve_market_structure_csv(symbol, tf)


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


def _format_zone_ref(zone: dict[str, Any] | None) -> str:
    if not zone:
        return "(none)"
    bounds = zone.get("bounds") if isinstance(zone.get("bounds"), dict) else zone
    tf = str(zone.get("tf") or "?")
    kind = str(zone.get("kind") or zone.get("zone_kind") or "zone")
    low = bounds.get("low") if isinstance(bounds, dict) else None
    high = bounds.get("high") if isinstance(bounds, dict) else None
    mid = bounds.get("mid") if isinstance(bounds, dict) else None
    if low is not None and high is not None:
        return f"{tf} {kind} {float(low):,.1f} → {float(high):,.1f}"
    if mid is not None:
        return f"{tf} {kind} @ {float(mid):,.1f}"
    return f"{tf} {kind}"


def _format_zone_summary(zone: dict[str, Any] | None) -> str:
    if not zone:
        return "(none)"
    bounds = zone.get("bounds") if isinstance(zone.get("bounds"), dict) else {}
    low = bounds.get("low") if bounds.get("low") is not None else zone.get("zone_low")
    mid = bounds.get("mid") if bounds.get("mid") is not None else zone.get("zone_mid")
    high = bounds.get("high") if bounds.get("high") is not None else zone.get("zone_high")
    core_low = zone.get("core_low")
    core_high = zone.get("core_high")
    distance = zone.get("distance_bps")
    selection = zone.get("selection_score")
    retest = zone.get("first_retest_status") or zone.get("first_retest_result") or "n/a"
    touches = zone.get("meaningful_touch_count") if zone.get("meaningful_touch_count") is not None else zone.get("touch_count")
    span = f"{float(low):,.4f} -> {float(high):,.4f}" if low is not None and high is not None else "n/a"
    core_span = f"{float(core_low):,.4f} -> {float(core_high):,.4f}" if core_low is not None and core_high is not None else None
    mid_text = f"{float(mid):,.4f}" if mid is not None else "n/a"
    current_role = zone.get("current_role") or zone.get("kind") or zone.get("zone_kind") or "n/a"
    relative_position = zone.get("relative_position") or "unknown"
    origin_kind = zone.get("origin_kind") or zone.get("zone_kind") or "n/a"
    pieces = [
        f"mid {mid_text}",
        f"band {span}",
        f"core {core_span}" if core_span else None,
        f"role {current_role} / pos {relative_position} / origin {origin_kind}",
        f"dist {float(distance):.1f}bps" if distance is not None else "dist n/a",
        f"sel {float(selection):.1f}" if selection is not None else "sel n/a",
        f"retest {retest}",
        f"touches {touches if touches is not None else 'n/a'}",
        f"anchor {_format_anchor_summary(zone)}",
    ]
    return " · ".join(piece for piece in pieces if piece)


def _format_zone_focus_summary(zone: dict[str, Any] | None) -> str:
    if not zone:
        return "(none)"
    bounds = zone.get("bounds") if isinstance(zone.get("bounds"), dict) else {}
    macro_bounds = zone.get("macro_bounds") if isinstance(zone.get("macro_bounds"), dict) else {}
    core_bounds = zone.get("core_bounds") if isinstance(zone.get("core_bounds"), dict) else {}

    effective_low = bounds.get("low") if bounds.get("low") is not None else zone.get("zone_low")
    effective_mid = bounds.get("mid") if bounds.get("mid") is not None else zone.get("zone_mid")
    effective_high = bounds.get("high") if bounds.get("high") is not None else zone.get("zone_high")
    macro_low = macro_bounds.get("low") if macro_bounds.get("low") is not None else zone.get("zone_low")
    macro_high = macro_bounds.get("high") if macro_bounds.get("high") is not None else zone.get("zone_high")
    core_low = core_bounds.get("low") if core_bounds.get("low") is not None else zone.get("core_low")
    core_high = core_bounds.get("high") if core_bounds.get("high") is not None else zone.get("core_high")

    effective_span = f"{float(effective_low):,.4f} -> {float(effective_high):,.4f}" if effective_low is not None and effective_high is not None else "n/a"
    macro_span = f"{float(macro_low):,.4f} -> {float(macro_high):,.4f}" if macro_low is not None and macro_high is not None else None
    core_span = f"{float(core_low):,.4f} -> {float(core_high):,.4f}" if core_low is not None and core_high is not None else None
    effective_mid_text = f"{float(effective_mid):,.4f}" if effective_mid is not None else "n/a"
    distance = zone.get("distance_bps")
    selection = zone.get("selection_score")
    current_role = zone.get("current_role") or zone.get("kind") or zone.get("zone_kind") or "n/a"
    relative_position = zone.get("relative_position") or "unknown"
    origin_kind = zone.get("origin_kind") or zone.get("zone_kind") or "n/a"

    pieces = [
        f"effective band {effective_span}",
        f"effective mid {effective_mid_text}",
        f"macro context {macro_span}" if macro_span and macro_span != effective_span else None,
        f"embedded core {core_span}" if core_span and core_span != effective_span else None,
        f"role {current_role} / pos {relative_position} / origin {origin_kind}",
        f"dist {float(distance):.1f}bps" if distance is not None else "dist n/a",
        f"sel {float(selection):.1f}" if selection is not None else "sel n/a",
        f"anchor {_format_anchor_summary(zone)}",
    ]
    return " · ".join(piece for piece in pieces if piece)


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


def _render_zone_block(label: str, zone: dict[str, Any] | None, *, focus_labels: bool = False) -> None:
    st.markdown(f"**{label}**")
    if not zone:
        st.write("(none)")
        return
    st.caption(_format_zone_badges(zone))
    formatter = _format_zone_focus_summary if focus_labels else _format_zone_summary
    st.write(formatter(zone))
    arbitration_summary = _format_arbitration_summary(zone)
    if arbitration_summary:
        st.caption(f"Arbitration: {arbitration_summary}")


def _render_shadow_surface_list(label: str, zones: list[dict[str, Any]]) -> None:
    st.markdown(f"**{label}**")
    if not zones:
        st.write("(none)")
        return
    for zone in zones[:4]:
        st.caption(_format_zone_badges(zone))
        st.write(_format_zone_summary(zone))


def _authoritative_group_title(group_key: str) -> str:
    titles = {
        "below_price": "Zones below current price / support context",
        "contains_price": "Zones containing current price / active band",
        "above_price": "Zones above current price / resistance context",
    }
    return titles.get(str(group_key), str(group_key))


def _format_authoritative_zone_line(zone: dict[str, Any]) -> str:
    bounds = zone.get("bounds") if isinstance(zone.get("bounds"), dict) else {}
    core_bounds = zone.get("core_bounds") if isinstance(zone.get("core_bounds"), dict) else {}
    low = bounds.get("low")
    mid = bounds.get("mid")
    high = bounds.get("high")
    core_low = core_bounds.get("low")
    core_mid = core_bounds.get("mid")
    core_high = core_bounds.get("high")
    core_definition = zone.get("core_definition")
    current_role = zone.get("current_role") or zone.get("kind") or zone.get("zone_kind") or "n/a"
    origin_kind = zone.get("origin_kind") or zone.get("zone_kind") or "n/a"
    families = ", ".join(str(item) for item in (zone.get("candidate_families") or []) if str(item).strip()) or "n/a"
    selection = zone.get("selection_score")
    selector_reason = zone.get("selector_reason")
    selector_rank = zone.get("selector_rank")
    tf = zone.get("tf") or "?"
    cluster_member_count = zone.get("local_cluster_member_count")
    cluster_demoted = zone.get("local_cluster_demoted_ids") or []
    pocket_member_count = zone.get("daily_pocket_member_count")
    pocket_demoted = zone.get("daily_pocket_demoted_ids") or []
    display_width_floor = zone.get("display_width_floor") if isinstance(zone.get("display_width_floor"), dict) else None
    span = f"{float(low):,.4f} -> {float(high):,.4f}" if low is not None and high is not None else "n/a"
    mid_text = f"{float(mid):,.4f}" if mid is not None else "n/a"
    selection_text = f"{float(selection):.1f}" if selection is not None else "n/a"
    core_span = f"{float(core_low):,.4f} -> {float(core_high):,.4f}" if core_low is not None and core_high is not None else None
    core_mid_text = f"{float(core_mid):,.4f}" if core_mid is not None else None
    core_text = None
    if core_span:
        core_label = f"core {core_span}"
        if core_mid_text:
            core_label += f" · core mid {core_mid_text}"
        if core_definition:
            core_label += f" · core rule {core_definition}"
        core_text = core_label
    selector_text = None
    if selector_rank is not None or selector_reason:
        selector_text = f"rank {selector_rank}" if selector_rank is not None else "selector kept"
        if selector_reason:
            selector_text += f" · {selector_reason}"
    cluster_text = None
    if cluster_member_count:
        cluster_text = f"cluster members {cluster_member_count}"
        if cluster_demoted:
            cluster_text += f" · demoted {', '.join(str(item) for item in cluster_demoted[:4])}"
    pocket_text = None
    if pocket_member_count:
        pocket_text = f"daily pocket members {pocket_member_count}"
        if pocket_demoted:
            pocket_text += f" · demoted {', '.join(str(item) for item in pocket_demoted[:4])}"
    display_floor_text = None
    if display_width_floor:
        display_floor_text = f"display floor {float(display_width_floor.get('target_width_bps') or 0.0):.0f} bps"
    return (
        f"band {span} · mid {mid_text}"
        f"{' · ' + core_text if core_text else ''}"
        f" · role {current_role} · tf {tf} · families {families} · sel {selection_text}"
        f"{' · ' + selector_text if selector_text else ''}"
        f"{' · ' + cluster_text if cluster_text else ''}"
        f"{' · ' + pocket_text if pocket_text else ''}"
        f"{' · ' + display_floor_text if display_floor_text else ''}"
        f" · origin {origin_kind}"
    )


def _render_authoritative_tf_surface(label: str, payload: dict[str, Any] | None) -> None:
    st.markdown(f"**{label}**")
    if not isinstance(payload, dict):
        st.write("(none)")
        return

    selector_surface = payload.get("selector_surface") or "unknown"
    st.caption(f"Shadow authoritative source · selector surface `{selector_surface}`")

    groups = payload.get("groups") if isinstance(payload.get("groups"), dict) else {}
    for group_key in ["below_price", "contains_price", "above_price"]:
        bucket = groups.get(group_key) or []
        st.caption(f"{_authoritative_group_title(group_key)} · {len(bucket)} level(s) · sorted low → high")
        if not bucket:
            st.write("(none)")
            continue
        for zone in bucket:
            st.caption(_format_zone_badges(zone))
            st.write(_format_authoritative_zone_line(zone))


def _authoritative_view_scope_caption() -> str:
    return (
        "Authoritative = shadow-selected levels only. "
        "This tab is the operator-facing truth-check surface; baseline and debug payloads live in the other tabs."
    )



def _focused_sr_scope_caption() -> str:
    return (
        "Surveyor-style SR view = minimal operator-facing surface. "
        "Read the effective band first. Treat macro bounds as context, not as the primary reaction band."
    )



def _format_bounds_span(bounds: dict[str, Any] | None) -> str | None:
    if not isinstance(bounds, dict):
        return None
    low = bounds.get("low")
    high = bounds.get("high")
    if low is None or high is None:
        return None
    return f"{float(low):,.4f} -> {float(high):,.4f}"



def _format_sr_focus_line(zone: dict[str, Any]) -> str:
    bounds = zone.get("bounds") if isinstance(zone.get("bounds"), dict) else {}
    core_bounds = zone.get("core_bounds") if isinstance(zone.get("core_bounds"), dict) else {}
    macro_bounds = zone.get("macro_bounds") if isinstance(zone.get("macro_bounds"), dict) else {}
    current_role = zone.get("current_role") or zone.get("kind") or zone.get("zone_kind") or "n/a"
    distance = zone.get("distance_bps")
    selection = zone.get("selection_score")
    selector_reason = zone.get("selector_reason")

    effective_span = _format_bounds_span(bounds)
    core_span = _format_bounds_span(core_bounds)
    macro_span = _format_bounds_span(macro_bounds)
    if macro_span is None:
        macro_span = _format_bounds_span({"low": zone.get("zone_low"), "high": zone.get("zone_high")})

    effective_label = "core / effective" if core_span else "effective"
    pieces = [
        f"{effective_label} {effective_span or 'n/a'}",
        f"macro {macro_span}" if macro_span and macro_span != effective_span else None,
        f"role {current_role}",
        f"dist {float(distance):.1f}bps" if distance is not None else None,
        f"sel {float(selection):.1f}" if selection is not None else None,
        selector_reason,
    ]
    return " · ".join(piece for piece in pieces if piece)



def _render_sr_focus_bucket(label: str, zones: list[dict[str, Any]]) -> None:
    st.caption(f"{label} · {len(zones)} level(s)")
    if not zones:
        st.write("(none)")
        return
    for zone in zones:
        zone_ref = str(zone.get("zone_id") or zone.get("id") or "").strip()
        caption = _format_zone_badges(zone)
        if zone_ref:
            caption = f"{caption} · `{zone_ref}`" if caption else f"`{zone_ref}`"
        if caption:
            st.caption(caption)
        st.write(_format_sr_focus_line(zone))



def _count_authoritative_levels(payload: dict[str, Any] | None) -> int:
    if not isinstance(payload, dict):
        return 0
    groups = payload.get("groups") if isinstance(payload.get("groups"), dict) else {}
    return sum(len(groups.get(group_key) or []) for group_key in ["below_price", "contains_price", "above_price"])



def _render_surveyor_sr_levels_view(
    *,
    symbol: str,
    entry: float,
    shadow_snapshot: dict[str, Any] | None,
    analytics: dict[str, Any],
) -> None:
    st.markdown("**Surveyor SR Levels View**")
    st.info(_focused_sr_scope_caption())

    shadow_payload = None
    if shadow_snapshot and isinstance(shadow_snapshot.get("symbols"), dict):
        candidate = shadow_snapshot["symbols"].get(symbol)
        if isinstance(candidate, dict):
            shadow_payload = candidate

    authoritative_view = shadow_payload.get("authoritative_view") if isinstance(shadow_payload, dict) and isinstance(shadow_payload.get("authoritative_view"), dict) else {}
    timeframes = authoritative_view.get("timeframes") if isinstance(authoritative_view.get("timeframes"), dict) else {}
    daily_payload = timeframes.get("1D") if isinstance(timeframes.get("1D"), dict) else None
    h4_payload = timeframes.get("4H") if isinstance(timeframes.get("4H"), dict) else None

    metric_a, metric_b, metric_c = st.columns(3)
    metric_a.metric("Current price", f"{float(entry):,.4f}")
    metric_b.metric("1D selected levels", _count_authoritative_levels(daily_payload))
    metric_c.metric("4H selected levels", _count_authoritative_levels(h4_payload))

    st.markdown("**Surfaced ladder**")
    sr_levels = analytics.get("sr", {}).get("nearest_levels", {}) if isinstance(analytics.get("sr"), dict) else {}
    left, right = st.columns(2)
    with left:
        _render_zone_block("Nearest support", sr_levels.get("nearest_support"), focus_labels=True)
        _render_zone_block("Next support", sr_levels.get("next_support"), focus_labels=True)
    with right:
        _render_zone_block("Nearest resistance", sr_levels.get("nearest_resistance"), focus_labels=True)
        _render_zone_block("Next resistance", sr_levels.get("next_resistance"), focus_labels=True)

    st.markdown("**Authoritative surfaces**")
    st.caption(
        "This is the Surveyor seed view: simple authoritative levels first, review/debug second. "
        "For 1D, read the effective/core band first and the macro band second."
    )
    left, right = st.columns(2)
    with left:
        st.markdown("**1D Authoritative Levels**")
        if not daily_payload:
            st.write("(none)")
        else:
            groups = daily_payload.get("groups") if isinstance(daily_payload.get("groups"), dict) else {}
            _render_sr_focus_bucket("Support context (below current price)", groups.get("below_price") or [])
            _render_sr_focus_bucket("Active band (contains current price)", groups.get("contains_price") or [])
            _render_sr_focus_bucket("Resistance context (above current price)", groups.get("above_price") or [])
    with right:
        st.markdown("**4H Authoritative Levels**")
        if not h4_payload:
            st.write("(none)")
        else:
            groups = h4_payload.get("groups") if isinstance(h4_payload.get("groups"), dict) else {}
            _render_sr_focus_bucket("Support context (below current price)", groups.get("below_price") or [])
            _render_sr_focus_bucket("Active band (contains current price)", groups.get("contains_price") or [])
            _render_sr_focus_bucket("Resistance context (above current price)", groups.get("above_price") or [])



def _review_surface_scope_caption() -> str:
    return (
        "Review = comparison surface. Use this tab to compare baseline vs shadow and raw/merged candidate counts vs selected surfaces. "
        "This is explanatory, not the authoritative chart-validation view."
    )



def _debug_payload_scope_caption() -> str:
    return (
        "Debug = raw payload inspection. Use this only when you need contract-level details; it is not the primary operator review surface."
    )



def _render_authoritative_levels_view(symbol: str, shadow_snapshot: dict[str, Any] | None) -> None:
    st.markdown("**Authoritative Levels View (shadow V3)**")
    if not shadow_snapshot or not isinstance(shadow_snapshot.get("symbols"), dict):
        st.info("No shadow authoritative snapshot found yet.")
        return

    shadow_payload = shadow_snapshot["symbols"].get(symbol)
    if not isinstance(shadow_payload, dict):
        st.info("No shadow authoritative payload found for this symbol.")
        return

    authoritative_view = shadow_payload.get("authoritative_view") if isinstance(shadow_payload.get("authoritative_view"), dict) else {}
    if authoritative_view.get("contract") != "authoritative_levels_view_v1":
        st.info("Shadow authoritative view contract is not available yet.")
        return

    st.info(_authoritative_view_scope_caption())
    st.caption(
        "Source contract: shadow-selected surfaces only (`authoritative_levels_view_v1`). "
        "`current_role` is primary; `origin_kind` remains secondary/diagnostic."
    )
    left, right = st.columns(2)
    with left:
        _render_authoritative_tf_surface("1D Authoritative Levels", (authoritative_view.get("timeframes") or {}).get("1D"))
    with right:
        _render_authoritative_tf_surface("4H Authoritative Levels", (authoritative_view.get("timeframes") or {}).get("4H"))


def _render_surveyor_packet_view(packet: dict[str, Any]) -> None:
    st.markdown("**Surveyor Packet (packet-faithful audit surface)**")
    meta = packet.get("meta") if isinstance(packet.get("meta"), dict) else {}
    packet_status = str(meta.get("packet_status") or "unknown")
    if packet_status == "complete":
        st.success(f"Packet status: {packet_status}")
    elif packet_status == "partial":
        st.warning(f"Packet status: {packet_status}")
    else:
        st.error(f"Packet status: {packet_status}")

    st.caption(
        "This tab renders the unified Surveyor packet directly. "
        "If this view is wrong, the packet or feed wiring is wrong."
    )
    st.write(
        {
            "symbol": meta.get("symbol"),
            "as_of_ts": meta.get("as_of_ts"),
            "intended_direction_context": meta.get("intended_direction_context"),
            "build_mode": meta.get("build_mode"),
            "packet_id": meta.get("packet_id"),
        }
    )

    market_timeframes = packet.get("market_data", {}).get("timeframes", {}) if isinstance(packet.get("market_data"), dict) else {}
    feed_rows: list[dict[str, Any]] = []
    for tf in ["1W", "1D", "4H", "5m"]:
        row = market_timeframes.get(tf) if isinstance(market_timeframes, dict) else None
        if not isinstance(row, dict):
            continue
        feed_rows.append(
            {
                "timeframe": tf,
                "provider": row.get("feed_provider"),
                "mode": row.get("dataset_mode"),
                "freshness": row.get("freshness_state"),
                "reason": row.get("freshness_reason"),
                "bars": row.get("bar_count_available"),
                "latest_close_time": row.get("latest_close_time"),
                "latest_ingested_at": row.get("latest_ingested_at"),
                "dataset_id": row.get("dataset_id"),
            }
        )
    if feed_rows:
        st.markdown("**Feed coverage**")
        st.dataframe(feed_rows, use_container_width=True)

    structure_timeframes = packet.get("structure", {}).get("timeframes", {}) if isinstance(packet.get("structure"), dict) else {}
    structure_rows: list[dict[str, Any]] = []
    for tf in ["1W", "1D", "4H", "5m"]:
        row = structure_timeframes.get(tf) if isinstance(structure_timeframes, dict) else None
        if not isinstance(row, dict):
            continue
        structure_rows.append(
            {
                "timeframe": tf,
                "status": row.get("status"),
                "direction": row.get("regime_direction"),
                "confidence": row.get("regime_confidence"),
                "reason": row.get("regime_reason") or row.get("transition_reason"),
                "latest_bar_close": row.get("latest_bar_close"),
                "source_bar_ts": row.get("source_bar_ts"),
                "events": len(row.get("events") or []),
                "swings": len(row.get("swings") or []),
            }
        )
    if structure_rows:
        st.markdown("**Structure coverage**")
        st.dataframe(structure_rows, use_container_width=True)

    fib_contexts = packet.get("fib", {}).get("contexts_by_timeframe", {}) if isinstance(packet.get("fib"), dict) else {}
    if isinstance(fib_contexts, dict) and fib_contexts:
        fib_rows = []
        for tf in ["1W", "1D", "4H"]:
            row = fib_contexts.get(tf)
            if not isinstance(row, dict):
                continue
            fib_rows.append(
                {
                    "timeframe": tf,
                    "state": row.get("state"),
                    "direction": row.get("direction"),
                    "active": row.get("active"),
                    "band_low": row.get("levels", {}).get("band_low") if isinstance(row.get("levels"), dict) else None,
                    "band_high": row.get("levels", {}).get("band_high") if isinstance(row.get("levels"), dict) else None,
                    "source_event_id": row.get("source_event_id"),
                }
            )
        if fib_rows:
            st.markdown("**Fib context**")
            st.dataframe(fib_rows, use_container_width=True)

    dynamic_levels = packet.get("dynamic_levels", {}).get("levels", []) if isinstance(packet.get("dynamic_levels"), dict) else []
    if dynamic_levels:
        st.markdown("**Dynamic levels**")
        dynamic_rows = [
            {
                "timeframe": row.get("timeframe"),
                "level_name": row.get("level_name"),
                "available": row.get("available"),
                "level_value": row.get("level_value"),
                "price_side": row.get("price_side"),
                "zone_relation": row.get("zone_relation"),
                "timeframe_bar_ts": row.get("timeframe_bar_ts"),
                "availability_reason": row.get("availability_reason"),
            }
            for row in dynamic_levels
            if isinstance(row, dict)
        ]
        st.dataframe(dynamic_rows, use_container_width=True)

    lifecycle = packet.get("interaction_lifecycle") if isinstance(packet.get("interaction_lifecycle"), dict) else {}
    st.markdown("**Interaction lifecycle**")
    st.write(
        {
            "zone_interactions": len(lifecycle.get("zone_interactions") or []),
            "level_interactions": len(lifecycle.get("level_interactions") or []),
            "retests": len(lifecycle.get("retests") or []),
            "breaches": len(lifecycle.get("breaches") or []),
            "state_changes": len(lifecycle.get("state_changes") or []),
        }
    )

    with st.expander("Surveyor packet JSON", expanded=False):
        st.json(packet)

    with st.expander("Contract versions", expanded=False):
        st.json(packet.get("contract_versions") or {})


def _surface_group_label(position: str) -> str:
    normalized = str(position or "unknown").strip().lower()
    if normalized == "above":
        return "Zones below current price / support context"
    if normalized == "inside":
        return "Zones containing current price / active band"
    if normalized == "below":
        return "Zones above current price / resistance context"
    return "Unknown side"


def _group_zones_by_relative_position(zones: list[dict[str, Any]]) -> list[tuple[str, list[dict[str, Any]]]]:
    order = ["above", "inside", "below", "unknown"]
    grouped = {key: [] for key in order}
    extras: dict[str, list[dict[str, Any]]] = {}
    for zone in zones:
        key = str(zone.get("relative_position") or "unknown").strip().lower()
        if key in grouped:
            grouped[key].append(zone)
        else:
            extras.setdefault(key, []).append(zone)

    output: list[tuple[str, list[dict[str, Any]]]] = []
    for key in order:
        if grouped[key]:
            output.append((key, grouped[key]))
    for key in sorted(extras.keys()):
        output.append((key, extras[key]))
    return output


def _render_grouped_zone_surface(label: str, zones: list[dict[str, Any]], *, limit_per_group: int = 4) -> None:
    st.markdown(f"**{label}**")
    if not zones:
        st.write("(none)")
        return
    for position, bucket in _group_zones_by_relative_position(zones):
        st.caption(f"{_surface_group_label(position)} · {len(bucket)} zone(s)")
        for zone in bucket[:limit_per_group]:
            st.caption(_format_zone_badges(zone))
            st.write(_format_zone_summary(zone))


def _nearest_zone_diff_rows(baseline_zone: dict[str, Any] | None, shadow_zone: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    labels = {
        "zone_id": "zone_id",
        "tf": "tf",
        "distance_bps": "distance_bps",
        "selection_score": "selection_score",
        "source_family": "source_family",
    }
    for key, label in labels.items():
        baseline_value = baseline_zone.get(key) if isinstance(baseline_zone, dict) else None
        shadow_value = shadow_zone.get(key) if isinstance(shadow_zone, dict) else None
        if baseline_value != shadow_value:
            if key == "zone_id":
                baseline_value = _format_zone_ref(baseline_zone)
                shadow_value = _format_zone_ref(shadow_zone)
            rows.append({
                "field": label,
                "baseline": baseline_value,
                "shadow": shadow_value,
            })

    b_low, b_high = _zone_bounds(baseline_zone or {}) if isinstance(baseline_zone, dict) else (None, None)
    s_low, s_high = _zone_bounds(shadow_zone or {}) if isinstance(shadow_zone, dict) else (None, None)
    if (b_low, b_high) != (s_low, s_high):
        rows.append({
            "field": "bounds",
            "baseline": f"{b_low} -> {b_high}",
            "shadow": f"{s_low} -> {s_high}",
        })
    return rows


def _render_shadow_delta_tables(baseline_payload: dict[str, Any] | None, shadow_payload: dict[str, Any]) -> None:
    baseline_payload = baseline_payload or {}
    baseline_tfs = baseline_payload.get("timeframes") if isinstance(baseline_payload.get("timeframes"), dict) else {}
    shadow_tfs = shadow_payload.get("timeframes") if isinstance(shadow_payload.get("timeframes"), dict) else {}

    shadow_surfaces = shadow_payload.get("surfaces") if isinstance(shadow_payload.get("surfaces"), dict) else {}

    count_rows: list[dict[str, Any]] = [
        {
            "surface": "all selected zones",
            "baseline_raw": int(baseline_payload.get("zone_count_raw") or 0),
            "baseline_selected": int(baseline_payload.get("zone_count") or 0),
            "shadow_raw": None,
            "shadow_selected": int(shadow_payload.get("zone_count") or 0),
            "selected_delta": int(shadow_payload.get("zone_count") or 0) - int(baseline_payload.get("zone_count") or 0),
        },
        {
            "surface": "shadow daily majors",
            "baseline_raw": None,
            "baseline_selected": None,
            "shadow_raw": int((shadow_tfs.get("1D") or {}).get("candidate_counts", {}).get("merged") or 0) if isinstance(shadow_tfs.get("1D"), dict) else None,
            "shadow_selected": len(shadow_surfaces.get("majors") or []),
            "selected_delta": None,
        },
        {
            "surface": "shadow 4H operational",
            "baseline_raw": None,
            "baseline_selected": None,
            "shadow_raw": int((shadow_tfs.get("4H") or {}).get("candidate_counts", {}).get("merged") or 0) if isinstance(shadow_tfs.get("4H"), dict) else None,
            "shadow_selected": len(shadow_surfaces.get("operational") or []),
            "selected_delta": None,
        },
    ]
    for tf in sorted(set(baseline_tfs.keys()) | set(shadow_tfs.keys())):
        b_tf = baseline_tfs.get(tf) if isinstance(baseline_tfs.get(tf), dict) else {}
        s_tf = shadow_tfs.get(tf) if isinstance(shadow_tfs.get(tf), dict) else {}
        baseline_raw = b_tf.get("zones_raw")
        baseline_kept = b_tf.get("zones_kept")
        shadow_raw = (s_tf.get("candidate_counts") or {}).get("merged") if isinstance(s_tf.get("candidate_counts"), dict) else None
        shadow_kept = s_tf.get("zones_kept")
        count_rows.append(
            {
                "surface": f"{tf} raw → selected",
                "baseline_raw": int(baseline_raw) if baseline_raw is not None else None,
                "baseline_selected": int(baseline_kept) if baseline_kept is not None else None,
                "shadow_raw": int(shadow_raw) if shadow_raw is not None else None,
                "shadow_selected": int(shadow_kept) if shadow_kept is not None else None,
                "selected_delta": (int(shadow_kept) - int(baseline_kept)) if shadow_kept is not None and baseline_kept is not None else None,
            }
        )

    st.caption("Baseline vs shadow / raw vs selected")
    st.dataframe(count_rows, use_container_width=True)

    nearest_rows: list[dict[str, Any]] = []
    baseline_nearest = baseline_payload.get("nearest") if isinstance(baseline_payload.get("nearest"), dict) else {}
    shadow_nearest = shadow_payload.get("nearest") if isinstance(shadow_payload.get("nearest"), dict) else {}
    for slot in ["nearest_support", "next_support", "nearest_resistance", "next_resistance"]:
        for row in _nearest_zone_diff_rows(
            baseline_nearest.get(slot) if isinstance(baseline_nearest, dict) else None,
            shadow_nearest.get(slot) if isinstance(shadow_nearest, dict) else None,
        ):
            nearest_rows.append({"slot": slot, **row})

    if nearest_rows:
        st.caption("Nearest-four field deltas")
        st.dataframe(nearest_rows, use_container_width=True)
    else:
        st.caption("Nearest-four field deltas: none")



def _render_shadow_comparison(symbol: str, baseline_snapshot: dict[str, Any] | None, shadow_snapshot: dict[str, Any] | None) -> None:
    if not shadow_snapshot or not isinstance(shadow_snapshot.get("symbols"), dict):
        return
    shadow_payload = shadow_snapshot["symbols"].get(symbol)
    if not isinstance(shadow_payload, dict):
        return

    baseline_payload = None
    if baseline_snapshot and isinstance(baseline_snapshot.get("symbols"), dict):
        maybe = baseline_snapshot["symbols"].get(symbol)
        baseline_payload = maybe if isinstance(maybe, dict) else None

    st.markdown("**Shadow V3 comparison**")
    left, right = st.columns(2)
    with left:
        st.caption("Baseline snapshot")
        st.write(
            {
                "zone_count": baseline_payload.get("zone_count") if baseline_payload else None,
                "nearest_contract": (baseline_payload.get("nearest") or {}).get("contract") if baseline_payload else None,
            }
        )
    with right:
        st.caption("Shadow V3 snapshot")
        st.write(
            {
                "zone_count": shadow_payload.get("zone_count"),
                "nearest_contract": (shadow_payload.get("nearest") or {}).get("contract"),
            }
        )

    _render_shadow_delta_tables(baseline_payload, shadow_payload)

    c1, c2 = st.columns(2)
    with c1:
        st.caption("Shadow nearest / next ladder")
        _render_zone_block("Nearest support", (shadow_payload.get("nearest") or {}).get("nearest_support"))
        _render_zone_block("Next support", (shadow_payload.get("nearest") or {}).get("next_support"))
    with c2:
        st.caption(" ")
        _render_zone_block("Nearest resistance", (shadow_payload.get("nearest") or {}).get("nearest_resistance"))
        _render_zone_block("Next resistance", (shadow_payload.get("nearest") or {}).get("next_resistance"))

    l2, r2 = st.columns(2)
    with l2:
        _render_grouped_zone_surface("Shadow Daily majors grouped by side of price", ((shadow_payload.get("surfaces") or {}).get("majors") or []))
    with r2:
        _render_shadow_surface_list("Shadow operational (selected 4H surface)", ((shadow_payload.get("surfaces") or {}).get("operational") or []))

    with st.expander("Shadow V3 payload", expanded=False):
        st.json(shadow_payload)


def _build_phase1_profile_surface(
    *,
    symbol: str,
    tf: str,
    candles: list[dict[str, Any]],
    entry: float,
    phase1_profile: str,
) -> dict[str, Any]:
    tuning = _PHASE1_COMPARISON_TUNING.get(str(tf).upper())
    if tuning is None:
        return {"timeframe": tf, "profile": phase1_profile, "status": "unsupported_tf"}

    candidate_kwargs = {
        "cluster_eps": tuning["cluster_eps"],
        "reaction_atr_min": tuning["reaction_atr_min"],
        "min_meaningful_touches": tuning["min_meaningful_touches"],
    }
    structure = build_structure_candidates(symbol, tf, candles, phase1_profile=phase1_profile, **candidate_kwargs)
    base = build_base_candidates(symbol, tf, candles, **candidate_kwargs)
    reaction = build_reaction_candidates(symbol, tf, candles, **candidate_kwargs)
    merged = merge_candidate_zones(structure, base, reaction)
    scored = [score_zone_v3(zone, last_price=float(entry)) for zone in merged]

    if str(tf).upper() == "1D":
        selected = select_daily_majors_v3(
            scored,
            min_strength=float(tuning["min_strength"]),
            min_zone_separation_bps=float(tuning["min_zone_separation_bps"]),
            max_zones=int(tuning["max_zones"]),
            strict_retest_quality=bool(tuning["require_first_retest_quality"]),
            reference_price=float(entry),
        )
    else:
        selected = select_operational_zones_v3(
            scored,
            min_strength=float(tuning["min_strength"]),
            min_zone_separation_bps=float(tuning["min_zone_separation_bps"]),
            max_zones=int(tuning["max_zones"]),
        )

    return {
        "timeframe": tf,
        "profile": phase1_profile,
        "structure_candidates": structure,
        "base_candidates": base,
        "reaction_candidates": reaction,
        "merged_candidates": merged,
        "selected": selected,
        "counts": {
            "structure": len(structure),
            "base": len(base),
            "reaction": len(reaction),
            "merged": len(merged),
            "selected": len(selected),
        },
    }


def _build_phase1_zone_surface_comparison(symbol: str, entry: float) -> dict[str, Any]:
    out: dict[str, Any] = {"contract": "phase1_zone_surface_comparison_v1", "timeframes": {}}
    for tf in ["1D", "4H"]:
        path = _find_market_structure_csv(symbol, tf)
        if path is None or not path.exists():
            out["timeframes"][tf] = {"status": "missing_source", "path": str(path) if path else None}
            continue
        candle_limit = int(_PHASE1_COMPARISON_CANDLE_LIMITS.get(str(tf).upper(), 800))
        candles = load_candles_from_csv(path, limit=candle_limit)
        legacy = _build_phase1_profile_surface(
            symbol=symbol,
            tf=tf,
            candles=candles,
            entry=entry,
            phase1_profile=PHASE1_STRUCTURE_PROFILE_LEGACY,
        )
        canonical = _build_phase1_profile_surface(
            symbol=symbol,
            tf=tf,
            candles=candles,
            entry=entry,
            phase1_profile=PHASE1_STRUCTURE_PROFILE_CANONICAL,
        )
        out["timeframes"][tf] = {
            "status": "ok",
            "path": str(path),
            "candle_count": len(candles),
            "lookback_contract": "shadow_bootstrap_equivalent_v1",
            "legacy": legacy,
            "canonical": canonical,
        }
    return out


def _phase1_surface_count_rows(comparison: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tf, payload in (comparison.get("timeframes") or {}).items():
        if not isinstance(payload, dict) or payload.get("status") != "ok":
            continue
        legacy = payload.get("legacy") if isinstance(payload.get("legacy"), dict) else {}
        canonical = payload.get("canonical") if isinstance(payload.get("canonical"), dict) else {}
        legacy_counts = legacy.get("counts") if isinstance(legacy.get("counts"), dict) else {}
        canonical_counts = canonical.get("counts") if isinstance(canonical.get("counts"), dict) else {}
        for key in ["structure", "base", "reaction", "merged", "selected"]:
            rows.append(
                {
                    "tf": tf,
                    "metric": key,
                    "legacy": legacy_counts.get(key),
                    "canonical": canonical_counts.get(key),
                    "delta": (int(canonical_counts.get(key) or 0) - int(legacy_counts.get(key) or 0)),
                }
            )
    return rows


def _phase1_selected_zone_delta_rows(comparison: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tf, payload in (comparison.get("timeframes") or {}).items():
        if not isinstance(payload, dict) or payload.get("status") != "ok":
            continue
        legacy = payload.get("legacy") if isinstance(payload.get("legacy"), dict) else {}
        canonical = payload.get("canonical") if isinstance(payload.get("canonical"), dict) else {}
        legacy_ids = {str(z.get("zone_id") or "") for z in (legacy.get("selected") or []) if str(z.get("zone_id") or "")}
        canonical_ids = {str(z.get("zone_id") or "") for z in (canonical.get("selected") or []) if str(z.get("zone_id") or "")}
        for zone_id in sorted(legacy_ids - canonical_ids):
            rows.append({"tf": tf, "change": "removed_in_canonical", "zone_id": zone_id})
        for zone_id in sorted(canonical_ids - legacy_ids):
            rows.append({"tf": tf, "change": "added_in_canonical", "zone_id": zone_id})
    return rows


def _render_phase1_surface_comparison(comparison: dict[str, Any]) -> None:
    st.markdown("**Phase 1 contract comparison on SR surfaces**")
    st.caption("Legacy = pre-unification BoS 0.20 / CHoCH 0.15. Canonical = unified 0.15 / 0.15 contract. This recomputes SR surfaces using the shadow-equivalent lookback horizon, full 1D history and 800 bars on 4H, so the comparison matches the authoritative shadow selector more honestly.")

    count_rows = _phase1_surface_count_rows(comparison)
    if count_rows:
        st.dataframe(count_rows, use_container_width=True)
    zone_delta_rows = _phase1_selected_zone_delta_rows(comparison)
    if zone_delta_rows:
        st.caption("Selected-zone id deltas")
        st.dataframe(zone_delta_rows, use_container_width=True)
    else:
        st.caption("Selected-zone id deltas: none")

    for tf, payload in (comparison.get("timeframes") or {}).items():
        st.markdown(f"**{tf} before vs after**")
        if not isinstance(payload, dict) or payload.get("status") != "ok":
            st.info(f"{tf}: {payload.get('status') if isinstance(payload, dict) else 'unavailable'}")
            continue
        st.caption(f"Source: {payload.get('path')} · candles {payload.get('candle_count', 'n/a')} · lookback {payload.get('lookback_contract') or 'n/a'}")
        legacy = payload.get("legacy") if isinstance(payload.get("legacy"), dict) else {}
        canonical = payload.get("canonical") if isinstance(payload.get("canonical"), dict) else {}

        left, right = st.columns(2)
        with left:
            st.caption("Before, legacy structure contract")
            if str(tf).upper() == "1D":
                _render_grouped_zone_surface("Legacy selected surface", legacy.get("selected") or [])
            else:
                _render_shadow_surface_list("Legacy selected surface", legacy.get("selected") or [])
        with right:
            st.caption("After, canonical unified contract")
            if str(tf).upper() == "1D":
                _render_grouped_zone_surface("Canonical selected surface", canonical.get("selected") or [])
            else:
                _render_shadow_surface_list("Canonical selected surface", canonical.get("selected") or [])


def _zone_bounds(zone: dict[str, Any]) -> tuple[float | None, float | None]:
    bounds = zone.get("bounds") if isinstance(zone.get("bounds"), dict) else zone
    low = bounds.get("low") if isinstance(bounds, dict) else None
    high = bounds.get("high") if isinstance(bounds, dict) else None
    try:
        return (float(low), float(high)) if low is not None and high is not None else (None, None)
    except (TypeError, ValueError):
        return None, None


def _build_audit_chart(symbol: str, candles: list[dict[str, Any]], entry: float, zones: list[dict[str, Any]], highlighted_ids: set[str] | None = None):
    if go is None or not candles:
        return None
    highlighted_ids = highlighted_ids or set()
    x = [row.get("timestamp") for row in candles]
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=x,
            open=[row.get("open") for row in candles],
            high=[row.get("high") for row in candles],
            low=[row.get("low") for row in candles],
            close=[row.get("close") for row in candles],
            name=symbol,
        )
    )
    fig.add_hline(
        y=float(entry),
        line_dash="dash",
        line_color="#f59e0b",
        annotation_text=f"current {float(entry):,.4f}",
        annotation_position="top left",
    )
    for zone in zones:
        low, high = _zone_bounds(zone)
        if low is None or high is None:
            continue
        zone_id = str(zone.get("zone_id") or "")
        is_highlighted = zone_id in highlighted_ids
        is_support = str(zone.get("kind") or zone.get("zone_kind") or "").lower() == "support"
        fill = "rgba(34,197,94,0.22)" if is_support else "rgba(239,68,68,0.22)"
        line = "rgba(34,197,94,0.90)" if is_support else "rgba(239,68,68,0.90)"
        fig.add_hrect(
            y0=low,
            y1=high,
            line_width=2 if is_highlighted else 1,
            fillcolor=fill,
            line_color=line,
            opacity=0.45 if is_highlighted else 0.18,
            annotation_text=f"{zone.get('tf')} {zone.get('kind') or zone.get('zone_kind') or ''} {zone.get('selection_score') or zone.get('strength') or zone.get('strength_score') or ''}",
            annotation_position="top left",
        )
    fig.update_layout(
        height=650,
        xaxis_rangeslider_visible=False,
        margin={"l": 8, "r": 8, "t": 32, "b": 8},
        legend={"orientation": "h"},
    )
    return fig


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

    shadow_run_status = _load_sr_shadow_run_status(artifact_root)
    if shadow_run_status:
        shadow_state = str(shadow_run_status.get("state", "unknown"))
        shadow_run_id = shadow_run_status.get("run_id", "-")
        if shadow_state == "failed":
            st.error(f"SR shadow status: {shadow_state} (run_id={shadow_run_id}) · {shadow_run_status.get('error', '')}")
        elif shadow_state == "running":
            st.warning(f"SR shadow status: {shadow_state} (run_id={shadow_run_id})")
        else:
            st.caption(f"SR shadow status: {shadow_state} (run_id={shadow_run_id})")

    snapshot = _load_sr_bootstrap_snapshot(artifact_root)
    shadow_snapshot = _load_sr_shadow_bootstrap_snapshot(artifact_root)
    if snapshot:
        st.caption(f"Last bootstrap snapshot: {snapshot.get('generated_at', '-')}")
    if shadow_snapshot:
        st.caption(f"Last shadow snapshot: {shadow_snapshot.get('generated_at', '-')}")

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
    phase1_zone_comparison = _build_phase1_zone_surface_comparison(symbol=symbol, entry=float(entry))
    shadow_payload = shadow_snapshot.get("symbols", {}).get(symbol) if isinstance(shadow_snapshot, dict) else None
    authoritative_view = shadow_payload.get("authoritative_view") if isinstance(shadow_payload, dict) else None
    authoritative_ladders = shadow_payload.get("nearest") if isinstance(shadow_payload, dict) else None
    surveyor_packet = build_surveyor_packet_snapshot(
        conn,
        symbol=symbol,
        authoritative_view=authoritative_view if isinstance(authoritative_view, dict) else None,
        ladders=authoritative_ladders if isinstance(authoritative_ladders, dict) else None,
    )

    chart_tf = st.selectbox("Audit chart TF", options=["4H", "1D"], index=0)
    chart_path = _find_market_structure_csv(symbol, chart_tf)
    if chart_path and chart_path.exists():
        chart_candles = load_candles_from_csv(chart_path, limit=220)
        highlight_ids = {
            str(zone.get("zone_id") or "")
            for zone in [
                sr_levels.get("nearest_support"),
                sr_levels.get("next_support"),
                sr_levels.get("nearest_resistance"),
                sr_levels.get("next_resistance"),
            ]
            if isinstance(zone, dict)
        }
        chart_zones = [z for z in zones if str(z.get("tf") or "").upper() == chart_tf.upper()]
        chart = _build_audit_chart(symbol, chart_candles, float(entry), chart_zones, highlighted_ids=highlight_ids)
        if chart is not None:
            st.plotly_chart(chart, use_container_width=True)
            st.caption(f"Chart source: {chart_path}")
        else:
            st.info("Plotly is declared for this UI, but it is not installed in the current runtime yet.")
    else:
        st.info(f"No canonical {chart_tf} flat file found for {symbol}.")

    packet_tab, focused_tab, authoritative_tab, review_tab, debug_tab = st.tabs([
        "Surveyor Packet",
        "Surveyor SR Levels",
        "Authoritative Levels View (shadow-selected)",
        "Review Surfaces (baseline ↔ shadow)",
        "Debug Payloads (raw contracts)",
    ])

    with packet_tab:
        _render_surveyor_packet_view(surveyor_packet)

    with focused_tab:
        _render_surveyor_sr_levels_view(
            symbol=symbol,
            entry=float(entry),
            shadow_snapshot=shadow_snapshot,
            analytics=analytics,
        )

    with authoritative_tab:
        _render_authoritative_levels_view(symbol=symbol, shadow_snapshot=shadow_snapshot)

    with review_tab:
        st.info(_review_surface_scope_caption())
        st.markdown("**Nearest / next ladder**")
        c1, c2 = st.columns(2)
        with c1:
            _render_zone_block("Nearest support", sr_levels.get("nearest_support"))
            _render_zone_block("Next support", sr_levels.get("next_support"))
        with c2:
            _render_zone_block("Nearest resistance", sr_levels.get("nearest_resistance"))
            _render_zone_block("Next resistance", sr_levels.get("next_resistance"))

        st.markdown("**Review surfaces**")
        majors = analytics.get("sr", {}).get("majors", [])
        operational = analytics.get("sr", {}).get("operational", [])
        left, right = st.columns(2)
        with left:
            _render_grouped_zone_surface("Daily majors grouped by side of price", majors)
        with right:
            _render_shadow_surface_list("Operational / selected 4H surface", operational)

        _render_shadow_comparison(symbol=symbol, baseline_snapshot=snapshot, shadow_snapshot=shadow_snapshot)
        _render_phase1_surface_comparison(phase1_zone_comparison)

    with debug_tab:
        st.info(_debug_payload_scope_caption())
        with st.expander("nearest_sr_v1 payload", expanded=False):
            st.json(nearest)

        with st.expander("Per-pair analytics contract", expanded=False):
            st.json(analytics)

        with st.expander("Surveyor packet", expanded=False):
            st.json(surveyor_packet)

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

        structure_comparisons = analytics.get("market_structure", {}).get("comparisons", {})
        if isinstance(structure_comparisons, dict) and structure_comparisons:
            st.markdown("**Market structure before vs after**")
            for tf_name in sorted(structure_comparisons.keys()):
                payload = structure_comparisons.get(tf_name) if isinstance(structure_comparisons.get(tf_name), dict) else {}
                st.write(f"{tf_name}: changed = {bool(payload.get('changed'))}")
                field_diffs = payload.get("field_diffs") if isinstance(payload.get("field_diffs"), list) else []
                event_diffs = payload.get("event_count_diffs") if isinstance(payload.get("event_count_diffs"), list) else []
                if field_diffs:
                    st.caption(f"{tf_name} field deltas")
                    st.dataframe(field_diffs, use_container_width=True)
                if event_diffs:
                    st.caption(f"{tf_name} event count deltas")
                    st.dataframe(event_diffs, use_container_width=True)
                if not field_diffs and not event_diffs:
                    st.caption(f"{tf_name}: no structure-state deltas")

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


def _resolve_repo_path(path_value: str) -> str:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = _LIQUIDSNIPER_ROOT / path
    return str(path)


def main() -> None:
    if st is None:
        raise RuntimeError("Streamlit is required to run the diagnostic UI.")

    db_path = _resolve_repo_path(os.getenv("LIQUIDSNIPER_DB_PATH", "data/liquidsniper.sqlite"))
    artifact_root = _resolve_repo_path(os.getenv("LS_ARTIFACT_ROOT", "data/artifacts"))
    run_app(db_path, artifact_root)


if __name__ == "__main__":
    main()
