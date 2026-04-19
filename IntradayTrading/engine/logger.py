from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path


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
    "dynamic_levels",
]


def _to_native(v):
    if isinstance(v, Mapping):
        return {k: _to_native(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_to_native(item) for item in v]
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
