# Phase 1 HTF Structure — DONE Stamp

Date: 2026-03-03  
Owners: Redact + Wit

## Summary
Phase 1 HTF structure certification is complete.

The v3.3 TradingView indicator and Python analytics engine are aligned on accepted BTC/ETH 1D regression windows under locked baseline settings.

## Certified artifacts
- Pine indicator:
  - `IntradayTrading/pine/HTF_Phase1_Structure_v3_3.pine`
  - user guide: `IntradayTrading/pine/HTF_Phase1_Structure_v3_3_USER_GUIDE.md`
- Python engine + tests:
  - `IntradayTrading/engine/htf_phase1.py`
  - `IntradayTrading/tests/test_htf_phase1.py`
- Parity evidence:
  - `IntradayTrading/artifacts/phase1_v3_3_parity/T1_contract_v3_3.md`
  - `IntradayTrading/artifacts/phase1_v3_3_parity/T4_btcusdt_1d_window.json`
  - `IntradayTrading/artifacts/phase1_v3_3_parity/T4_ethusdt_1d_window.json`
  - `IntradayTrading/artifacts/phase1_v3_3_parity/T4_run_summary.json`
  - `IntradayTrading/artifacts/phase1_v3_3_parity/T5_parity_report.md`
  - `IntradayTrading/artifacts/phase1_v3_3_parity/T7_last3_events_okx_1d.json`

## Locked baseline settings
- `n_init=25`
- `strictGating=false`
- `bosRequireFreshCross=true`
- `breakMinFrac=0.15`
- `chochBreakMinFrac=0.15`
- `enableContinuationBreak=true`

## Caveats
- Indicator computes on active chart timeframe (not fixed HTF `request.security()` pin).
- Phase 1 scope excludes watch-state, trigger, and execution/risk policy logic.

## Transition decision
✅ Phase 1 closed. Move to **Phase 2 — Watch Engine Certification**.
