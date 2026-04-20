# Hybrid Confluence Pipeline Spec (Legacy v0)

Archived from stale branch `task-03-mobchart-parser` during the 2026-04-19 Surveyor / Arbiter refocus.

Why archived:
- it captures a historically interesting OpenClaw + deterministic-analysis concept
- but it is anchored to an older Mobchart / TradingView-heavy repo identity, not the current Surveyor / Arbiter center

---

## Intent

Combine LiquidSniper’s deterministic liquidity-zone pipeline with OpenClaw agent-driven qualitative analysis.

Design goal:
- **Backend intelligence first** (event stream + scoring + agent decisions)
- **UI second** (debug terminal, auditability, manual override)

---

## 1) System shape (practical)

### A) Deterministic analysis engine (always-on)

Input:
- Mobchart signal stream (Telegram ingested)
- OHLCV multi-timeframe data
- optional perp metadata (later)

Output:
- candidate symbol cards
- quantitative confluence features
- preliminary score

### B) OpenClaw analysis agent (event-driven)

Triggered only for top candidates.

Responsibilities:
- pull latest context package
- optionally fetch TradingView screenshots (15m/1h/4h/1D/1W)
- run qualitative rubric over deterministic + screenshot context
- produce final thesis + confidence + watch/act recommendation

### C) Delivery layer

Primary delivery:
- post high-quality candidate signals to configured channel

Secondary delivery:
- lightweight debug UI + raw feed explorer for development/validation

---

## 2) Why this architecture

- Avoid overinvesting in frontend polish before edge is proven.
- Keep critical logic deterministic and testable.
- Use agent reasoning where it adds value (context synthesis), not as sole signal source.
- Preserve full audit trail for every recommendation.

---

## 3) Pipeline stages

## Stage 1 — Zone candidate generation (deterministic)

For each signal event:
- normalize size/distance/venue context
- attach to symbol card
- compute Zone Priority features:
  - liquidity_size_percentile
  - distance_to_level_atr_norm
  - cross_venue_cluster_count
  - freshness decay

Output:
- `zone_priority_score` (0–100)

## Stage 2 — Multi-timeframe context features (deterministic)

Compute on 15m/1h/4h/1D/1W:
- HTF trend regime
- structure state (trend/range/transition)
- S/R proximity + first-retest flag
- local structure shift proxy (LTF)
- volatility regime

Output:
- `context_score` (0–100)

## Stage 3 — Agent qualitative pass (conditional)

Run only if score threshold reached (see §5).

Agent receives:
- structured feature packet
- optional TradingView screenshots
- explicit strategy rubric from user

Agent outputs:
- `thesis_summary`
- `reaction_plan` (what must happen at level)
- suggested `entry_zone`, `stop_zone`, `tp_final_zone`
- `agent_confidence_score` (0–100)
- `confidence_rationale` (feature contribution + caveats)

## Stage 4 — Signal publication

If final threshold met:
- publish to channel with concise thesis + risk box
- include links to artifacts (see §6)

Else:
- keep record in debug feed only

---

## 4) Scoring model v0

Two-tier scoring:

1) **Pre-agent score**
- `pre_score = 0.55*zone_priority + 0.45*context_score`

2) **Post-agent score**
- `final_score = 0.7*pre_score + 0.3*agent_confidence`

Agent cannot rescue poor deterministic setups entirely:
- hard floor: if `pre_score < pre_floor`, force `watch_only`.

All weights are provisional and must be recalibrated with outcome data.

---

## 5) Trigger thresholds (initial)

- Run MTF context stage for any card with `zone_priority >= 45`
- Run agent pass for any card with `pre_score >= 60`
- Publish candidate only if `final_score >= 70`
- Mark `high_priority` if `final_score >= 80`

These are bootstrapping thresholds; tune from observed precision/recall.

---

## 6) TradingView screenshot artifacts in UI + messages

Requirement:
- Store screenshot artifacts and expose **clickable links** in UI and signal messages.

For each analysis run, store:
- timeframe
- capture timestamp
- source URL (TradingView chart link)
- image artifact path/object URL
- analysis_run_id

UI should show:
- card-level list of latest analysis runs
- per-run screenshot links for each timeframe
- “what the agent saw at decision time” view

Message payload should include:
- compact list of timeframe screenshot links (or one bundle link)

---

## 7) UI stance (minimal by design)

The UI is a **debug and audit terminal**, not the product center.

Must-have UI functions:
- raw signal feed explorer
- card list with score + state
- run history with artifacts and rationale
- manual status annotations

Defer:
- high-polish dashboards
- advanced custom visualizations

---

## 8) OpenClaw integration model

Two viable modes:

### Mode A — Background pipeline + channel delivery (recommended)
- analysis engine runs on schedule/event triggers
- specialized OpenClaw agent executes qualitative pass
- outputs posted to channel

### Mode B — Complex skill only
- OpenClaw skill orchestrates everything directly

Recommendation:
- start with Mode A for reliability + observability
- expose orchestration entrypoints as skills later for reuse/shareability

---

## 9) Data contracts (minimum)

`analysis_runs`
- id, symbol, trigger_event_id, ts_started, ts_completed
- zone_priority_score, context_score, agent_confidence, final_score
- decision (`publish|watch_only|reject`)
- thesis_summary, rationale_json

`screenshot_artifacts`
- id, analysis_run_id, timeframe, captured_ts
- tv_url, image_url_or_path, hash

`published_signals`
- id, analysis_run_id, channel, message_id, published_ts

---

## 10) Failure/fallback behavior

If TradingView capture fails:
- do not block deterministic scoring
- reduce confidence by penalty factor
- publish only if still above threshold and mark `tv_capture_missing`

If market data is stale:
- no publish; status `blocked_stale_data`

If agent pass fails:
- keep deterministic result in debug feed
- no publish unless explicit fallback policy enabled

---

## 11) Validation metrics

Track at minimum:
- candidate precision by score bucket
- outcome lift vs baseline Mobchart-only
- publish rate vs hit rate tradeoff
- false positive concentration by regime/symbol

Include confidence intervals and walk-forward splits.

---

## 12) Build sequencing implications

Before broad UI work:
1) finalize data contracts + scoring pipeline
2) implement artifact capture + storage
3) implement channel publication format
4) keep UI minimal but auditable

This keeps effort aligned with the real objective: reliable, high-signal opportunity surfacing.
