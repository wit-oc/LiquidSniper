"""TradingView adapter primitives for MVP integration path.

Provides deterministic helpers for:
- parsing TradingView links
- validating webhook payload shape
- status transition safety checks
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

VALID_STATUSES = {"ok", "unavailable", "auth_required", "failed"}


@dataclass(frozen=True)
class TVLink:
    url: str
    symbol: str | None
    interval: str | None


def parse_tv_link(url: str) -> TVLink:
    parsed = urlparse(url)
    q = parse_qs(parsed.query or "")

    symbol = None
    interval = None

    if "symbol" in q and q["symbol"]:
        symbol = q["symbol"][0]
    if "interval" in q and q["interval"]:
        interval = q["interval"][0]

    # fallback: some links contain symbol-like suffixes in fragment
    if not symbol and parsed.fragment:
        frag_q = parse_qs(parsed.fragment)
        if "symbol" in frag_q and frag_q["symbol"]:
            symbol = frag_q["symbol"][0]

    return TVLink(url=url, symbol=symbol, interval=interval)


def validate_webhook_payload(payload: dict) -> tuple[bool, str | None]:
    required = ["symbol", "timeframe", "event", "price", "timestamp"]
    for k in required:
        if k not in payload:
            return False, f"missing_required_field:{k}"

    try:
        float(payload["price"])
    except Exception:
        return False, "invalid_price"

    if not str(payload["symbol"]).strip():
        return False, "empty_symbol"

    if not str(payload["timeframe"]).strip():
        return False, "empty_timeframe"

    return True, None


def valid_status_transition(current: str, nxt: str) -> bool:
    if current not in VALID_STATUSES or nxt not in VALID_STATUSES:
        return False

    # Any state can recover to ok; degraded states can switch among themselves.
    if nxt == "ok":
        return True
    if current == "ok" and nxt in {"unavailable", "auth_required", "failed"}:
        return True
    if current in {"unavailable", "auth_required", "failed"} and nxt in {"unavailable", "auth_required", "failed"}:
        return True
    return False
