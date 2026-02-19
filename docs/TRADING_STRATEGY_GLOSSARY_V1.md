# LiquidSniper Trading Strategy Glossary (v1)

Status: canonical terminology companion for `docs/TRADING_STRATEGY_RUNBOOK_V1.md`  
Scope: paper/simulation decisioning vocabulary only (no live-execution authority)

---

## Purpose

This glossary standardizes trading-strategy terms used across:
- `docs/TRADING_STRATEGY_RUNBOOK_V1.md`
- `docs/HTF_ANCHOR_PROFILE_CONTRACT_V1.md`
- `docs/HYBRID_CONFLUENCE_PIPELINE_SPEC.md`
- `docs/TASK14_15_HTF_SCORE_PAYLOAD_MAPPING.md`

Use these definitions in code, tests, fixtures, and operator notes to keep decisions deterministic and replay-safe.

---

## A) Core strategy terms

- **Confluence**  
  Combined evidence from multiple independent signals. In LiquidSniper, confluence is policy-gated and never indicator-singleton.

- **Primary confluences (hard gates)**  
  Required pair:
  1. Support/Resistance first retest
  2. Market structure alignment (BoS/CHoCH)

- **Secondary confluences (confidence boosters)**  
  Ranked set used for tiering once primaries pass:
  1. Fibonacci level alignment
  2. Trend line alignment
  3. Liquidity alert context
  4. VWAP alignment
  5. EMA200 alignment

- **Decision core**  
  The deterministic rule path that maps validated inputs to `decision_tier`.

- **Annotation-only signal**  
  A captured signal that may be logged for context but is not allowed to change decision tier (e.g., order blocks in current policy).

---

## B) Structure and regime terms

- **BoS (Break of Structure)**  
  Price confirms continuation by breaking a prior structural point in trend direction.

- **CHoCH (Change of Character)**  
  Structural transition signal indicating potential regime shift versus prior structure behavior.

- **Regime permission** (`allow|degrade|deny`)  
  Policy control for whether a profile may promote:
  - `allow`: normal tiering behavior
  - `degrade`: cap promotion (max `publish_candidate`)
  - `deny`: block promotion (force non-promoted result)

- **Regime reason codes**  
  Deterministic machine-readable reasons attached to `regime_permission` outcomes.

---

## C) Timeframe model terms

- **HTF (Higher Timeframe)**  
  Anchor timeframe defining dominant context.

- **ITF (Intermediate Timeframe)**  
  Bridge timeframe between HTF context and LTF trigger behavior.

- **LTF (Lower Timeframe)**  
  Trigger timeframes used for local execution-context validation.

- **Anchor profile**  
  Canonical timeframe bundle:
  - `S` (Swing): `1D / 4H / [1H,15m]`
  - `I` (Intraday): `4H / 1H / [15m,5m]`
  - `C` (Scalp): `1H / 15m / [5m,1m]`

- **Hierarchy guard**  
  Validation rule requiring strict order: `HTF > ITF > each LTF`.

---

## D) Scoring and decision terms

- **Zone priority score** (`zone_priority_score`)  
  Stage-A score (0–100) reflecting liquidity/zone relevance.

- **Context score** (`context_score`)  
  Stage-B score (0–100) reflecting MTF context quality.

- **Pre-score** (`pre_score`)  
  Deterministic weighted baseline: `0.55*zone + 0.45*context`.

- **Agent confidence score** (`agent_confidence_score`)  
  Optional Stage-C qualitative score; may be zeroed if stage is not eligible.

- **Final score** (`final_score`)  
  Weighted result: `0.70*pre_score + 0.30*agent_confidence_score_effective`.

- **Decision floor**  
  Guardrail that forces `watch_only` when `pre_score < 60` (or when regime denies).

- **Decision tier** (`decision_tier`)  
  Canonical output state:
  - `reject`
  - `watch_only`
  - `publish_candidate`
  - `high_priority`

- **Runbook confluence override**  
  Priority gate where failed primaries prevent score-based promotion.

---

## E) Required payload field terms

- **`anchor_profile_id`**  
  Profile enum (`S|I|C`) selecting canonical timeframe contract.

- **`htf_anchor_tf` / `itf_tf` / `ltf_trigger_tfs`**  
  Profile-bound timeframe fields; must match canonical map.

- **`runbook_primary_ok`**  
  Boolean indicating both primary confluences passed.

- **`runbook_secondary_hits`**  
  Integer count of matched secondary confluences.

- **`rulebook_ref`**  
  Version pin to strategy/rulebook document used for decisioning.

- **`policy_version`**  
  Version pin for machine policy/contract semantics.

- **`trace_id`**  
  Stable execution identifier for replay/audit linkage.

- **`decision_reason_codes`**  
  Ordered, deterministic reasons explaining final decision tier.

---

## F) Safety and operations terms

- **Paper mode / simulation mode**  
  Non-live decision workflow producing auditable artifacts only.

- **Fail-closed**  
  On missing/invalid critical fields, system must block promotion and return safe non-promoted outcome.

- **Replay-safe**  
  Identical inputs produce identical outputs and reason codes.

- **Deterministic**  
  No discretionary runtime branches that can alter decision outcome for same input payload.

---

## G) Clarifications and non-goals (v1)

- This glossary does **not** authorize live order routing.
- This glossary does **not** define execution adapter behavior.
- This glossary does **not** optimize thresholds; it standardizes vocabulary used by existing contracts.

---

## H) Change control

When strategy semantics change, update in lockstep:
1. `TRADING_STRATEGY_RUNBOOK_V1.md`
2. `HTF_ANCHOR_PROFILE_CONTRACT_V1.md`
3. `TASK14_15_HTF_SCORE_PAYLOAD_MAPPING.md`
4. This glossary file

Versioning rule: bump glossary version when term meaning changes (not for typo-only edits).
