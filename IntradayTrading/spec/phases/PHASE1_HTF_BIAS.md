# Phase 1 — HTF Structure / Bias (Certified)

Status: **DONE (2026-03-03)**

Scope: structure-state certification only (no trigger/risk/exec policy).

## Certified implementation

### TradingView indicator
- `IntradayTrading/pine/HTF_Phase1_Structure_v3_3.pine`

### Python analytics engine
- `IntradayTrading/engine/htf_phase1.py`
- Entrypoint: `run_phase1_htf_structure(...)`

### Regression/parity assets
- `IntradayTrading/artifacts/phase1_v3_3_parity/`

## Certified behavior
- Regime direction is persistent (`bullish|bearish`).
- CHoCH and BoS drive structural anchor updates.
- `transitional` is diagnostic/risk metadata (not anchor source).
- BoS fresh-cross + dedupe controls prevent repeated same-ref spam.

## Baseline cert settings
- `n_init=25`
- `strictGating=false`
- `bosRequireFreshCross=true`
- `breakMinFrac=0.15`
- `chochBreakMinFrac=0.15`
- `enableContinuationBreak=true`

## Acceptance result
- TradingView and Python parity accepted by operator on BTC/ETH 1D sample set.
- Documented as “100% alignment” in control-thread validation.

## Phase transition
- Phase 1 is closed.
- Proceed to **Phase 2 — Watch Engine Certification**.

## References
- `spec/phases/PHASE1_HTF_STRUCTURE_CERT_PLAN.md`
- `spec/phases/PHASE1_HTF_STRUCTURE_DONE.md`
