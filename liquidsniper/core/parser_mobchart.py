"""Parser for Mobchart Liquidity Screener Telegram payloads.

This module is intentionally pure (no DB calls) so it can be unit-tested in
isolation and reused by ingestion jobs.
"""

from __future__ import annotations

import re
from typing import Any

PREFIX_RE = re.compile(r"^(?P<venue>[A-Za-z0-9_-]+)\s+(?P<market>SPOT|FUTURES):\s*(?P<rest>.*)$")
LINE_RE = re.compile(
    r"^(?P<strength>\S+)\s+"
    r"(?P<symbol>[A-Z0-9]+)\s+"
    r"\$(?P<price>[0-9]+(?:\.[0-9]+)?(?:e[+-]?[0-9]+)?)\s+"
    r"\$(?P<size>[0-9]+(?:\.[0-9]+)?[KMB]?)\s+"
    r"(?P<distance>[0-9]+(?:\.[0-9]+)?)%\s+"
    r"(?P<side>[🔴🟢])\s+"
    r"(?P<age>.+)$"
)

SIZE_SUFFIXES = {"": 1.0, "K": 1_000.0, "M": 1_000_000.0, "B": 1_000_000_000.0}
SIDE_MAP = {
    "🔴": ("ask", "sell"),
    "🟢": ("bid", "buy"),
}


class ParseError(ValueError):
    """Raised when a line cannot be parsed into a valid signal."""


def parse_size_usd(raw: str) -> float:
    """Parse human-readable dollar size values like 339.11K or 2.66M."""
    m = re.fullmatch(r"(?P<num>[0-9]+(?:\.[0-9]+)?)(?P<sfx>[KMB]?)", raw)
    if not m:
        raise ParseError(f"invalid size: {raw}")
    num = float(m.group("num"))
    sfx = m.group("sfx")
    return num * SIZE_SUFFIXES[sfx]


def parse_age_min_seconds(age_raw: str) -> int:
    """Parse age into a minimum bound in seconds.

    Supports examples like:
    - 1h 22m
    - 13h+
    - 61h+
    - 4h 6m
    """
    s = age_raw.strip()

    h_plus = re.fullmatch(r"(?P<h>\d+)h\+", s)
    if h_plus:
        return int(h_plus.group("h")) * 3600

    hm = re.fullmatch(r"(?P<h>\d+)h(?:\s+(?P<m>\d+)m)?", s)
    if hm:
        h = int(hm.group("h"))
        m = int(hm.group("m") or 0)
        return h * 3600 + m * 60

    raise ParseError(f"invalid age: {age_raw}")


def _parse_signal_line(
    line: str,
    *,
    line_index: int,
    venue: str | None,
    market_type: str | None,
) -> dict[str, Any]:
    m = LINE_RE.match(line.strip())
    if not m:
        raise ParseError("line format mismatch")

    strength = m.group("strength")
    symbol = m.group("symbol")
    price = float(m.group("price"))
    size_usd = parse_size_usd(m.group("size"))
    distance_pct = float(m.group("distance"))
    side_emoji = m.group("side")
    age_raw = m.group("age").strip()
    age_seconds_min = parse_age_min_seconds(age_raw)

    side, liquidity_side = SIDE_MAP.get(side_emoji, ("unknown", "unknown"))

    return {
        "event_type": "liquidity_screener_alert",
        "venue": (venue or "unknown").lower(),
        "market_type": (market_type or "unknown").lower(),
        "symbol": symbol,
        "level_price": price,
        "liquidity_size_usd": size_usd,
        "distance_pct": distance_pct,
        "side_emoji_raw": side_emoji,
        "side": side,
        "liquidity_side": liquidity_side,
        "strength_emoji_raw": strength,
        "age_raw": age_raw,
        "age_seconds_min": age_seconds_min,
        "raw_text": line,
        "line_index": line_index,
    }


def parse_mobchart_message(text: str) -> list[dict[str, Any]]:
    """Parse a Mobchart Telegram message into per-line event records.

    - Multiline messages emit one record per non-empty line.
    - Venue/market context is inherited from the last prefixed line in the
      same message.
    - Malformed lines emit parse_error records; this function never raises.
    """
    results: list[dict[str, Any]] = []
    venue_ctx: str | None = None
    market_ctx: str | None = None

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i, raw_line in enumerate(lines):
        line = raw_line

        p = PREFIX_RE.match(line)
        if p:
            venue_ctx = p.group("venue")
            market_ctx = p.group("market")
            line = p.group("rest").strip()

        try:
            parsed = _parse_signal_line(
                line,
                line_index=i,
                venue=venue_ctx,
                market_type=market_ctx,
            )
            results.append(parsed)
        except Exception as exc:  # defensive by design
            results.append(
                {
                    "event_type": "parse_error",
                    "venue": (venue_ctx or "unknown").lower(),
                    "market_type": (market_ctx or "unknown").lower(),
                    "raw_text": raw_line,
                    "line_index": i,
                    "error": str(exc),
                }
            )

    return results
