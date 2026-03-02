# Phase 1 HTF Bias FSM Rewrite — T6 Completion Summary

## BTC 1D Validation (OKX provenance-locked)

- Dataset: `intraday_revisit/data/btc_1d_okx_ccxt_2022_to_now.csv`
- Bars processed: `1522`
- BoS confirmed: `12`
- CHoCH detected: `659`
- Anchor update events: `23` (`1.51` per 100 bars)
- Final state: `bearish / impulsive_down` (confidence: `transitional`, latch: `true`)

## Candle Audit Slice

- Generated: `intraday_revisit/artifacts/phase1_htf_bias/btc_1d_candle_audit_2025-11_to_2026-01.csv`
- Window: `2025-11-01T00:00:00Z` to `2026-02-01T00:00:00Z` (exclusive end)
- Rows: `92` candles (+ header)

## Report Channel Delivery

- Intended destination (not auto-sent in this run): `discord:channel:1477769141539836015`
