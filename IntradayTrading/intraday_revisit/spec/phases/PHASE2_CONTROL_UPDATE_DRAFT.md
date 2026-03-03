Aligned with latest thread guidance:
- **No long-term zone persistence required** for Phase 2A; zones are recalculated on-chart for watcher POIs.
- **Cache is recommended** (JSON first, Parquet optional) for replay speed + audit logs.
- **EXPIRED remains disabled by default** (optional policy hook only).
- **No per-symbol width presets** in v1; keep global structure-derived width.

Phase 2A docs now include:
1) explicit runtime input contract for watcher/TV validator,
2) cache model (rebuildable from candles),
3) TradingView indicator starter scope (viewer/validator only).

Docs:
- `intraday_revisit/spec/phases/PHASE2A_SR_ARCHITECTURE_V1.md`
- `intraday_revisit/spec/phases/PHASE2A_SR_TV_VALIDATION_PLAN.md`
- `intraday_revisit/spec/phases/PHASE2_CONTROL_UPDATE_DRAFT.md`

Recommended next step: draft Pine input schema + output labels exactly matching reason codes, then run first two BTC fixtures in TV replay.
