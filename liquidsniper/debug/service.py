from __future__ import annotations

import base64
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs

from .contracts import STRATEGY_BY_PROFILE


def _json_response(start_response: Callable[..., Any], status: str, payload: dict[str, Any]) -> list[bytes]:
    body = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
    start_response(status, [("Content-Type", "application/json"), ("Content-Length", str(len(body)))])
    return [body]


def _parse_filters(query: str) -> dict[str, Any]:
    params = parse_qs(query, keep_blank_values=False)
    limit = 200
    if "limit" in params:
        try:
            limit = max(1, min(1000, int(params["limit"][0])))
        except (TypeError, ValueError):
            limit = 200
    strategy = params.get("strategy", [None])[0]
    run_id = params.get("run_id", [None])[0]
    test_id = params.get("test_id", [None])[0]
    return {
        "strategy": strategy if strategy in {"scalp", "intraday", "swing"} else None,
        "run_id": run_id or None,
        "test_id": test_id or None,
        "limit": limit,
    }


def _artifact_root() -> Path:
    raw = os.getenv("LS_ARTIFACT_ROOT") or os.getenv("LIQUIDSNIPER_ARTIFACT_ROOT") or "artifacts"
    return Path(raw)


def _load_runs() -> list[dict[str, Any]]:
    runs_dir = _artifact_root() / "paper_mvp" / "runs"
    if not runs_dir.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(runs_dir.glob("*.json"), reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        payload["_source_path"] = str(path)
        out.append(payload)
    return out


def _strategy_for_run(run: dict[str, Any]) -> tuple[str, str]:
    profile_id = str(run.get("anchor_profile_id") or "I").upper()
    return STRATEGY_BY_PROFILE.get(profile_id, "intraday"), profile_id


def _test_id_for_run(run: dict[str, Any]) -> str | None:
    if isinstance(run.get("test_id"), str) and run.get("test_id"):
        return str(run["test_id"])
    trade_intent = run.get("trade_intent") if isinstance(run.get("trade_intent"), dict) else {}
    test_id = trade_intent.get("test_id")
    return str(test_id) if isinstance(test_id, str) and test_id else None


def _apply_filters(runs: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for run in runs:
        strategy, _ = _strategy_for_run(run)
        if filters["strategy"] and strategy != filters["strategy"]:
            continue
        if filters["run_id"] and str(run.get("run_id") or "") != filters["run_id"]:
            continue
        if filters["test_id"] and _test_id_for_run(run) != filters["test_id"]:
            continue
        out.append(run)
        if len(out) >= int(filters["limit"]):
            break
    return out


def _build_orders(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in runs:
        strategy, profile_id = _strategy_for_run(run)
        rows.append(
            {
                "run_id": run.get("run_id"),
                "timestamp": run.get("timestamp"),
                "strategy": strategy,
                "profile_id": profile_id,
                "symbol": run.get("symbol"),
                "side": run.get("direction"),
                "decision_tier": run.get("decision_tier"),
                "execution_decision": run.get("execution_decision"),
                "proposal_decision": run.get("proposal_decision"),
                "test_id": _test_id_for_run(run),
            }
        )
    return rows


def _build_positions(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    open_by_symbol: dict[str, dict[str, Any]] = {}
    for run in runs:
        if run.get("execution_decision") != "executed":
            continue
        if run.get("exit_reason"):
            continue
        symbol = str(run.get("symbol") or "")
        if not symbol:
            continue
        strategy, profile_id = _strategy_for_run(run)
        open_by_symbol[symbol] = {
            "strategy": strategy,
            "profile_id": profile_id,
            "symbol": symbol,
            "side": run.get("direction"),
            "entry": run.get("entry"),
            "stop_loss_initial": run.get("stop_loss_initial"),
            "risk_usd": run.get("risk_usd"),
            "run_id": run.get("run_id"),
            "timestamp": run.get("timestamp"),
        }
    return list(open_by_symbol.values())


def _build_events(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for run in runs:
        strategy, profile_id = _strategy_for_run(run)
        gate_passed = bool(run.get("score_gate_passed"))
        symbol = run.get("symbol")
        base = {
            "run_id": run.get("run_id"),
            "timestamp": run.get("timestamp"),
            "strategy": strategy,
            "profile_id": profile_id,
            "symbol": symbol,
            "gate_passed": gate_passed,
            "test_id": _test_id_for_run(run),
        }
        for code in run.get("decision_reason_codes") or []:
            out.append({**base, "event_type": "decision_reason", "code": code})
        for code in run.get("feed_reason_codes") or []:
            out.append({**base, "event_type": "feed_reason", "code": code})
    return out


def _build_strategy_summaries(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "strategy": "",
        "profile_id": "",
        "runs_total": 0,
        "executed_total": 0,
        "rejected_total": 0,
        "open_positions": 0,
        "latest_run_ts": None,
    })
    open_positions = _build_positions(runs)
    open_by_strategy: dict[str, int] = defaultdict(int)
    for row in open_positions:
        open_by_strategy[str(row["strategy"])] += 1

    for run in runs:
        strategy, profile_id = _strategy_for_run(run)
        b = buckets[strategy]
        b["strategy"] = strategy
        b["profile_id"] = profile_id
        b["runs_total"] += 1
        if run.get("execution_decision") == "executed":
            b["executed_total"] += 1
        if run.get("proposal_decision") == "rejected":
            b["rejected_total"] += 1
        ts = run.get("timestamp")
        if ts and (b["latest_run_ts"] is None or str(ts) > str(b["latest_run_ts"])):
            b["latest_run_ts"] = ts

    for strategy, count in open_by_strategy.items():
        buckets[strategy]["open_positions"] = count

    return sorted(buckets.values(), key=lambda x: str(x.get("strategy")))


def _authorized(environ: dict[str, Any]) -> bool:
    token = os.getenv("LIQUIDSNIPER_DEBUG_TOKEN", "").strip()
    user = os.getenv("LIQUIDSNIPER_DEBUG_USER", "").strip()
    password = os.getenv("LIQUIDSNIPER_DEBUG_PASS", "").strip()
    if not any([token, user and password]):
        return True

    auth = str(environ.get("HTTP_AUTHORIZATION") or "")
    if token and auth.startswith("Bearer "):
        return auth.removeprefix("Bearer ").strip() == token

    if user and password and auth.startswith("Basic "):
        raw = auth.removeprefix("Basic ").strip()
        try:
            decoded = base64.b64decode(raw).decode("utf-8")
        except Exception:
            return False
        return decoded == f"{user}:{password}"

    return False


def build_app() -> Callable[..., list[bytes]]:
    def app(environ: dict[str, Any], start_response: Callable[..., Any]) -> list[bytes]:
        method = str(environ.get("REQUEST_METHOD") or "GET").upper()
        path = str(environ.get("PATH_INFO") or "/")

        if method not in {"GET", "HEAD"}:
            return _json_response(start_response, "405 Method Not Allowed", {"error": "READ_ONLY_MODE", "read_only": True})

        if not _authorized(environ):
            return _json_response(start_response, "401 Unauthorized", {"error": "UNAUTHORIZED", "read_only": True})

        if path == "/" or path == "/index.html":
            html = _INDEX_HTML.encode("utf-8")
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(html)))])
            return [html]

        if not path.startswith("/api/v1/debug"):
            return _json_response(start_response, "404 Not Found", {"error": "NOT_FOUND"})

        filters = _parse_filters(str(environ.get("QUERY_STRING") or ""))
        runs = _apply_filters(_load_runs(), filters)

        if path == "/api/v1/debug/orders":
            data = _build_orders(runs)
        elif path == "/api/v1/debug/positions":
            data = _build_positions(runs)
        elif path == "/api/v1/debug/events":
            data = _build_events(runs)
        elif path == "/api/v1/debug/strategies":
            data = _build_strategy_summaries(runs)
        elif path == "/api/v1/debug/snapshot":
            data = {
                "strategies": _build_strategy_summaries(runs),
                "orders": _build_orders(runs),
                "positions": _build_positions(runs),
                "events": _build_events(runs),
            }
        else:
            return _json_response(start_response, "404 Not Found", {"error": "NOT_FOUND"})

        return _json_response(
            start_response,
            "200 OK",
            {"data": data, "meta": {"read_only": True, "count": len(data) if isinstance(data, list) else None, "filters": filters}},
        )

    return app


_INDEX_HTML = """<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <title>LiquidSniper Paper Debug UI</title>
  <style>body{font-family:system-ui;margin:20px} .row{display:flex;gap:8px;flex-wrap:wrap} .card{border:1px solid #ddd;border-radius:8px;padding:10px;margin:6px 0} table{border-collapse:collapse;width:100%} td,th{border:1px solid #ddd;padding:4px;font-size:12px}</style>
</head>
<body>
  <h2>Paper Debug UI (read-only v1)</h2>
  <div class=\"row\">
    <label>Strategy <select id=\"strategy\"><option value=\"\">all</option><option>scalp</option><option>intraday</option><option>swing</option></select></label>
    <label>Run ID <input id=\"run_id\" /></label>
    <label>Test ID <input id=\"test_id\" /></label>
    <button onclick=\"reloadAll()\">Apply</button>
    <button onclick=\"exportSnapshot()\">Export snapshot JSON</button>
  </div>
  <h3>Strategy cards</h3><div id=\"strategies\"></div>
  <h3>Order flow</h3><table id=\"orders\"></table>
  <h3>Open positions</h3><table id=\"positions\"></table>
  <h3>Event log</h3><table id=\"events\"></table>
<script>
function filters(){
  const q = new URLSearchParams();
  for (const id of ["strategy","run_id","test_id"]) { const v=document.getElementById(id).value; if(v) q.set(id,v); }
  q.set("limit","200");
  return q.toString();
}
async function get(path){ const r=await fetch(path+"?"+filters()); return await r.json(); }
function table(el, rows){ if(!rows.length){el.innerHTML="<tr><td>No rows</td></tr>"; return;} const cols=Object.keys(rows[0]); el.innerHTML="<tr>"+cols.map(c=>`<th>${c}</th>`).join("")+"</tr>"+rows.map(r=>"<tr>"+cols.map(c=>`<td>${r[c] ?? ''}</td>`).join("")+"</tr>").join(""); }
async function reloadAll(){
  const s = (await get('/api/v1/debug/strategies')).data || [];
  document.getElementById('strategies').innerHTML = s.map(x=>`<div class=card><b>${x.strategy}</b> (${x.profile_id}) · runs ${x.runs_total} · executed ${x.executed_total} · rejected ${x.rejected_total} · open ${x.open_positions}</div>`).join('') || '<div class=card>No data</div>';
  table(document.getElementById('orders'), (await get('/api/v1/debug/orders')).data || []);
  table(document.getElementById('positions'), (await get('/api/v1/debug/positions')).data || []);
  table(document.getElementById('events'), (await get('/api/v1/debug/events')).data || []);
}
async function exportSnapshot(){
  const snap = await get('/api/v1/debug/snapshot');
  const blob = new Blob([JSON.stringify(snap, null, 2)], {type:'application/json'});
  const a = document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='paper-debug-snapshot.json'; a.click();
}
reloadAll();
</script>
</body>
</html>"""
