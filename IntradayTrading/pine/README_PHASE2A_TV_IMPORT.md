# Phase2A S/R Watcher V1 — TradingView Import

## File
- `intraday_revisit/tv/PHASE2A_SR_WATCHER_V1.pine`

## Import steps
1. Open TradingView chart.
2. Open **Pine Editor**.
3. Paste full contents of `PHASE2A_SR_WATCHER_V1.pine`.
4. Click **Save** then **Add to chart**.

## What this build includes
- Phase 2A watcher-only scaffold (no entries/triggers).
- Pivot-derived S/R reaction zones with ATR-scaled width (`kAtr * ATR`).
- Non-overlap/spacing pruning (same-side strongest locus kept).
- State flow: ACTIVE → FLIP_CANDIDATE → FLIPPED / INVALID (+ optional EXPIRED hook OFF by default).
- Retest counter behavior aligned to doctrine (touches increment, no touch reset; reset on confirmed flip).
- Reason-code labels for transition diagnostics.
- HTF pivot markers as authority hints.

## Notes
- This is an implementation starter intended for the TV validation loop in Phase 2A.
- Cache/export to JSON/Parquet is handled by external runner tooling, not Pine-native storage.
- If compile limits are hit on lower-end plans, reduce `maxZones` and disable `showReasonLabels`.
