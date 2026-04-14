# Phase 2 S/R Timeframe Refinement Rules — 2026-03-24

## Purpose

Codify the refinement rules for the next timeframe-specific pass so implementation stays tightly scoped and does not drift into generic tuning.

This document is the concrete implementation anchor for:
- 1D core-band refinement
- 4H local consolidation / representative selection

It complements:
- `docs/PHASE2_SR_TIMEFRAME_REFINEMENT_MATRIX_2026-03-24.md`
- `docs/zone_schema_v2.md`
- `docs/selector_policy_v2.md`

---

## 1D refinement: macro bounds vs operator-facing core

### Problem
Current 1D zones often look directionally plausible but too broad to serve as clear operator-facing review levels.

### Goal
Preserve broad macro truth while surfacing a narrower operator-facing core.

### Rule set

#### 1D-R1 — Preserve macro bounds
Keep the existing broad 1D zone as the macro region of record.

Use fields:
- `zone_low`
- `zone_high`
- `zone_mid`

These remain the authoritative macro bounds.

#### 1D-R2 — Add explicit core bounds
Add narrower operator-facing fields inside the macro zone:
- `core_low`
- `core_high`
- `core_mid`

These fields must always satisfy:
- `zone_low <= core_low <= core_high <= zone_high`

#### 1D-R3 — Core extraction should be evidence-centered
Prefer a core derived from the strongest overlapping evidence rather than a naive midpoint cut.

Priority order for defining a 1D core:
1. overlapping multi-family evidence region
2. strongest provenance cluster / densest evidence sub-band
3. midpoint-centered fallback contraction if no better evidence-centered core exists

#### 1D-R4 — Core should be narrower than macro bounds by default
The 1D operator-facing core should usually be visibly narrower than the full macro band.

Exception:
- if evidence is genuinely broad and diffuse, preserve the wide core but record that explicitly as a review signal rather than pretending it is a crisp level.

#### 1D-R5 — Operator surfaces use core first, macro second
For the authoritative levels view:
- primary displayed bounds should be `core_*` when available
- macro bounds remain visible as secondary context / expandable detail

#### 1D-R6 — Do not drop macro zones just to make the operator view cleaner
This refinement is about **representation + operator usability**, not a blunt reduction in Daily inventory.

---

## 4H refinement: local consolidation / representative selection

### Problem
Current 4H levels are often directionally believable but too stacked near each other.

### Goal
Reduce same-side nearby clutter without deleting meaningful structure.

### Rule set

#### 4H-R1 — Consolidation should be local, not global
Do not reduce all 4H levels by a broad cap alone.

Instead, consolidate within local same-side neighborhoods.

#### 4H-R2 — Consolidate same-side near-neighbors first
Within a local neighborhood of nearby zones that share the same current role:
- select a representative level for the operator-facing surface
- preserve subordinate members as secondary/debug detail where possible

#### 4H-R3 — Preserve meaningful opposite-side separation
Do not collapse a support cluster into a resistance cluster just because they are both near price.

Consolidation is role-aware.

#### 4H-R4 — Prefer representative winners by evidence quality, not arbitrary nearest-only choice
When selecting a representative operational level, prefer:
- richer provenance / corroboration
- better selection score
- better local role clarity

Nearest-only ranking should not wipe out a clearly better nearby representative.

#### 4H-R5 — Authoritative operator view should show the cleaned representative set
The operator-facing 4H view should prioritize the representative set.

Raw/secondary nearby bands can remain available in debug/provenance surfaces.

---

## Contract implications

### Required surfaced fields
For the next implementation pass, authoritative outputs should expose:
- macro bounds: `zone_low/high/mid`
- operator-facing core (1D when available): `core_low/high/mid`
- role semantics: `current_role`, `relative_position`, `origin_kind`
- provenance: `candidate_families`, `family_provenance`

### UI implications
The authoritative view should show:
- 1D and 4H separately
- below / contains / above price
- lowest -> highest ordering
- current role as primary label
- core bounds first when available, macro bounds second

---

## Explicit non-goals for this tranche

Do not do these here:
- broad all-surface weight retuning
- symbol-specific overrides
- another architecture rewrite
- broad reduction of Daily or 4H inventory without role-aware/local evidence logic

---

## Success criteria

This tranche is successful if:
- 1D zones still feel like macro context, but operator-facing levels are sharper
- 4H still feels rich enough to navigate price, but clutter is visibly reduced
- BTC and ETH become easier to judge as good / borderline / wrong without long explanation chains
- remaining disagreements are specific enough to enter targeted config tweaking afterward
