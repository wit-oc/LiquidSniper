"""Paper-trade dry-run harness: signal -> payload -> journal snapshot."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

from .signal_delivery import make_signal_packet, render_discord_payload, render_imessage_payload


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_journal_entry(signal_row: dict[str, Any]) -> dict[str, Any]:
    pkt = make_signal_packet(signal_row)
    return {
        "ts": _utc_now(),
        "symbol": pkt.symbol,
        "decision": pkt.decision,
        "score": pkt.final_score,
        "confidence_band": pkt.confidence_band,
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
