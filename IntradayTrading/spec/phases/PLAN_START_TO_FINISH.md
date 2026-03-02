# Intraday Revisit — Start-to-Finish Phase Plan (Config-first discipline)

## Program policy
- Control thread owns approvals and phase transitions.
- Phase threads own implementation diagnostics.
- No broad sweeps until certification phases pass.

## Phase sequence
1. Phase 1: HTF Bias Certification (`phase-1-htf-bias`)
2. Phase 2a: Watch Engine — POI/Fib gating (`phase-2a-watch-poi-fib`)
3. Phase 2b: Watch Engine — lifecycle/timeouts (`phase-2b-watch-lifecycle`)
4. Phase 3a: Trigger Engine — candle scoring (`phase-3a-trigger-candles`)
5. Phase 3b: Trigger Engine — retest ordinal (`phase-3b-trigger-retest-ordinal`)
6. Phase 3c: Trigger Engine — score calibration (`phase-3c-trigger-score-calibration`)
7. Phase 4: Risk/Execution integration (`phase-4-risk-exec`)
8. Phase 5: Config-only tuning (`phase-5-tuning-config-only`)
9. Phase 6: Promotion + parity (`phase-6-promotion-parity`)

## Transition rule
- PASS or CONDITIONAL PASS required in control thread before moving forward.
- Any FAIL requires smallest-fix loop in same phase thread.
