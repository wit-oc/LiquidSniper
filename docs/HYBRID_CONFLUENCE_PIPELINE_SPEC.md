# Hybrid Confluence Pipeline Spec (v0)

## Intent

Combine LiquidSniper deterministic scoring with OpenClaw qualitative analysis.

Principle:
- backend intelligence first
- channel delivery first
- UI as diagnostic/audit terminal (not heavy product surface)

## 1) System components

1. Deterministic engine
- consumes signal events + market data
- computes zone/context/final scores
- writes analysis run + decision records

2. OpenClaw analysis agent (conditional)
- runs only for score-qualified candidates
- applies user rulebook to deterministic + screenshot context
- emits thesis + confidence + reaction plan

3. Delivery layer
- simulation-first (`would_alert` records)
- later optional live channel posting
- diagnostic UI for auditability and debugging

## 2) Pipeline stages

### Stage A — Zone priority
From liquidity events, compute:
- size percentile
- ATR-normalized distance
- cross-venue agreement
- freshness

Output: `zone_priority_score`

### Stage B — MTF context
For 15m/1h/4h/1D/1W compute:
- HTF regime
- structure state
- S/R proximity + first retest
- LTF structure-shift proxy
- volatility regime

Output: `context_score`

### Stage C — Agent pass (thresholded)
Input:
- structured feature packet
- optional TV screenshots
- external user rulebook

Output:
- thesis summary
- reaction plan
- suggested SL/TP zones
- `agent_confidence_score`

### Stage D — Decision
- `publish_candidate`
- `watch_only`
- `reject`

During early phases, publish is simulated only.

## 3) Scoring v0

- `pre_score = 0.55*zone_priority + 0.45*context_score`
- `final_score = 0.70*pre_score + 0.30*agent_confidence`

Guardrail:
- if `pre_score` below floor, force `watch_only` regardless of agent output.

## 4) Thresholds v0

- Run context stage if `zone_priority >= 45`
- Run agent stage if `pre_score >= 60`
- Mark `publish_candidate` if `final_score >= 70`
- Mark `high_priority` if `final_score >= 80`

## 4b) Runbook confluence gate (current override)

Current v1 runbook policy (stub) overrides score-only promotion:

Primary required (both):
- support/resistance first retest
- market structure alignment (BoS/CHoCH)

Secondary priority order:
1. fib
2. trendline
3. liquidity alert
4. vwap
5. ema200

Decision tiering with primary satisfied:
- 0–1 secondary hits => `watch_only`
- 2–3 secondary hits => `publish_candidate`
- 4–5 secondary hits => `high_priority`

Explicitly excluded from decision core (annotation-only):
- order blocks
- supply zones

### 4c) HTF-anchor profile contract (new baseline)

The confluence policy must be tagged by an anchor profile to make timeframe portability explicit and auditable.

Required fields per run:
- `anchor_profile_id` (`swing|intraday|scalp`)
- `htf_anchor_tf`
- `itf_tf`
- `ltf_trigger_tfs`

Assumption posture:
- strategy constructs are conditionally fractal across anchors,
- but costs, noise, and execution microstructure are not scale-invariant,
- therefore each anchor profile must maintain profile-specific risk/viability thresholds.

## 5) Screenshot artifacts in UI + messages

Store per analysis run:
- timeframe
- capture timestamp
- source chart URL
- local artifact path / URL
- hash

UI requirements:
- clickable links per timeframe
- "what agent saw at decision time" history
- clear marker for would-alert cards (e.g. `!`)

## 6) Failure/fallback

- TV capture fail: apply confidence penalty and tag `tv_capture_missing`
- stale market data: block publish decision
- agent pass fail: persist deterministic result; no live publish

## 7) Secrets + configuration model

All inputs parameterized.

- Secrets from keychain/secret manager -> env vars in memory at runtime
- No secrets in repo
- No user-specific defaults hardcoded in code

Examples:
- Telegram credentials/session path
- provider API keys
- channel route targets
- scoring thresholds
- artifact root path

## 8) Rulebook bootstrap (user-owned)

- Rulebook is external, user-provided at bootstrap
- Platform ships with schema/template, not a universal strategy
- Analysis runs store rulebook reference/version used

## 9) Shared mount contract

Backend and diagnostic UI share a mount (example: `/data/artifacts`) containing:
- screenshots
- run artifacts
- debug exports

Both services read/write via this mount to ensure local, auditable artifacts.

## 10) Metrics and validation

Track at minimum:
- candidate volume per day
- would-alert frequency by symbol/session
- precision by score bucket
- lift vs baseline Mobchart-only
- confidence intervals + walk-forward stability
