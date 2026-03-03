# T5 Parity Report — HTF Phase-1 Structure v3.3

## Scope

Summarize parity status after T1–T4 for Python engine vs certified Pine v3.3 contract under locked baseline inputs:

- strictGating = false
- breakMinFrac = 0.15
- chochBreakMinFrac = 0.15
- bosRequireFreshCross = true

## Evidence Reviewed

1. Contract/spec artifact: `intraday_revisit/artifacts/phase1_v3_3_parity/T1_contract_v3_3.md`
2. Test suite: `intraday_revisit/tests/test_htf_phase1.py`
3. Runtime artifacts:
   - `intraday_revisit/artifacts/phase1_v3_3_parity/T4_btcusdt_1d_window.json`
   - `intraday_revisit/artifacts/phase1_v3_3_parity/T4_ethusdt_1d_window.json`
   - `intraday_revisit/artifacts/phase1_v3_3_parity/T4_run_summary.json`
4. Validation command:
   - `python3 -m pytest -q intraday_revisit/tests/test_htf_phase1.py` → `7 passed in 0.01s`

## Mismatch Summary

- **Observed mismatches:** none found in contract-covered lifecycle behavior.
- BoS/CHoCH lifecycle and anchor write-point expectations from T1 are represented in tests and pass.
- Fresh-cross dedupe behavior is explicitly tested and passes.
- BTCUSDT/ETHUSDT 1D baseline parity runs completed and emitted deterministic artifacts with expected event emissions (no runtime or schema anomalies observed).

## Verdict

**PASS (Phase-1 parity at current contract/test scope).**

Current implementation satisfies v3.3 contract-level parity checks and produces stable baseline artifacts for both symbols. Remaining closeout work is documentation/certification state update (T6).
