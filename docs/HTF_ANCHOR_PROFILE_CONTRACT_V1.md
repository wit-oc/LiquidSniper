# HTF Anchor Profile Contract (v1)

Status: Scaffold (Task 14 kickoff, 2026-02-18)  
Scope: Deterministic anchor-profile contract for paper/simulation decisioning only.

---

## 1) Purpose

This document defines the canonical profile contract for HTF-anchored strategy runs so every analysis execution is:
- profile-tagged,
- schema-validatable,
- replay-auditable,
- fail-closed when profile/timeframe constraints are invalid.

This is a **paper-mode contract scaffold**. It does not authorize live execution.

---

## 2) Profile IDs and default anchors (v1)

Canonical profile set:

- `S` (Swing)
  - `htf_anchor_tf`: `1D`
  - `itf_tf`: `4H`
  - `ltf_trigger_tfs`: `["1H", "15m"]`
- `I` (Intraday)
  - `htf_anchor_tf`: `4H`
  - `itf_tf`: `1H`
  - `ltf_trigger_tfs`: `["15m", "5m"]`
- `C` (Scalp)
  - `htf_anchor_tf`: `1H`
  - `itf_tf`: `15m`
  - `ltf_trigger_tfs`: `["5m", "1m"]`

Default paper-MVP focus profiles for immediate fixture parity:
- `S` (`1D` anchor)
- `C` (`1H` anchor)

---

## 3) Required analysis payload fields

Every analysis run MUST include:

- `anchor_profile_id` (`S|I|C`)
- `htf_anchor_tf`
- `itf_tf`
- `ltf_trigger_tfs`
- `regime_permission` (`allow|deny|degrade`)
- `regime_reason_codes` (string array; deterministic reasons)
- `rulebook_ref` (doc/version pin)
- `policy_version`
- `trace_id`

If any required field is missing, the run is invalid and must fail closed to non-promoted output (`reject` or `watch_only` per rulebook policy).

---

## 4) Validation constraints (deterministic)

A profile selection is valid only when all constraints pass:

1. **Profile ID validity**
   - `anchor_profile_id` must be one of `S|I|C`.

2. **Exact timeframe mapping**
   - `htf_anchor_tf`, `itf_tf`, and `ltf_trigger_tfs` must exactly match the selected canonical profile in §2.

3. **Hierarchy ordering**
   - Timeframes must satisfy strict ordering: `HTF > ITF > each LTF trigger`.

4. **Trigger set bounds**
   - `ltf_trigger_tfs` must contain 1-2 items and all must belong to the profile default set.

5. **Regime gate presence**
   - `regime_permission` and non-empty `regime_reason_codes` are mandatory.

6. **Version pinning**
   - `rulebook_ref` and `policy_version` must be present and non-empty.

7. **Fail-closed behavior**
   - Any invalid combination or missing field must block promotion beyond paper/simulation semantics.

---

## 5) Regime-permission contract

`regime_permission` semantics:

- `allow`: structural regime conditions permit normal profile evaluation.
- `degrade`: profile is partially permitted; confidence/promotion tier must be reduced and reason-coded.
- `deny`: profile is not tradable under current regime context; decision must not promote.

Rule:
- `deny` always blocks candidate promotion regardless of secondary confluence score.

---

## 6) Replay fixture minimums (Task 14 acceptance hook)

At minimum, replay coverage must include:

1. One valid `S` profile fixture (`1D` anchor path).
2. One valid `C` profile fixture (`1H` anchor path).
3. One invalid profile/timeframe mismatch fixture that deterministically rejects.

Fixture artifacts should include:
- input payload,
- validation result,
- deterministic reason codes,
- final decision tier.

---

## 7) Promotion boundary and safety

- This contract is authoritative for profile validation in paper-mode MVP.
- No live trading actions are implied or enabled by this document.
- Any unresolved operator dependency stubs (credentials/egress/allowlist/signoff) remain hard blockers for progression beyond paper.

---

## 8) Implementation handoff notes

Downstream docs/tasks expected to consume this scaffold:
- `docs/TRADING_STRATEGY_RUNBOOK_V1.md`
- `tasks/14_htf_anchor_rulebook_contract.md`
- `tasks/15_*` score mapping contract work
- adversarial validation artifacts (Task 17)

This scaffold intentionally locks profile defaults and validation behavior before score-mapping expansion.