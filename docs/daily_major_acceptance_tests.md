# Daily Major Acceptance Tests

Status: draft for Phase 2 shadow-mode migration  
Branch: `phase2-zone-engine-v3`

## 1) Purpose

These tests define what it means for the **Daily major** surface to be acceptable in Phase 2 shadow mode.

They are intentionally **deterministic and doctrine-first**.
They are not a tuning worksheet.
They do not authorize symbol-specific overrides.
They exist to answer one question:

**Does Daily major selection reliably produce sparse, structural higher-timeframe anchors without degrading into reaction-score clutter?**

## 2) Scope

This document covers only the **Daily major** selector surface.

It does not validate:
- 4H operational usefulness in full
- nearest-four payload parity in full
- score-weight optimality
- per-symbol tuning

Those belong to separate review steps.

## 3) Test philosophy

The selector passes only if it demonstrates all of the following:
- **structural priority** over mere proximity or reaction popularity
- **sparsity** appropriate for higher-timeframe map review
- **determinism** for the same input set
- **explainability** through selector reasons and provenance
- **cross-symbol generality** without BTC-only hacks

## 4) Roles for the Phase 2 acceptance set

Use two roles, not two doctrine trees:
- **BTC diagnostic case** — the primary high-signal inspection case used to study keep/drop reasoning in detail
- **ETH blind-check case** — the anti-overfit check used to ensure the selector behavior generalizes without symbol-specific rescue logic

Rule:
The ETH case must be evaluated using the same selector doctrine and acceptance rules as BTC.
If BTC passes only because of implicit BTC behavior, the suite fails.

## 5) Required test inputs

For each symbol under test, the review artifact must include:
- canonical Zone Schema V2 candidate/merged-zone set
- Daily selector output
- compact keep/drop trace fields
- source-family provenance
- structural bounds for kept zones
- comparison view against baseline Daily-style anchors when available

Minimum fields required in the review record for each kept zone:
- `zone_id`
- `symbol`
- `tf`
- `zone_kind`
- `status`
- `zone_low`
- `zone_high`
- `zone_mid`
- `candidate_family`
- `candidate_sources`
- `merge_family_count`
- `selector_status`
- `selector_reason`
- `selector_rank`

## 6) Core acceptance criteria

### AC1 — Daily majors are sparse

For a given review snapshot, Daily major output must be visibly sparse relative to the full candidate set.

Pass conditions:
- output is small enough to read as a higher-timeframe map rather than an operational ladder
- kept zones are materially fewer than the eligible canonical candidate set
- selector reasons do not justify keeping multiple near-duplicate anchors without a clear structural distinction

Fail signals:
- dense stacks of adjacent zones
- output that resembles 4H operational density
- multiple zones kept primarily because they scored well despite serving the same structural role

### AC2 — Structural doctrine is visible

Daily major output must privilege structural anchors.

Pass conditions:
- kept zones are mostly `1D`-role or clearly higher-timeframe-relevant anchors
- structure-family participation is present in the kept set unless the input genuinely lacks credible structure candidates
- if a non-structure zone is kept, the reason explains why it acts as a durable macro anchor

Fail signals:
- reaction-only dominance with no explicit explanation
- selection that reads like "top scores near important price" rather than structural mapping
- repeated preference for tactical bands over broader anchors

### AC3 — Selector does not chase proximity

Daily major must remain useful even when price is not close to the selected anchors.

Pass conditions:
- at least some kept anchors are justified by structural role rather than immediate price distance
- selector reasons reference anchor quality, durability, or map role—not just closeness

Fail signals:
- output changes primarily because price moved slightly inside the surrounding regime
- chosen anchors cluster around current price as if Daily major were an execution surface

### AC4 — Keep/drop reasons are auditably concrete

Every kept Daily major zone must carry a compact reason that explains the doctrinal role.

Pass conditions:
- each kept zone has a readable reason such as structural anchor, family-fused macro level, or durable higher-timeframe bound
- dropped candidates near the cut line can be distinguished from kept ones by reason, not just rank

Fail signals:
- empty or generic reasons like `high score`
- reasons that require reverse-engineering hidden thresholds
- no explanation for why one overlapping zone beat another

### AC5 — Deterministic output

For the same input candidate set, the selector must produce the same Daily major output and ordering.

Pass conditions:
- repeated evaluation on identical input returns the same kept zone ids and ranks
- tie-break behavior is stable and rule-based

Fail signals:
- unstable ordering across repeated runs
- arbitrary changes in near-equal candidates without documented tie-break rules

### AC6 — No symbol-specific overrides

The Daily major selector must generalize.

Pass conditions:
- BTC diagnostic and ETH blind-check both evaluate under the same rules
- no per-symbol threshold branches are required for acceptance
- selector reasons use doctrinal concepts, not symbol names

Fail signals:
- BTC passes only after special casing
- ETH requires manual reinterpretation of the rules
- acceptance language includes hidden symbol-specific exceptions

## 7) BTC diagnostic case

BTC is the detailed inspection case.
The goal is not to make BTC look good at any cost.
The goal is to make selector behavior legible.

Required review questions:
1. Did the selector keep sparse higher-timeframe anchors?
2. Did structure or family fusion visibly outrank reaction-only clutter?
3. Were any dropped high-score reaction candidates correctly excluded as too tactical or too dense?
4. Do kept-zone reasons explain the map in plain English?
5. If BTC differs from baseline expectations, is the difference explainable as doctrine improvement rather than drift?

BTC-specific deliverable for acceptance:
- a short comparison note describing why each kept zone belongs on the Daily map
- at least one example of a plausible candidate that was correctly dropped

Important rule:
BTC is a **diagnostic lens**, not permission to add BTC-only logic.

## 8) ETH blind-check case

ETH is the anti-overfit case.
Run the same Daily major doctrine without symbol-specific rescue rules.

Required review questions:
1. Does the selector still produce sparse structural anchors?
2. Does it avoid collapsing into reaction-score clutter?
3. Are keep/drop reasons still coherent without hand-tuned BTC assumptions?
4. Would a reviewer who never saw BTC still recognize the output as a Daily major map?

ETH passes only if:
- the selector remains structurally legible
- no special-case logic is required
- any weakness is explained as a doctrine gap or input gap, not patched ad hoc

## 9) Comparison rules against baseline

Where a baseline Daily-style reference exists, compare using these categories:
- `cleaner` — fewer but better structural anchors
- `equivalent` — same essential anchors with better provenance/explanation
- `noisier` — more clutter without better map value
- `drifted` — materially different anchors without clear doctrinal justification

Acceptance bias:
- `cleaner` or `equivalent` is acceptable
- `noisier` or unexplained `drifted` is a fail

## 10) Required failure reporting

If the selector fails, record the failure in doctrine terms.
Not tuning terms.

Examples of acceptable failure statements:
- `Daily major over-selected reaction-family tactical bands and lost macro sparsity.`
- `ETH blind-check showed symbol-generalization failure despite acceptable BTC diagnostics.`
- `Selector reasons were too weak to explain why overlapping candidates were kept or dropped.`

Examples of unacceptable failure reporting:
- `Needs more tuning.`
- `BTC looked kind of off.`
- `Maybe increase threshold.`

## 11) Minimum pass bar for Phase 2

Phase 2 Daily major acceptance is met only if all of the following are true:
- BTC diagnostic case passes AC1 through AC6
- ETH blind-check passes AC1 through AC6 under the same doctrine
- no symbol-specific override is introduced
- selector reasons are present and human-legible
- review shows Daily major is not merely nearest-high-score output with a better label

## 12) What this suite intentionally does not settle

This suite does not settle:
- exact number of Daily majors to keep
- exact scoring formulas
- whether one family should always outrank another numerically
- production cutover timing

Those are downstream decisions.
This suite only answers whether the Daily major selector is doctrinally acceptable for shadow-mode comparison.

## 13) Summary

A passing Phase 2 Daily major selector must:
- stay sparse
- look structural
- explain itself
- behave deterministically
- survive an ETH blind-check without BTC crutches

If it cannot do that, it is not ready for promotion, no matter how persuasive a few charts look.
