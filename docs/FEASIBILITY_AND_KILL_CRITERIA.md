# LiquidSniper — Feasibility & Kill Criteria

## Purpose

Prevent sunk-cost drift by evaluating LiquidSniper as a **time-boxed experiment**.

This project proceeds only if measured outcomes pass pre-defined thresholds.

---

## Scope of evaluation

We evaluate three stages:

1. **Baseline**: raw Mobchart liquidity alerts only
2. **Phase 2A confluences**: HTF regime + S/R retest + ATR-normalized distance + size percentile + session bucket
3. **Phase 2B+ confluences**: trendline proxy, VWAP/fib/EMA, optional funding/OI

---

## Hard gates (must pass)

## Gate A — Data quality

Timebox: first 3–5 days of continuous collection.

Must meet:
- >= 95% of incoming alerts persisted to raw store
- >= 90% of lines parsed into valid `signal_event` rows
- <= 2% duplicate event inflation after dedupe
- timestamps and symbol fields present for >= 99% of parsed rows

If fail:
- fix ingestion/parser first; no strategy claims allowed.

## Gate B — Labeling integrity

Timebox: once >= 300 events available.

Must meet:
- deterministic label pipeline produces MFE/MAE + outcome labels for >= 95% of events
- fee/slippage assumptions explicitly parameterized
- rerun on same data yields identical results

If fail:
- stop model experiments; fix labeling reproducibility.

## Gate C — Baseline realism check

Timebox: after Gate B.

Measure baseline expectancy using raw Mobchart alerts.

Expected: likely weak/negative net edge.

Pass condition is not profitability here; pass condition is:
- baseline report is stable and reproducible
- confidence intervals shown, not just point estimates

If fail:
- no further confluence work until baseline pipeline is trustworthy.

## Gate D — Confluence lift

Timebox: 1 week after Phase 2A features implemented.

Primary criterion:
- confluence-filtered subset must improve net expectancy vs baseline by a meaningful margin

Suggested threshold (adjustable):
- >= 20% relative improvement in expectancy
- and higher win/loss asymmetry after fees/slippage

Robustness criteria:
- improvement observed across multiple symbols and at least 2 sessions (e.g., EU/US)
- no single-symbol dominance > 40% of total edge contribution

If fail:
- do not proceed to execution ideas; either pivot to decision-support tool or sunset.

## Gate E — Stability / overfit check

Timebox: after Gate D pass.

Must meet:
- walk-forward split performance does not collapse (train/test regime consistency)
- no severe metric inversion in adjacent time windows

If fail:
- treat as overfit; redesign features or stop.

---

## Time-box and stop rules

## Total research budget

- **Max 2 weeks** for feasibility verdict from now.

## Automatic stop triggers

Stop immediately if any occurs:
- data quality remains below Gate A after 2 focused fix cycles
- no measurable lift after 2 feature rounds (2A and 2B)
- net expectancy remains negative in realistic fee/slippage scenarios
- process complexity rises without measurable performance gain

---

## Decision outcomes

At end of timebox, choose one:

1. **GO**
- Gates A–E passed; continue buildout

2. **PIVOT**
- No tradable edge, but useful as discretionary decision-support/journaling platform

3. **NO-GO / SUNSET**
- Insufficient edge and no high-value pivot

---

## MVP v1 scorecard (today's execution baseline)

This is the concrete first-pass scorecard we use while implementing MVP tasks.

### Required metrics (must be computable)

- **Signal quality proxy**
  - Hit-rate proxy at configured horizon(s)
  - Expectancy per signal after fees/slippage assumptions
- **Risk profile**
  - Max drawdown proxy (paper-trade replay)
  - MAE/MFE distribution snapshots
- **Operational quality**
  - End-to-end latency: alert ingest -> scored signal -> outbound payload
  - Parsing success rate and adapter status coverage

### Initial acceptance thresholds (v1)

These are intentionally pragmatic for a first pass; tighten after first 1-2 replay cycles.

- Parsing success rate: **>= 90%**
- Adapter status contract coverage (`ok|unavailable|auth_required|failed`): **100% path-tested**
- End-to-end p95 latency: **<= 15s** in local dry-run harness
- Replay determinism: same fixture run produces identical scores/payloads: **100%**
- Expectancy: **not materially negative** after configured fees/slippage on replay set
  - (if negative beyond tolerance, trigger immediate threshold/feature review)

### Kill criteria (v1-fast)

Stop or pivot this MVP lane if any persist after 2 fix iterations:

- replay harness cannot be made deterministic,
- adapter contract/state handling remains flaky,
- expectancy stays clearly negative under realistic assumptions,
- latency/error profile makes reliable delivery impractical.

---

## Reporting template (weekly)

Required sections:
- data quality metrics
- baseline performance summary
- confluence-lift deltas
- robustness checks
- recommendation: go / pivot / stop

Keep all claims tied to metrics + confidence intervals.
