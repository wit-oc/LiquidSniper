# Phase 2 Confluence Research Spec (v0)

## Why this exists

Mobchart liquidity alerts are likely **zone candidates**, not standalone entry signals.
This spec defines a deterministic, low-cost research framework to discover which confluences are predictive.

## Core principle

No image analysis for v0.

Everything should be computed from OHLCV + alert stream + (optional) perp metadata.
Visual concepts (market structure, S/R, trendlines) are represented by explicit, reproducible rules.

---

## 1) Research question

**Under which market conditions do liquidity-zone alerts produce positive expectancy after fees/slippage?**

We evaluate conditional edge, not global hit rate.

---

## 2) Feature model: primary vs secondary confluences

### Primary confluences (hard gate features)

These define whether a setup is even eligible.

1. **Market structure regime** (deterministic)
   - HTF trend state from swing highs/lows (daily, weekly)
   - Labels: `uptrend | downtrend | range | transition`

2. **Support/Resistance interaction**
   - Programmatic pivot zones from HTF/LTF pivots
   - Distance of alert level to nearest HTF S/R zone
   - **First retest flag**: has this zone been touched since creation? (yes/no)

3. **Trendline retest proxy**
   - Deterministic trendline definition from pivot anchors
   - Breakout/breakdown event + retest within tolerance
   - Labels: `none | breakout_retest | breakdown_retest`

### Secondary confluences (score boosters)

1. Fib confluence
   - distance to major retracement levels from prior impulse
2. Dynamic levels
   - distance to 1D/4H QVWAP, YVWAP
   - distance to anchored VWAPs (ATH/ATL/event anchors)
3. EMA context
   - distance/position relative to 1D EMA12 and EMA200
4. Perp context (if futures)
   - funding bucket, OI change bucket
5. Alert-quality context
   - liquidity size percentile
   - distance-to-level normalized by ATR
   - venue agreement count (cross-exchange clustering)

---

## 3) Data required

Mandatory:
- Signal stream (Phase 1 events)
- OHLCV candles (1m, 5m, 1h, 4h, 1D, 1W)

Optional (Phase 2.1):
- funding rate snapshots
- OI deltas

---

## 4) Labeling and outcomes

For each alert event, compute forward-window outcomes:
- windows: 30s, 2m, 5m, 15m, 1h, 4h
- MFE, MAE
- level reaction type: `reject | absorb | break`
- strategy-style labels (template dependent):
  - `tp_hit_before_sl`
  - `sl_hit_before_tp`
  - `neither`

All labels should include fee + slippage assumptions.

---

## 5) Score model (v0)

Two-stage scoring:

1. **Primary gate** (boolean):
   - require structure alignment + first-retest + valid trendline state (configurable)

2. **Secondary score** (0–100):
   - weighted sum of standardized confluence features
   - initial weights heuristic; later replaced by learned weights from backtest stats

Output:
- `candidate_confidence_score`
- plus per-feature contribution table for explainability

---

## 6) Experiment plan

### Phase 2A (fastest path)

- Build deterministic feature extractors for:
  - HTF structure
  - S/R proximity + first retest
  - ATR-normalized distance
  - liquidity size percentile
- Run on 200–500 events
- Produce bucketed expectancy report

### Phase 2B

- Add trendline retest proxy + dynamic VWAP features + EMA features
- Re-run and compare lift over Phase 2A

### Phase 2C

- Add perp metadata (funding/OI)
- Re-run and compare incremental lift

---

## 7) Practical risk controls during research

Until confluence model is validated:
- treat trades as data collection
- smaller size
- fixed daily max attempts
- fixed daily max loss

---

## 8) Deliverables

1. `confluence_features` dataset (event-level)
2. `outcome_labels` dataset (event-window-level)
3. report notebook/script with:
   - expectancy by bucket
   - hit-rate by regime
   - score calibration chart
4. `confidence_v0` scoring function with documented weights

---

## 9) Important design stance

Your intuition is correct: many trader concepts are visual, but we should avoid image ML for now.

For v0:
- convert each visual rule into deterministic geometry/math on candle data,
- keep definitions explicit,
- and iterate based on measured lift.

If deterministic proxies fail, then we can justify higher-cost ML later.
