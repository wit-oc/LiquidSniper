# PHASE2A — TradingView-First Validation Plan (S/R Watcher)

## 0) Goal
Validate Phase 2A S/R watcher behavior against visual market structure in TradingView before any code tuning beyond v1 defaults.

Scope locked to WATCH/INVALID/EXPIRED logic.

---

## 1) TradingView indicator build scope (starter)

Build a Phase 2A viewer indicator first (no entries/triggers):
- Inputs panel exposes only watcher parameters (kAtr, spacing, break/separation/base/reclaim).
- Multi-timeframe zone projection (chart TF + HTF list).
- Deterministic labels for state, retestCount, and reason code.
- Optional cache export hook (JSON/Parquet via external runner, not Pine-native persistence).

## 2) Required TV overlays

For each chart (BTC/ETH; 15m + 1h minimum), render:

1. **Zone bands**
   - Active support/resistance rectangles (top/bottom/mid).
   - Color by state: ACTIVE, FLIP_CANDIDATE, FLIPPED_ACTIVE, INVALID, EXPIRED.
2. **HTF authority marker**
   - Label zones with timeframe rank; highlight when HTF overrides LTF.
3. **Touch markers**
   - Dot/triangle on qualifying touch bars.
   - Distinct marker for first retest.
4. **Break-close markers**
   - Marker on bar that confirms close beyond zone.
5. **Separation threshold guide**
   - Projected line at `sepK * width` beyond broken zone.
6. **Base window overlay**
   - Box spanning consolidation bars counted toward 4–6 requirement.
   - Show `baseCount` text.
7. **Reason code stream (compact label)**
   - Last emitted reason code at each transition bar.
8. **Retest counter label**
   - Current retestCount near zone mid.

---

## 2) Screenshot artifact protocol

Store artifacts under:
`intraday_revisit/spec/phases/artifacts/phase2a_tv_validation/<symbol>/<fixture>/`

Per fixture, capture exactly:
1. `01_context.png` — full context before event sequence.
2. `02_transition.png` — key transition moment (break/flip/invalidation/etc).
3. `03_outcome.png` — final resulting state.
4. `events.json` — exported bar-by-bar event log (timestamp, state, retestCount, reasonCode).
5. `notes.md` — short human note: pass/fail + discrepancy summary.

Naming convention:
`<symbol>_<tf>_<fixture>_<step>.png`

Example:
`BTCUSDT_15m_break_sep_base_flip_02_transition.png`

---

## 3) Validation sequence

1. Load fixture candles in TV replay mode.
2. Apply S/R watcher overlay with v1 defaults unchanged.
3. Step bar-by-bar through fixture window.
4. Capture required screenshots/events at defined milestones.
5. Compare against expected deterministic log.
6. Mark fixture pass/fail.

No threshold tuning during first pass. Tuning is allowed only after full first-pass discrepancy report.

---

## 4) Pass/fail rubric

A fixture is **PASS** only if all conditions hold:
1. Final state equals expected state.
2. Transition order matches expected (no missing/extra transitions).
3. Reason codes match expected transition bars.
4. Retest counter path matches expected values.
5. HTF override behavior matches doctrine where applicable.

Automatic **FAIL** conditions:
- Retest reset without confirmed flip chain.
- Flip confirmed without all prerequisites (break close + separation + 4–6 base).
- LTF decision overrides conflicting HTF zone.
- Overlapping authoritative zones after normalization.

---

## 5) Initial fixture matrix (must run first)

- BTC_15m_first_retest_hold
- BTC_15m_break_sep_base_flip
- BTC_15m_false_break_reclaim_invalid
- ETH_1h_htf_overrides_ltf
- ETH_15m_touch_cluster_no_reset
- ETH_15m_spacing_overlap_resolution

---

## 6) Output checklist for certification thread

For each fixture, post:
- Pass/Fail
- One-line reason
- Link/path to `03_outcome.png`
- Link/path to `events.json`
- If fail: exact first divergence bar and expected vs actual reason code

This keeps Phase 2 certification discussions fast and auditable.
