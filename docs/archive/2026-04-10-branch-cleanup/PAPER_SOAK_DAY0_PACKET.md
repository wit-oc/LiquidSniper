# LiquidSniper Paper Soak — Day 0 Control Packet

Date: 2026-02-24 (ET)
Scope: Paper-only soak kickoff under existing hard risk controls.

## 1) Fixed cadence + checkpoints

- **T0 (start):** preflight and launch confirmation
- **T+15m:** startup health checkpoint
- **T+60m:** checkpoint-1 evidence snapshot
- **T+4h:** intraday stability checkpoint
- **T+24h:** day summary + GO/HOLD recommendation

All checkpoints must produce a timestamped artifact in `artifacts/paper_soak/`.

## 2) Metrics to collect at every checkpoint

Minimum required fields:

- Runtime mode (`paper` expected)
- Policy gate status (daily-loss breaker gate first)
- Feed health: heartbeat lag, missing candle count, reconnect count
- Strategy fan-out health: enabled lanes, per-lane cycle latency p50/p95
- Decision pipeline counts: intents generated/filtered/accepted
- Circuit-breaker events (any trigger reason)
- Error counts by class (ingest/policy/execution)

## 3) Kill criteria (immediate HOLD)

Enter HOLD and stop promotion actions if any of these occur:

1. Mode safety violation (anything not paper mode)
2. Daily-loss breaker not first gate or fail-closed behavior regresses
3. Telemetry blind spot >10 minutes for core health metrics
4. Repeated ingest/policy/execution hard failures for 3 consecutive cycles
5. Any non-bypass boundary violation evidence in strategy->policy->execution chain

## 4) Promotion criteria (continue soak / consider progression)

Day-0 only allows **continue soak** (not live enablement). Criteria:

- Paper mode remains enforced for full interval
- No kill criteria triggered
- Core telemetry coverage complete for all checkpoints
- Error rate stable/non-escalating between T+15m and T+60m
- Daily-loss breaker behavior confirmed with no ordering regressions

## 5) Checkpoint-1 artifact template (T+60m)

Use this structure:

```json
{
  "timestamp_et": "",
  "mode": "paper",
  "policy_gate_order": ["RISK_DAILY_LOSS_CAP_BREACH", "..."],
  "feed_health": {
    "heartbeat_lag_ms": 0,
    "missing_candles": 0,
    "reconnect_count": 0
  },
  "pipeline": {
    "intents_generated": 0,
    "intents_filtered": 0,
    "intents_accepted": 0
  },
  "errors": {
    "ingest": 0,
    "policy": 0,
    "execution": 0
  },
  "circuit_breakers": [],
  "status": "GO|HOLD",
  "notes": ""
}
```

## 6) Operator notes

- This packet does **not** authorize non-paper execution.
- If HOLD is triggered, pause execution immediately and publish blocker + smallest unblocked next step.
