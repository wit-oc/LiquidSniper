# LiquidSniper Execution Core Command Contract (v1)

Status: Draft (paper-mode first)  
Purpose: Define deterministic CLI/API command surfaces between orchestration agents and the Python execution core so strategy intent cannot bypass policy/risk gates.

---

## 1) Design principles

1. Agent proposes; core decides.
2. No direct order path without policy validation.
3. Every command returns structured reason codes.
4. Same inputs + same policy version => same decision.
5. Paper mode is default; live execution disabled unless explicit promotion gates pass.

---

## 2) Runtime modes

- `paper` (default): simulate fills + PnL, no exchange order placement.
- `dryrun`: full decision trace, no fill simulation.
- `live` (future): blocked by gate until explicit sign-off.

---

## 3) Canonical command set (CLI-first)

Base command: `python -m liquidsniper.exec_core <command> [flags]`

### 3.1 Data and context

#### `refresh-data`
Fetch/incremental update canonical OHLCV feed.

Input:
- `--symbols BTCUSDT,ETHUSDT,...`
- `--timeframes 1d,4h,1h,15m`
- `--from <iso8601 optional>`

Output:
- feed status, staleness, quality summary by symbol/timeframe.

#### `feed-health`
Return feed quality/rate-limit/circuit-breaker status.

---

### 3.2 Strategy evaluation

#### `score-candidates`
Run strategy scoring and produce candidate decisions.

Input:
- `--symbols ...`
- `--anchor-profile swing|intraday|scalp`
- `--mode paper|dryrun`
- `--as-of <iso8601 optional>`

Output:
- candidate list with score breakdown, risk tier proposal, and decision (`go|reduced|no_go`).

#### `explain-candidate`
Explain one candidate trace deterministically.

Input:
- `--candidate-id <id>`

Output:
- factor breakdown + rule checks + reason codes.

---

### 3.3 Execution proposal + policy firewall

#### `propose-trade`
Submit a trade intent to policy/risk validation.

Input:
- `--symbol`
- `--side long|short`
- `--entry`
- `--stop`
- `--targets t1,t2`
- `--anchor-profile`
- `--score`
- `--thesis-ref`
- `--mode paper|dryrun`

Output:
- `accepted` or `rejected`
- blocking/non-blocking reason codes
- normalized risk allocation if accepted

#### `execute-approved`
Execute only previously accepted proposal id.

Input:
- `--proposal-id`

Output:
- paper fill result + position state (paper), or blocked if mode disallows.

---

### 3.4 Portfolio controls

#### `portfolio-status`
Return open risk, cluster risk, drawdown state, lockouts.

#### `set-kill-switch`
Enable/disable execution lock.

Input:
- `--state on|off`
- `--reason`

Output:
- updated lock state + timestamp + actor.

---

## 4) Policy firewall: hard reject model

`propose-trade` and `execute-approved` must run blocking checks in this order:

1. mode gate (`live` blocked unless promotion gate passed)
2. data integrity gate (staleness/quality)
3. strategy gate (score threshold, HTF alignment, regime permission)
4. risk gate (per-trade, cluster, portfolio, drawdown)
5. venue/account gate (allowlist/scope)
6. kill-switch gate

If any gate fails => `rejected` with stable reason codes.

### 4.1 Required blocking reason codes (v1)

- `MODE_NOT_ALLOWED`
- `DATA_STALE`
- `CANDLE_QUALITY_FAIL`
- `SCORE_TOO_LOW`
- `HTF_MISALIGNMENT`
- `REGIME_NO_TRADE`
- `INVALIDATION_MISSING`
- `RR_BELOW_MIN`
- `RISK_PER_TRADE_EXCEEDED`
- `CLUSTER_RISK_EXCEEDED`
- `PORTFOLIO_RISK_EXCEEDED`
- `DAILY_DRAWDOWN_LOCKOUT`
- `VENUE_NOT_ALLOWED`
- `ACCOUNT_SCOPE_VIOLATION`
- `KILL_SWITCH_ACTIVE`

---

## 5) Minimum JSON schemas

### 5.1 Proposal request

```json
{
  "trace_id": "run_...",
  "symbol": "ETHUSDT",
  "side": "long",
  "entry": 2012.5,
  "stop": 1978.0,
  "targets": [2060.0, 2125.0],
  "anchor_profile_id": "swing",
  "htf_anchor_tf": "1d",
  "score_total": 8.6,
  "score_breakdown": {
    "regime_alignment": 2.5,
    "structure_quality": 1.5,
    "location_quality": 1.8,
    "trigger_quality": 1.8,
    "execution_geometry": 1.0
  },
  "policy_version": "v1",
  "rulebook_ref": "TRADING_STRATEGY_PLAYBOOK_V1"
}
```

### 5.2 Proposal response

```json
{
  "decision": "rejected",
  "reasons": [
    {"code": "HTF_MISALIGNMENT", "detail": "daily bias=short, proposed=long"},
    {"code": "SCORE_TOO_LOW", "detail": "5.4 < 6.0"}
  ],
  "policy_version": "v1",
  "trace_id": "run_..."
}
```

---

## 6) Scoring/risk contract bindings (v1)

- Minimum eligible score: `>= 6.0`
- 10/10 max risk cap: `6%`
- Counter-structure scalp cap: `1%–2%`
- Score/risk tier mapping sourced from strategy playbook and runbook references.

---

## 7) Sub-agent contract (safe orchestration)

Sub-agents may call only command-set endpoints.
They may not place raw exchange orders.
All execution must pass `propose-trade` -> `execute-approved` handshake.

---

## 8) Acceptance criteria (for Tasks 14/15/16 linkage)

1. CLI commands return schema-valid JSON.
2. Reject reasons are deterministic and replayable.
3. At least 10 fixed fixtures prove hard rejects for invalid proposals.
4. Policy non-bypass tests fail any direct execution attempt.
5. Paper-mode run emits auditable trace bundle.

---

## 9) References

- `docs/MVP_PAPER_SEQUENCE_V1.md`
- `docs/DATA_FEED_STRATEGY_V1.md`
- `docs/HTF_ANCHOR_PROFILE_CONTRACT_V1.md`
- `docs/TRADING_STRATEGY_RUNBOOK_V1.md`
- `docs/AUTOMATED_TRADING_AGENT_ALIGNMENT_V1.md`
- `docs/GO_NO_GO_CHECKLIST.md`
