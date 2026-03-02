from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping


EVENT_KEYS = [
    "index",
    "timestamp",
    "symbol",
    "tf",
    "structure_bias",
    "zone_id",
    "zone_kind",
    "zone_touched",
    "reclaim_confirmed",
    "filters_passed",
    "at_risk_count",
    "breaker_open",
    "action",
    "reason",
]


def _to_native(v):
    if hasattr(v, "item"):
        try:
            return v.item()
        except Exception:
            return v
    return v


def normalize_event(event: Mapping) -> dict:
    return {k: _to_native(event.get(k)) for k in EVENT_KEYS}


def write_jsonl(path: str | Path, events: Iterable[Mapping]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(normalize_event(e), separators=(",", ":"), sort_keys=False) + "\n")
