from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Chartability:
    state: str  # charted_primary | supported_blofin_uncharted | unsupported_or_unknown
    normalized_symbol: str


def normalize_symbol(symbol: str) -> str:
    s = (symbol or "").upper().strip()
    if ":" in s:
        s = s.split(":", 1)[1]
    if s.endswith(".P"):
        s = s[:-2]
    return s


def _load_watchlists(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {"watchlist": [], "blofin_pairs": []}
    return json.loads(p.read_text(encoding="utf-8"))


def classify_symbol(symbol: str, watchlists_path: str | Path = "config/watchlists.json") -> Chartability:
    data = _load_watchlists(watchlists_path)
    watchlist = {normalize_symbol(x) for x in data.get("watchlist", [])}
    blofin = {normalize_symbol(x) for x in data.get("blofin_pairs", [])}

    s = normalize_symbol(symbol)
    if s in watchlist:
        return Chartability("charted_primary", s)
    if s in blofin:
        return Chartability("supported_blofin_uncharted", s)
    return Chartability("unsupported_or_unknown", s)
