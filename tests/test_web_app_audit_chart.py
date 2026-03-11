from __future__ import annotations

from liquidsniper.web.app import _build_audit_chart


def test_build_audit_chart_returns_none_without_plotly(monkeypatch) -> None:
    monkeypatch.setattr("liquidsniper.web.app.go", None)
    chart = _build_audit_chart(
        "BTCUSDT",
        [{"timestamp": "t1", "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5}],
        1.5,
        [],
    )
    assert chart is None
