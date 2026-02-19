# Paper Trading Scorecard (V1)

Purpose: deterministic tracking of paper-trading success/failure for LiquidSniper before any live-mode discussion.

## 1) Tracking ownership

- **Wit (agent):** generate run artifacts, daily/weekly scorecards, and gate recommendation.
- **Redact (operator):** approve thresholds/overrides and promotion decisions.

## 2) Artifact outputs (authoritative)

- Per-run decision log: `artifacts/paper_mvp/runs/<run_id>.json`
- Daily summary: `artifacts/paper_mvp/daily/<YYYY-MM-DD>.json`
- Weekly rollup: `artifacts/paper_mvp/weekly/<YYYY-Www>.json`
- Gate artifact: `artifacts/paper_mvp/task17_26_gate_evidence.json`

## 3) Required per-run schema

```json
{
  "run_id": "string",
  "timestamp": "ISO8601",
  "symbol": "ETHUSDT",
  "direction": "long|short",
  "anchor_profile_id": "S|I|C",
  "htf_anchor_tf": "1D|4H|1H",
  "score_total": 8.4,
  "score_gate_passed": true,
  "decision_tier": "watch_only|publish_candidate|high_priority|reject",
  "decision_reason_codes": ["..."],
  "feed_state": "ok|degraded|tripped|resync_required",
  "feed_reason_codes": ["..."],
  "canonical_trace_id": "string",
  "trigger_trace_id": "string|null",
  "trigger_influence": 3.2,
  "entry": 2012.5,
  "stop_loss_initial": 1978.0,
  "tp_levels": [2060.0, 2125.0, 2190.0],
  "tp_plan": [
    {"level": 2060.0, "size_pct": 0.4},
    {"level": 2125.0, "size_pct": 0.35},
    {"level": 2190.0, "size_pct": 0.25}
  ],
  "stop_policy": {
    "move_to_break_even_on_tp1": true,
    "break_even_price": 2012.5,
    "post_tp1_trailing": "disabled_by_default"
  },
  "risk_pct_requested": 2.0,
  "risk_pct_allowed": 2.0,
  "proposal_decision": "accepted|rejected",
  "execution_decision": "executed|blocked|noop",
  "pnl_r": 0.8,
  "pnl_pct": 0.34,
  "max_adverse_excursion_r": -0.6,
  "max_favorable_excursion_r": 1.2,
  "exit_reason": "tp|sl|time|policy",
  "policy_version": "v1",
  "rulebook_ref": "TRADING_STRATEGY_PLAYBOOK_V1"
}
```

## 4) Trade management policy (required)

- Every paper trade must include **multiple TP levels** (`tp_levels` + `tp_plan`).
- On first TP hit, stop loss must move to **break even** (`move_to_break_even_on_tp1=true`).
- After TP1, no further automatic stop movement is required by default.
- Early/urgent exit after TP1 is allowed only when fresh data/regime evidence invalidates thesis (`exit_reason=policy`).

## 5) Success / failure definitions

### Hard failure (auto HOLD/NO_GO)
- Any non-bypass break (`NON_BYPASS_FAILED`)
- Policy pinning/replay failure (`POLICY_VERSION_UNPINNED`, `REPLAY_PARITY_FAILED`)
- Persistent feed-health instability above thresholds

### Paper success (GO candidate)
- Gate artifact remains `recommendation=GO`
- Feed metrics remain within benchmark thresholds
- Positive expectancy over review window (with sufficient sample)
- Loss behavior remains inside policy caps and drawdown constraints

## 6) Review cadence

- **Per run:** record deterministic run artifact
- **Daily:** summarize hit rate, expectancy (R), reject-rate by reason code, feed health
- **Weekly:** promotion posture: `GO | HOLD | NO_GO` with top 3 blockers/opportunities

## 7) Operator-facing summary format (daily)

```markdown
Paper Trading Daily (YYYY-MM-DD)
- Runs: <n> | Accepted: <n> | Executed: <n> | Rejected: <n>
- Expectancy: <x.xx R> | Win rate: <x%> | Profit factor: <x.xx>
- Risk discipline: breaches=<n> | drawdown=<x%> | cluster cap breaches=<n>
- Feed health: freshness=<x%> gap_rate=<x%> rate_limit_rate=<x%>
- Top reject reasons: <code1>(n), <code2>(n), <code3>(n)
- Gate posture: GO|HOLD|NO_GO — <one-line reason>
```

## 8) Initial promotion guideline

Minimum for considering live-discussion readiness (not activation):
- 3–7 day paper window complete
- No critical hard-failure reason codes
- Benchmark and adversarial gates passing
- Stable operational discipline and reproducible artifacts

## 9) Activation runbook (paper-only)

All commands below are intentionally paper-only and write artifacts under `artifacts/paper_mvp/`.

### 9.1 One paper execution cycle (writes per-run artifact)

```bash
python3 - <<'PY'
from liquidsniper.core.execution_boundary import ExecutionBoundary, PolicyDecision

boundary = ExecutionBoundary()
proposal = {
    "trace_id": "manual-2026-02-19T00:00:00Z",
    "policy_version": "v1",
    "rulebook_ref": "TRADING_STRATEGY_PLAYBOOK_V1",
    "mode": "paper",
    "symbol": "ETHUSDT",
    "direction": "long",
    "entry": 2012.5,
    "stop_loss_initial": 1978.0,
    "tp_levels": [2060.0, 2125.0, 2190.0],
    "trade_intent": {
        "symbol": "ETHUSDT",
        "side": "buy",
        "mode": "paper",
        "risk_pct": "1.0",
        "stop_loss": "1978.0",
        "take_profit": "2060.0",
        "projected_daily_loss_usd": "150",
        "max_daily_loss_usd": "500",
        "projected_cluster_loss_usd": "120",
        "max_cluster_loss_usd": "300",
        "slippage_bps": "8",
        "max_slippage_bps": "25",
        "policy_version": "v1",
        "trace_id": "manual-2026-02-19T00:00:00Z",
        "rulebook_ref": "TRADING_STRATEGY_PLAYBOOK_V1",
    },
}
policy = PolicyDecision(
    accepted=True,
    reason_codes=(),
    trace_id=proposal["trace_id"],
    policy_version=proposal["policy_version"],
)
out = boundary.propose_trade(proposal, policy)
print(boundary.execute_with_adapter(out["proposal_id"], lambda _: {"status": "paper_fill"}))
PY
```

Expected: `decision='executed'` and `paper_run_artifact_path='artifacts/paper_mvp/runs/<trace_id>.json'`.

### 9.2 Generate daily scorecard from accumulated run artifacts

```bash
python3 - <<'PY'
from liquidsniper.core.paper_artifacts import persist_daily_scorecard
payload, path = persist_daily_scorecard(trading_day="2026-02-19")
print(path)
print(payload)
PY
```

### 9.3 Generate weekly rollup from accumulated run artifacts

```bash
python3 - <<'PY'
from liquidsniper.core.paper_artifacts import persist_weekly_rollup
payload, path = persist_weekly_rollup(trading_week="2026-W08")
print(path)
print(payload)
PY
```

### 9.4 Optional: continuous paper loop (operator shell)

```bash
while true; do
  # run your paper decisioning/execution cycle(s) here
  python3 -m pytest -q tests/test_execution_boundary_task16.py || break
  sleep 60
done
```

Use your existing scheduler/orchestrator to replace the placeholder cycle with your real proposal+policy path.

## 10) Operator output format (copy/paste)

Use this message format when posting scorecards:

```markdown
Paper Trading Daily (YYYY-MM-DD)
- Runs: <n> | Accepted: <n> | Executed: <n> | Rejected: <n>
- Expectancy: <x.xx R> | Win rate: <x%> | Profit factor: <x.xx>
- Risk discipline: breaches=<n> | drawdown=<x%> | cluster cap breaches=<n>
- Feed health: freshness=<x%> gap_rate=<x%> rate_limit_rate=<x%>
- Top reject reasons: <code1>(n), <code2>(n), <code3>(n)
- Gate posture: GO|HOLD|NO_GO — <one-line reason>
- Artifacts: run_dir=artifacts/paper_mvp/runs daily=artifacts/paper_mvp/daily/<YYYY-MM-DD>.json weekly=artifacts/paper_mvp/weekly/<YYYY-Www>.json
```
