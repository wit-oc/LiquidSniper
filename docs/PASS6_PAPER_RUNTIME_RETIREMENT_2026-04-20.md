# Pass 6, Paper Runtime Retirement

Date: 2026-04-20  
Status: first destructive cleanup pass removing the experimental paper-runtime stack from the active repo surface

This pass treats the paper-runtime subsystem as retired rather than merely legacy.

---

## Outcome

### Deleted from the active repo surface

Runtime / orchestration:
- `liquidsniper/ops/paper_daemon.py`
- `liquidsniper/ops/paper_parallel.py`
- `liquidsniper/ops/scorecard_worker.py`

Core paper helpers:
- `liquidsniper/core/execution_boundary.py`
- `liquidsniper/core/paper_artifacts.py`
- `liquidsniper/core/paper_policy.py`
- `liquidsniper/core/paper_trade.py`
- `liquidsniper/core/rollout_controls.py`

Paper debug API surface:
- `liquidsniper/debug/`

Operational wrappers / configs:
- `docker-compose.paper.yml`
- `Makefile` paper-runtime targets
- tracked paper env example(s)

Test surface used only for the paper stack:
- paper daemon / policy / breaker / rollout / scorecard / debug API tests
- `tests/test_signal_delivery_and_paper_trade.py`

Paper-only active docs:
- `docs/PR_EVIDENCE_PACK_MULTISTRATEGY_BREAKER_V1.md`
- `docs/internal/SWING_BIAS_AUDIT_2026-02-24.md`

### Archived instead of deleted

Historical tracked paper artifacts moved from:
- `artifacts/paper_mvp/`

to:
- `artifacts/archive/2026-04-20-paper-runtime-retirement/paper_mvp/`

Reason:
- the runtime is retired
- the evidence can remain as historical reference without occupying an active path

### Kept intentionally

These were **not** deleted in this pass because they are broader than the paper-runtime experiment or may still be useful outside it:

- `liquidsniper/core/policy_gate.py`
  - generic trade-intent validation, though it still contains paper-mode assumptions
- `liquidsniper/core/signal_delivery.py`
  - generic payload-rendering utility, not paper-runtime-specific by itself
- mixed historical docs that mention paper outputs but are not themselves the runtime surface

---

## Keep / move / delete judgment

### Keep
- `policy_gate.py` for now, pending a later cleanup of paper-specific enum logic
- `signal_delivery.py`

### Move
- `artifacts/paper_mvp/` -> `artifacts/archive/2026-04-20-paper-runtime-retirement/paper_mvp/`

### Delete
- the executable paper runtime
- the paper-only orchestration/debug surface
- the paper-only tests and operator wrappers

---

## Next follow-up

The remaining cleanup is smaller and more semantic than structural:
1. remove paper-specific assumptions from `policy_gate.py` if we no longer want `mode=paper` recognized there
2. optionally archive or prune mixed historical docs that still reference retired paper outputs
3. after that, reassess whether the repo rename can finally happen without lying
