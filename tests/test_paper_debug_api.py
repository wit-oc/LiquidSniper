from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from liquidsniper.debug.service import build_app


def _call(app, path: str, *, method: str = "GET", query: str = "", auth: str | None = None):
    status_headers: dict[str, object] = {}

    def start_response(status, headers):
        status_headers["status"] = status
        status_headers["headers"] = headers

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
    }
    if auth:
        environ["HTTP_AUTHORIZATION"] = auth

    body = b"".join(app(environ, start_response))
    return str(status_headers["status"]), json.loads(body.decode("utf-8"))


def _write_run(path: Path, **kw):
    payload = {
        "run_id": kw.get("run_id", "r1"),
        "timestamp": kw.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "anchor_profile_id": kw.get("anchor_profile_id", "I"),
        "strategy": kw.get("strategy"),
        "symbol": kw.get("symbol", "BTCUSDT"),
        "direction": kw.get("direction", "buy"),
        "decision_tier": kw.get("decision_tier", "publish_candidate"),
        "execution_decision": kw.get("execution_decision", "executed"),
        "proposal_decision": kw.get("proposal_decision", "accepted"),
        "score_gate_passed": kw.get("score_gate_passed", True),
        "decision_reason_codes": kw.get("decision_reason_codes", []),
        "feed_reason_codes": kw.get("feed_reason_codes", []),
        "exit_reason": kw.get("exit_reason"),
        "global_breaker": kw.get("global_breaker"),
    }
    if "test_id" in kw:
        payload["test_id"] = kw["test_id"]
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_snapshot_and_filters(monkeypatch, tmp_path: Path):
    runs = tmp_path / "paper_mvp" / "runs"
    runs.mkdir(parents=True)
    _write_run(runs / "a.json", run_id="a", anchor_profile_id="I", test_id="test-1")
    _write_run(
        runs / "b.json",
        run_id="b",
        anchor_profile_id="S",
        proposal_decision="rejected",
        execution_decision="blocked",
        decision_reason_codes=["HTF_CHOP_EXCEEDED"],
        test_id="test-2",
    )

    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(tmp_path))
    app = build_app()

    status, payload = _call(app, "/api/v1/debug/snapshot", query="strategy=swing")
    assert status.startswith("200")
    assert isinstance(payload["data"], dict)
    assert all(row["strategy"] == "swing" for row in payload["data"]["orders"])

    status2, payload2 = _call(app, "/api/v1/debug/events", query="test_id=test-2")
    assert status2.startswith("200")
    assert len(payload2["data"]) == 1
    assert payload2["data"][0]["code"] == "HTF_CHOP_EXCEEDED"


def test_snapshot_includes_breaker_visibility(monkeypatch, tmp_path: Path):
    runs = tmp_path / "paper_mvp" / "runs"
    state = tmp_path / "paper_mvp" / "state"
    runs.mkdir(parents=True)
    state.mkdir(parents=True)
    _write_run(
        runs / "trip.json",
        run_id="trip",
        strategy="intraday",
        global_breaker={"tripped": True, "trip_reason": "GLOBAL_DRAWDOWN_TRIPPED_ABSOLUTE"},
    )
    (state / "global_drawdown_breaker_state.json").write_text(
        json.dumps({"tripped": True, "trip_reason": "GLOBAL_DRAWDOWN_TRIPPED_ABSOLUTE", "trading_day": "2026-02-20"}),
        encoding="utf-8",
    )

    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(tmp_path))
    app = build_app()
    status, payload = _call(app, "/api/v1/debug/snapshot")
    assert status.startswith("200")
    assert payload["data"]["breaker"]["tripped"] is True
    events = payload["data"]["events"]
    assert any(e["event_type"] == "breaker_transition" for e in events)


def test_read_only_guard(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(tmp_path))
    app = build_app()
    status, payload = _call(app, "/api/v1/debug/orders", method="POST")
    assert status.startswith("405")
    assert payload["error"] == "READ_ONLY_MODE"


def test_pagination_and_event_retention(monkeypatch, tmp_path: Path):
    runs = tmp_path / "paper_mvp" / "runs"
    runs.mkdir(parents=True)
    now = datetime.now(timezone.utc)
    old_ts = (now - timedelta(hours=30)).isoformat()
    new_ts = (now - timedelta(hours=2)).isoformat()

    _write_run(runs / "old.json", run_id="old", timestamp=old_ts, decision_reason_codes=["OLD_EVENT"]) 
    _write_run(runs / "new1.json", run_id="new1", timestamp=new_ts, decision_reason_codes=["NEW_EVENT_1"]) 
    _write_run(runs / "new2.json", run_id="new2", timestamp=new_ts, decision_reason_codes=["NEW_EVENT_2"]) 

    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(tmp_path))
    app = build_app()

    status_o, payload_o = _call(app, "/api/v1/debug/orders", query="page_size=1&page=2")
    assert status_o.startswith("200")
    assert payload_o["meta"]["pagination"]["page"] == 2
    assert payload_o["meta"]["pagination"]["page_size"] == 1
    assert payload_o["meta"]["pagination"]["total"] >= 2
    assert len(payload_o["data"]) == 1

    status_e, payload_e = _call(app, "/api/v1/debug/events")
    assert status_e.startswith("200")
    codes = {row["code"] for row in payload_e["data"]}
    assert "NEW_EVENT_1" in codes
    assert "NEW_EVENT_2" in codes
    assert "OLD_EVENT" not in codes


def test_auth_guard_token_and_basic(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setenv("LIQUIDSNIPER_DEBUG_TOKEN", "abc123")
    app = build_app()

    status, _ = _call(app, "/api/v1/debug/orders")
    assert status.startswith("401")

    ok, _ = _call(app, "/api/v1/debug/orders", auth="Bearer abc123")
    assert ok.startswith("200")

    monkeypatch.delenv("LIQUIDSNIPER_DEBUG_TOKEN")
    monkeypatch.setenv("LIQUIDSNIPER_DEBUG_USER", "user")
    monkeypatch.setenv("LIQUIDSNIPER_DEBUG_PASS", "pass")
    app2 = build_app()
    basic = base64.b64encode(b"user:pass").decode("ascii")
    ok2, _ = _call(app2, "/api/v1/debug/orders", auth=f"Basic {basic}")
    assert ok2.startswith("200")
