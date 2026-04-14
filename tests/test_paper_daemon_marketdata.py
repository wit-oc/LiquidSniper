from __future__ import annotations

import io
import json

from liquidsniper.ops import paper_daemon


class _Resp:
    def __init__(self, payload: list[list[object]], status: int = 200):
        self.status = status
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _payload(close: float) -> list[list[object]]:
    out = []
    ts = 1700000000000
    for i in range(60):
        base = close + (i * 0.1)
        out.append([ts + (i * 60000), base, base + 1.0, base - 1.0, base + 0.25, 1000.0, ts + ((i + 1) * 60000)])
    return out


def test_marketdata_candidates_default_to_perp_first(monkeypatch):
    monkeypatch.delenv("LIQUIDSNIPER_MARKETDATA_BASE", raising=False)
    monkeypatch.delenv("LIQUIDSNIPER_MARKETDATA_MODE", raising=False)
    candidates = paper_daemon._marketdata_base_candidates()
    assert candidates[0] == ("https://fapi.binance.com", "perp")
    assert candidates[1][1] == "spot"


def test_fetch_klines_prefers_perp_anchor(monkeypatch):
    calls: list[str] = []

    def fake_urlopen(req, timeout=0):
        calls.append(req.full_url)
        assert "/fapi/v1/klines" in req.full_url
        return _Resp(_payload(200.0))

    monkeypatch.setattr(paper_daemon.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.delenv("LIQUIDSNIPER_MARKETDATA_BASE", raising=False)
    monkeypatch.delenv("LIQUIDSNIPER_MARKETDATA_MODE", raising=False)

    candles = paper_daemon._fetch_klines("BTCUSDT", "1h", limit=60)
    assert candles[0]["price_anchor"] == "perp"
    assert calls and calls[0].startswith("https://fapi.binance.com/fapi/v1/klines")


def test_fetch_klines_falls_back_to_spot_when_perp_unavailable(monkeypatch):
    calls: list[str] = []

    def fake_urlopen(req, timeout=0):
        calls.append(req.full_url)
        if "/fapi/v1/klines" in req.full_url:
            raise paper_daemon.urllib.error.URLError("nope")
        return _Resp(_payload(100.0))

    monkeypatch.setattr(paper_daemon.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.delenv("LIQUIDSNIPER_MARKETDATA_BASE", raising=False)
    monkeypatch.delenv("LIQUIDSNIPER_MARKETDATA_MODE", raising=False)

    candles = paper_daemon._fetch_klines("ETHUSDT", "4h", limit=60)
    assert candles[0]["price_anchor"] == "spot"
    assert any("/fapi/v1/klines" in url for url in calls)
    assert any("/api/v3/klines" in url for url in calls)
