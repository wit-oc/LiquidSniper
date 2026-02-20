from __future__ import annotations

import base64
import json
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
        "timestamp": kw.get("timestamp", "2026-02-20T00:00:00+00:00"),
        "anchor_profile_id": kw.get("anchor_profile_id", "I"),
        "symbol": kw.get("symbol", "BTCUSDT"),
        "direction": kw.get("direction", "buy"),
        "decision_tier": kw.get("decision_tier", "publish_candidate"),
        "execution_decision": kw.get("execution_decision", "executed"),
        "proposal_decision": kw.get("proposal_decision", "accepted"),
        "score_gate_passed": kw.get("score_gate_passed", True),
        "decision_reason_codes": kw.get("decision_reason_codes", []),
        "feed_reason_codes": kw.get("feed_reason_codes", []),
        "exit_reason": kw.get("exit_reason"),
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


def test_read_only_guard(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(tmp_path))
    app = build_app()
    status, payload = _call(app, "/api/v1/debug/orders", method="POST")
    assert status.startswith("405")
    assert payload["error"] == "READ_ONLY_MODE"


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
