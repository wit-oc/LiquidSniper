# Phase 1 HTF Market Structure — Certification Plan (v3.3)

Status: IN PROGRESS  
Owner: Redact + Wit  
Scope: TradingView Pine + Python Analysis Engine parity for HTF structure

## Objective
Certify HTF market-structure logic as "DONE" for this phase by proving:
1. TradingView indicator behavior is acceptable on representative replay segments.
2. Equivalent Python logic reproduces swing/anchor events from the same candles and same inputs.
3. Backtest-side structural event stream is consistent enough for automated paper-trading analysis.

---

## Canonical Pine candidate
- File: `IntradayTrading/pine/HTF_Phase1_Structure_v3_3.pine`
- Candidate profile (current best):
  - `strictGating = false`
  - `bosRequireFreshCross = true`
  - `breakMinFrac = 0.05` (primary)
  - `chochBreakMinFrac = 0.12`

Secondary sensitivity profile:
- Same settings, but `breakMinFrac = 0.20`

---

## Workstream A — Freeze visual baseline
1. Lock canonical Pine version/hash and input profile.
2. Capture 3-5 replay segments with before/during/after screenshots for:
   - expected BoS up and down,
   - expected CHoCH up and down,
   - prior known failure windows (anchor drift, overfiring, missed anchor write).
3. Mark each segment pass/fail with notes.

Artifact:
- `IntradayTrading/artifacts/phase1_htf_structure/pine_v3_3_visual_cert.md`

---

## Workstream B — Python parity implementation
1. Port v3.3 structural rules into Python analysis engine (same inputs/thresholds).
2. Emit deterministic event tape:
   - BoS (confirmed)
   - CHoCH
   - Structural anchor updates (VH/VL)
   - Validated swing references
3. Add tests for edge cases from replay findings.

Artifacts:
- Python module update (engine path)
- `IntradayTrading/tests/test_htf_phase1_v3_3_parity.py`

---

## Workstream C — Candle-level parity validation
For each certification segment:
1. Export OHLC candles used in TradingView replay (or equivalent source-aligned candles).
2. Run Python engine on identical candles + identical inputs.
3. Compare event tape vs Pine expectations:
   - direction changes,
   - anchor index/price updates,
   - BoS/CHoCH ordering.

Pass target:
- No critical mismatches on anchor lifecycle or trend flips.
- Minor marker timing differences only if explained and accepted.

Artifact:
- `IntradayTrading/artifacts/phase1_htf_structure/parity_report_v3_3.md`

---

## Workstream D — Certification stamp
When A+B+C pass:
1. Mark Phase 1 HTF Structure as DONE.
2. Write short closeout with:
   - certified Pine file + input profile,
   - certified Python engine version,
   - known caveats.

Artifacts:
- `IntradayTrading/spec/phases/PHASE1_HTF_BIAS.md` (status update)
- `IntradayTrading/spec/phases/PHASE1_HTF_STRUCTURE_DONE.md`

---

## Next phase handoff target
After Phase 1 done stamp, proceed to Watch Engine Certification (per linked thread reference) with HTF structure treated as upstream certified dependency.
