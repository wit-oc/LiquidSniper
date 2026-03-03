# HTF Phase 1 Structure v3.3 — User Guide

Indicator file: `HTF_Phase1_Structure_v3_3.pine`

## What this indicator does

This indicator tracks HTF market structure using:
- **BoS** (continuation structure breaks)
- **CHoCH** (structure flips)
- Structural anchor updates:
  - Uptrend anchor = **low (VL)**
  - Downtrend anchor = **high (VH)**

v3.3 is **structure-first**:
- CHoCH and BoS write structural anchors.
- `transitional` is diagnostic/risk metadata, not anchor source logic.

---

## Quick start (recommended baseline)

1. Open TradingView -> Pine Editor.
2. Paste `HTF_Phase1_Structure_v3_3.pine`.
3. Add to chart.
4. Use defaults unless you are calibrating:
   - `strictGating = false`
   - `breakMinFrac = 0.15`
   - `chochBreakMinFrac = 0.15`
   - `panelMode = minimal`
   - `debugView = false`

---

## Inputs (plain-English)

### Bootstrap / scope
- `Bootstrap from EMA12 over first N bars`: auto-picks initial direction once warmup is done.
- `Bootstrap bars`: warmup length for EMA bootstrap.
- `Manual initial bullish`: only used before bootstrap lock.
- `Process only recent bars`: limits analysis window to recent history.
- `Max lockback window bars`: safety cap for dynamic lookback windows.

### Break thresholds
- `BoS min fraction of candle range` (`breakMinFrac`): required body displacement beyond BoS reference.
- `CHoCH min fraction of candle range` (`chochBreakMinFrac`): required body displacement for CHoCH.
- `BoS requires fresh cross of validated ref`: avoids repeated BoS on consecutive closes above/below same ref.

### Gate / continuation (advanced)
- `strictGating`: if on, BoS/CHoCH can be deferred until candidate validation gate opens.
- `Enable Continuation Break (CB)`: marks deferred continuation breaks and can promote to BoS later.

### Visual controls
- `panelMode`: `off` | `minimal` | `full`
  - **off**: no panel
  - **minimal**: direction + BoS-confirmed status
  - **full**: full diagnostics
- `debugView`: enables internal overlays/noise tooling
- `Show internal validated labels (debug)`: internal iVH/iVL labels (only when debugView=true)
- `Show weak break dots`: weak-break markers (only when debugView=true)
- `Show BoS anchor labels (VL/VH)`: prints structural anchor labels on BoS
- `Show BoS break labels (BoS→VL/VH)`: labels the break candle when BoS is confirmed
- `Show CHoCH break labels (CHoCH↑/↓)`: labels break candle on CHoCH
- `Show CHoCH flip-anchor labels (FlipVH/FlipVL)`: labels structural flip-anchor point set on CHoCH

---

## How to read the chart

### Core markers
- **BoS**: green diamond marker (`BoS`) + optional break label (`BoS→VL` or `BoS→VH`)
- **CHoCH**: yellow marker (`CH`) + optional break label (`CHoCH↑` or `CHoCH↓`)
- **CB**: magenta square (`CB`) for deferred continuation while gate is closed

### Anchor labels
- **VL**: structural low anchor in bullish structure
- **VH**: structural high anchor in bearish structure
- **FlipVL / FlipVH**: anchor set at CHoCH transition window

### Lines
- Validated reference lines (directional)
- Active structural anchor line (directional)
- Candidate lines only in debug view

---

## Recommended operating profiles

### Profile A — Production visual review (default)
- `strictGating=false`
- `breakMinFrac=0.15`
- `chochBreakMinFrac=0.15`
- `panelMode=minimal`
- `debugView=false`

### Profile B — Sensitive calibration
- Same as above, but `breakMinFrac=0.05`
- Use only for sensitivity checks; expect more signals.

### Profile C — Deep debugging
- `panelMode=full`
- `debugView=true`
- Optional: toggle strict gate for controlled A/B replay tests.

---

## Replay/testing notes

- Do not compare strict ON/OFF by toggling mid-replay.
- Run separate replay passes from the same start point for fair comparison.
- During validation, capture before/at/after bars for any disputed BoS/CHoCH event.

---

## Known intent boundaries

- This indicator certifies **HTF structure logic**.
- Trade sizing/risk handling from `transitional` belongs to downstream analytics/execution engines.
- Use this indicator as structure truth input; not as complete execution policy.

---

## Companion docs

- `../spec/phases/PHASE1_HTF_STRUCTURE_CERT_PLAN.md`
- `../spec/phases/PHASE1_DECISION_FORK_BOS_CONTINUATION.md`
