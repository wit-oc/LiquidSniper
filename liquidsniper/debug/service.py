from __future__ import annotations

import base64
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
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

    page_size = 200
    raw_limit = params.get("limit", [None])[0]
    raw_page_size = params.get("page_size", [None])[0]
    raw_size = raw_page_size if raw_page_size is not None else raw_limit
    if raw_size is not None:
        try:
            page_size = max(1, min(1000, int(raw_size)))
        except (TypeError, ValueError):
            page_size = 200

    page = 1
    if "page" in params:
        try:
            page = max(1, int(params["page"][0]))
        except (TypeError, ValueError):
            page = 1

    event_hours = int(os.getenv("LIQUIDSNIPER_EVENT_RETENTION_HOURS", "24"))
    if "event_hours" in params:
        try:
            event_hours = max(1, min(24 * 30, int(params["event_hours"][0])))
        except (TypeError, ValueError):
            event_hours = int(os.getenv("LIQUIDSNIPER_EVENT_RETENTION_HOURS", "24"))

    strategy = params.get("strategy", [None])[0]
    run_id = params.get("run_id", [None])[0]
    test_id = params.get("test_id", [None])[0]
    return {
        "strategy": strategy if strategy in {"scalp", "intraday", "swing"} else None,
        "run_id": run_id or None,
        "test_id": test_id or None,
        "page_size": page_size,
        "page": page,
        "event_hours": event_hours,
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


def _load_breaker_state() -> dict[str, Any]:
    path = _artifact_root() / "paper_mvp" / "state" / "global_drawdown_breaker_state.json"
    if not path.exists():
        return {"tripped": False, "trip_reason": "", "state": "missing"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"tripped": True, "trip_reason": "GLOBAL_DRAWDOWN_STATE_UNREADABLE", "state": "corrupt"}
    return {
        "tripped": bool(payload.get("tripped", False)),
        "trip_reason": str(payload.get("trip_reason", "")),
        "drawdown_usd": payload.get("realized_pnl_usd", 0) * -1 if payload.get("realized_pnl_usd", 0) < 0 else 0,
        "trading_day": payload.get("trading_day"),
        "state": "ok",
    }


def _strategy_for_run(run: dict[str, Any]) -> tuple[str, str]:
    explicit = str(run.get("strategy") or "").strip().lower()
    if explicit in {"scalp", "intraday", "swing"}:
        return explicit, str(run.get("anchor_profile_id") or explicit[:1]).upper()
    profile_id = str(run.get("anchor_profile_id") or "I").upper()
    return STRATEGY_BY_PROFILE.get(profile_id, "intraday"), profile_id


def _test_id_for_run(run: dict[str, Any]) -> str | None:
    if isinstance(run.get("test_id"), str) and run.get("test_id"):
        return str(run["test_id"])
    trade_intent = run.get("trade_intent") if isinstance(run.get("trade_intent"), dict) else {}
    test_id = trade_intent.get("test_id")
    return str(test_id) if isinstance(test_id, str) and test_id else None


def _run_matches_filters(run: dict[str, Any], filters: dict[str, Any]) -> bool:
    strategy, _ = _strategy_for_run(run)
    if filters["strategy"] and strategy != filters["strategy"]:
        return False
    if filters["run_id"] and str(run.get("run_id") or "") != filters["run_id"]:
        return False
    if filters["test_id"] and _test_id_for_run(run) != filters["test_id"]:
        return False
    return True


def _apply_filters(runs: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
    return [run for run in runs if _run_matches_filters(run, filters)]


def _paginate(rows: list[dict[str, Any]], *, page: int, page_size: int) -> tuple[list[dict[str, Any]], dict[str, int]]:
    total = len(rows)
    start = (page - 1) * page_size
    end = start + page_size
    page_rows = rows[start:end]
    total_pages = max(1, (total + page_size - 1) // page_size)
    return page_rows, {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def _build_orders(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in runs:
        strategy, profile_id = _strategy_for_run(run)
        sr = run.get("sr_context") if isinstance(run.get("sr_context"), dict) else {}
        checks = run.get("gate_checks") if isinstance(run.get("gate_checks"), dict) else {}
        sec = checks.get("secondary_confluence") if isinstance(checks.get("secondary_confluence"), dict) else {}
        rows.append(
            {
                "run_id": run.get("run_id"),
                "timestamp": run.get("timestamp"),
                "strategy": strategy,
                "profile_id": profile_id,
                "symbol": run.get("symbol"),
                "side": run.get("direction"),
                "entry": run.get("entry"),
                "confluence_score": run.get("score_total"),
                "confluence_score_raw": run.get("score_total_raw"),
                "confluence_score_adj": run.get("score_total_adj"),
                "confluence_gate_passed": run.get("score_gate_passed"),
                "confluence_hits": sec.get("actual"),
                "confluence_min": sec.get("min"),
                "decision_tier": run.get("decision_tier"),
                "execution_decision": run.get("execution_decision"),
                "proposal_decision": run.get("proposal_decision"),
                "sr_entry_tf": sr.get("entry_tf"),
                "sr_itf_tf": sr.get("itf_tf"),
                "sr_htf_tf": sr.get("htf_tf"),
                "sr_nearest_htf_level": sr.get("nearest_htf_level"),
                "sr_nearest_itf_level": sr.get("nearest_itf_level"),
                "sr_first_retest_eligible": sr.get("first_retest_eligible"),
                "sr_distance_bps": sr.get("distance_bps"),
                "sr_retest_mode": run.get("sr_retest_mode") or sr.get("retest_mode"),
                "sr_near_retest_used": run.get("sr_near_retest_used") or sr.get("near_retest_used"),
                "sr_penalty": run.get("sr_penalty") or sr.get("sr_penalty"),
                "htf_chop_ci": run.get("htf_chop_ci"),
                "htf_chop_er": run.get("htf_chop_er"),
                "htf_chop_norm": run.get("htf_chop_norm"),
                "htf_chop_penalty": run.get("htf_chop_penalty"),
                "swing_bias_votes": (run.get("bias_snapshot") or {}).get("votes") if isinstance(run.get("bias_snapshot"), dict) else {},
                "test_id": _test_id_for_run(run),
            }
        )
    return rows


def _build_positions(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    open_by_lane_symbol: dict[str, dict[str, Any]] = {}
    for run in runs:
        if run.get("execution_decision") != "executed":
            continue
        if run.get("exit_reason"):
            continue
        symbol = str(run.get("symbol") or "")
        if not symbol:
            continue
        strategy, profile_id = _strategy_for_run(run)
        key = f"{strategy}:{symbol}"
        open_by_lane_symbol[key] = {
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
    return list(open_by_lane_symbol.values())


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    raw = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _build_events(runs: list[dict[str, Any]], *, event_hours: int = 24) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max(1, int(event_hours)))
    for run in runs:
        ts = _parse_timestamp(run.get("timestamp"))
        if ts is None or ts < cutoff:
            continue
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
        breaker = run.get("global_breaker") if isinstance(run.get("global_breaker"), dict) else {}
        if breaker.get("tripped"):
            out.append({**base, "event_type": "breaker_transition", "code": breaker.get("trip_reason") or "GLOBAL_DRAWDOWN_TRIPPED"})
    return out


def _build_strategy_summaries(runs: list[dict[str, Any]], breaker: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "strategy": "",
        "profile_id": "",
        "runs_total": 0,
        "executed_total": 0,
        "rejected_total": 0,
        "open_positions": 0,
        "latest_run_ts": None,
        "global_breaker_tripped": bool((breaker or {}).get("tripped", False)),
        "global_breaker_reason": (breaker or {}).get("trip_reason", ""),
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

        if path in {"/", "/ui", "/index.html"}:
            html = _INDEX_HTML.encode("utf-8")
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(html)))])
            return [html]

        if not path.startswith("/api/v1/debug"):
            return _json_response(start_response, "404 Not Found", {"error": "NOT_FOUND"})

        filters = _parse_filters(str(environ.get("QUERY_STRING") or ""))
        all_runs = _load_runs()
        runs = _apply_filters(all_runs, filters)
        breaker = _load_breaker_state()

        pagination: dict[str, int] | None = None
        if path == "/api/v1/debug/orders":
            rows = _build_orders(runs)
            data, pagination = _paginate(rows, page=int(filters["page"]), page_size=int(filters["page_size"]))
        elif path == "/api/v1/debug/positions":
            rows = _build_positions(runs)
            data, pagination = _paginate(rows, page=int(filters["page"]), page_size=int(filters["page_size"]))
        elif path == "/api/v1/debug/events":
            rows = _build_events(runs, event_hours=int(filters["event_hours"]))
            data, pagination = _paginate(rows, page=int(filters["page"]), page_size=int(filters["page_size"]))
        elif path == "/api/v1/debug/strategies":
            data = _build_strategy_summaries(runs, breaker)
        elif path == "/api/v1/debug/snapshot":
            data = {
                "strategies": _build_strategy_summaries(runs, breaker),
                "orders": _build_orders(runs),
                "positions": _build_positions(runs),
                "events": _build_events(runs, event_hours=int(filters["event_hours"])),
                "breaker": breaker,
            }
        else:
            return _json_response(start_response, "404 Not Found", {"error": "NOT_FOUND"})

        meta: dict[str, Any] = {"read_only": True, "count": len(data) if isinstance(data, list) else None, "filters": filters}
        if pagination is not None:
            meta["pagination"] = pagination

        return _json_response(start_response, "200 OK", {"data": data, "meta": meta})

    return app


_INDEX_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>LiquidSniper Paper Debug UI</title>
  <style>body{font-family:system-ui;margin:20px} .row{display:flex;gap:8px;flex-wrap:wrap} .card{border:1px solid #ddd;border-radius:8px;padding:10px;margin:6px 0} table{border-collapse:collapse;width:100%} td,th{border:1px solid #ddd;padding:4px;font-size:12px}</style>
</head>
<body>
  <h2>Paper Debug UI (read-only v1)</h2>
  <div class="row">
    <label>Strategy <select id="strategy"><option value="">all</option><option>scalp</option><option>intraday</option><option>swing</option></select></label>
    <label>Run ID <input id="run_id" /></label>
    <label>Test ID <input id="test_id" /></label>
    <label>Page <input id="page" type="number" min="1" value="1" style="width:72px" /></label>
    <label>Page size <input id="page_size" type="number" min="1" max="1000" value="100" style="width:88px" /></label>
    <label>Event hours <input id="event_hours" type="number" min="1" max="720" value="24" style="width:88px" /></label>
    <button onclick="reloadAll()">Apply</button>
    <button onclick="prevPage()">Prev</button>
    <button onclick="nextPage()">Next</button>
    <button onclick="exportSnapshot()">Export snapshot JSON</button>
  </div>
  <h3>Strategy cards</h3><div id="strategies"></div>
  <h3>Order flow</h3><div id="orders_meta"></div><table id="orders"></table>
  <h3>Open positions</h3><div id="positions_meta"></div><table id="positions"></table>
  <h3>Event log (retention window applied)</h3><div id="events_meta"></div><table id="events"></table>
<script>
function filters(){
  const q = new URLSearchParams();
  for (const id of ["strategy","run_id","test_id","page","page_size","event_hours"]) { const v=document.getElementById(id).value; if(v) q.set(id,v); }
  return q.toString();
}
async function get(path){ const r=await fetch(path+"?"+filters()); return await r.json(); }
function table(el, rows){ if(!rows.length){el.innerHTML="<tr><td>No rows</td></tr>"; return;} const cols=Object.keys(rows[0]); el.innerHTML="<tr>"+cols.map(c=>`<th>${c}</th>`).join("")+"</tr>"+rows.map(r=>"<tr>"+cols.map(c=>`<td>${r[c] ?? ''}</td>`).join("")+"</tr>").join(""); }
function setMeta(elId, payload){
  const p = payload?.meta?.pagination;
  if(!p){ document.getElementById(elId).innerHTML=''; return; }
  document.getElementById(elId).innerHTML = `<div class=card>page ${p.page}/${p.total_pages} · page_size ${p.page_size} · total ${p.total}</div>`;
}
function prevPage(){
  const el=document.getElementById('page');
  const n=Math.max(1, (parseInt(el.value||'1',10)-1));
  el.value=String(n); reloadAll();
}
function nextPage(){
  const el=document.getElementById('page');
  const n=Math.max(1, (parseInt(el.value||'1',10)+1));
  el.value=String(n); reloadAll();
}
async function reloadAll(){
  const s = (await get('/api/v1/debug/strategies')).data || [];
  document.getElementById('strategies').innerHTML = s.map(x=>`<div class=card><b>${x.strategy}</b> (${x.profile_id}) · runs ${x.runs_total} · executed ${x.executed_total} · rejected ${x.rejected_total} · open ${x.open_positions}</div>`).join('') || '<div class=card>No data</div>';

  const orders = await get('/api/v1/debug/orders');
  const positions = await get('/api/v1/debug/positions');
  const events = await get('/api/v1/debug/events');

  setMeta('orders_meta', orders);
  setMeta('positions_meta', positions);
  setMeta('events_meta', events);

  table(document.getElementById('orders'), orders.data || []);
  table(document.getElementById('positions'), positions.data || []);
  table(document.getElementById('events'), events.data || []);
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