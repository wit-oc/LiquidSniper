# Intraday Revisit — Phase Thread Convention

Control thread (this thread):
- `#intraday-revisit-v1-sr-zone-logic-robust-backtesting-plan`
- Purpose: approvals, phase transitions, final decisions.

One active phase thread at a time:
- `phase-1-htf-bias`
- `phase-2a-watch-poi-fib`
- `phase-2b-watch-lifecycle`
- `phase-3a-trigger-candles`
- `phase-3b-trigger-retest-ordinal`
- `phase-3c-trigger-score-calibration`
- `phase-4-risk-exec`
- `phase-5-tuning-config-only`
- `phase-6-promotion-parity`

Rules:
1) Only one active phase thread at once.
2) No next phase starts until control thread approves prior phase handoff.
3) Logic rewrite scope is phase-bound; outside-scope changes are deferred.
4) Phase threads carry diagnostics; control thread carries decisions and checkpoints.
