# Phase 2: Enrichment + correlation (design)

Phase 1 gives us a clean, trustworthy **signal stream**.

Phase 2 turns that stream into something evaluable and increasingly actionable:

- enrich each signal with external context
- compute outcome metrics (MFE/MAE, etc.)
- build correlation signals (multi-exchange clusters, liquidation heat, etc.)

This phase still does **not** place trades.

---

## A) Market data enrichment (baseline)

Attach read-only market context at/after `ts_alert`:

- spot/perp price candles for the symbol
- volatility proxy (e.g., 5m range / ATR proxy)
- spread proxy (if available)

Derived metrics per event:
- **MFE** (max favorable excursion) over windows: 30s / 2m / 5m / 15m
- **MAE** (max adverse excursion) over same windows
- time-to-MFE / time-to-MAE

Purpose:
- quantify whether an alert tends to yield a tradable move
- inform TP/SL templates

---

## B) Mobchart multi-exchange correlation

Because Mobchart levels are exchange-specific, we want to score “clusters”:

- group recent events by `symbol` + `side`
- cluster by `level_price` within a tolerance (e.g., 0.1% or configurable)
- score each cluster by:
  - number of distinct venues
  - sum/median of `liquidity_size_usd`
  - strength bucket distribution
  - age distribution

Output:
- `ClusterCandidate` records (still not a trade)

---

## C) Coinglass liquidation context (optional enrichment)

### Motivation

Liquidation “heat” can serve as a confirmation layer:

- high liquidation concentration near a price zone
- aligned with a Mobchart liquidity level
- combined with directional interest can raise confidence

### Important caveat

Coinglass liquidation data is typically derived from **positions opened** over a lookback window (1d/7d/30d). It does **not** guarantee:

- those exact liquidation levels are still active
- that liquidation will occur at those levels

So it should be treated as a **probabilistic prior**, not ground truth.

### Proposed usage

Add fields (enrichment record):
- `coinglass.lookback`: `1d|7d|30d`
- `coinglass.liq_heat_levels`: list of { price, intensity, side }
- `coinglass.liq_heat_near_level`: intensity within tolerance of Mobchart `level_price`

Then incorporate into a composite score:

- `confidence_score = f(mobchart_cluster_score, liq_heat_score, volatility_regime, ...)`

### Implementation note

Treat Coinglass as a plug-in enrichment provider:
- ingest should be resilient to API failures
- cache results per symbol/time bucket
- keep API keys out of the core ingestor when possible

---

## Outputs of Phase 2

- enriched events dataset
- cluster candidates dataset
- evaluation reports (which signal settings / thresholds correlate with better outcomes)

Phase 3 (execution) consumes only the **best-defined, safest** artifacts (likely cluster candidates + TP/SL templates) and still must run in an isolated container.
