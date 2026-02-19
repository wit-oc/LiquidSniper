"""Paper-trade dry-run harness: signal -> payload -> journal snapshot."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

from .signal_delivery import make_signal_packet, render_discord_payload, render_imessage_payload


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _f(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _tp_levels(signal_row: dict[str, Any]) -> list[float]:
    raw = signal_row.get("tp_levels")
    if isinstance(raw, list):
        levels = [_f(v) for v in raw]
        return [v for v in levels if v is not None]

    legacy = [_f(signal_row.get("tp1")), _f(signal_row.get("tp2")), _f(signal_row.get("tp3"))]
    return [v for v in legacy if v is not None]


def _tp_plan(signal_row: dict[str, Any], tp_levels: list[float]) -> list[dict[str, float]]:
    raw = signal_row.get("tp_plan")
    if isinstance(raw, list):
        plan: list[dict[str, float]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            level = _f(item.get("level"))
            size_pct = _f(item.get("size_pct"))
            if level is None or size_pct is None:
                continue
            plan.append({"level": level, "size_pct": size_pct})
        if plan:
            return plan

    if not tp_levels:
        return []

    # Default deterministic split: 40/35/25 for first 3 levels, equal-split otherwise.
    if len(tp_levels) == 1:
        splits = [1.0]
    elif len(tp_levels) == 2:
        splits = [0.5, 0.5]
    elif len(tp_levels) == 3:
        splits = [0.4, 0.35, 0.25]
    else:
        per = round(1.0 / len(tp_levels), 4)
        splits = [per] * len(tp_levels)

    return [{"level": lvl, "size_pct": splits[i]} for i, lvl in enumerate(tp_levels)]


def build_journal_entry(signal_row: dict[str, Any]) -> dict[str, Any]:
    pkt = make_signal_packet(signal_row)

    entry = _f(signal_row.get("entry"))
    stop = _f(signal_row.get("stop_loss") or signal_row.get("stop"))
    tp_levels = _tp_levels(signal_row)
    tp_plan = _tp_plan(signal_row, tp_levels)

    return {
        "ts": _utc_now(),
        "symbol": pkt.symbol,
        "decision": pkt.decision,
        "score": pkt.final_score,
        "confidence_band": pkt.confidence_band,
        "entry": entry,
        "stop_loss_initial": stop,
        "tp_levels": tp_levels,
        "tp_plan": tp_plan,
        "stop_policy": {
            "move_to_break_even_on_tp1": True,
            "break_even_price": entry,
            "post_tp1_trailing": "disabled_by_default",
        },
        "tp_events": signal_row.get("tp_events") or [],
        "exit_reason": signal_row.get("exit_reason"),
        "outcome": signal_row.get("outcome"),
        "pnl_r": _f(signal_row.get("pnl_r")),
        "pnl_pct": _f(signal_row.get("pnl_pct")),
        "max_adverse_excursion_r": _f(signal_row.get("max_adverse_excursion_r")),
        "max_favorable_excursion_r": _f(signal_row.get("max_favorable_excursion_r")),
        "discord_payload": render_discord_payload(pkt),
        "imessage_payload": render_imessage_payload(pkt),
    }


def append_journal(path: str | Path, signal_row: dict[str, Any]) -> dict[str, Any]:
    entry = build_journal_entry(signal_row)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def read_journal(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out
