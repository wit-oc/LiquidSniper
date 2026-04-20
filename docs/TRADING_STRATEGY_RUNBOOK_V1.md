# LiquidSniper Trading Strategy Runbook v1.1

Status: **Bridge version (deterministic + HTF-anchor ready)**

This runbook upgrades the earlier stub into a strategy foundation that can drive automated decisioning while keeping strict safety/risk boundaries.

---

## 1) Scope

Defines the confluence and structure rules that the LiquidSniper analysis pipeline should treat as the core strategy foundation.

This runbook is for:
- simulation and paper decisioning now,
- constrained live design preparation,
- deterministic replay/audit.

This runbook is **not** permission to auto-execute live trades.

Companion terminology reference: `docs/TRADING_STRATEGY_GLOSSARY_V1.md`.

---

## 2) Core strategy thesis

Trade qualification is top-down and confluence-weighted:

1. Regime permission (HTF anchor context)
2. Structure/location validation
3. Trigger confirmation
4. Risk gate authority (final say)

No single indicator is sufficient.

---

## 3) HTF-anchor model (new baseline)

## Assumption check

The framework is largely fractal and can be re-anchored (e.g., `HTF=1D` vs `HTF=1H`) **with constraints**.

### Constraints (mandatory)

1. Preserve timeframe hierarchy spacing (e.g., HTF -> ITF -> LTF).
2. Recompute cost and viability per profile (do not reuse thresholds blindly).
3. Use tighter risk caps for smaller anchors.
4. Require profile-specific replay validation before promotion.

### Anchor profiles (v1 defaults)

- **Swing profile:** HTF `1D`, ITF `4H`, trigger `1H/15m`
- **Intraday profile:** HTF `4H`, ITF `1H`, trigger `15m/5m`
- **Scalp profile:** HTF `1H`, ITF `15m`, trigger `5m/1m`

Decision payloads must include:
- `anchor_profile_id`
- `htf_anchor_tf`

---

## 4) Confluence policy (decision core)

## Primary confluences (hard gates)

1. **HTF bias permission** (BoS/CHoCH interpreted as bias mechanism: `long|short|neutral`)
2. **Support/Resistance first retest** from SR Engine V2 nearest eligible structural zones (HTF/ITF policy-eligible TFs only)
3. **Secondary confluence minimum** (profile-configured)

BoS/CHoCH is no longer a direct entry hard gate; it is used to classify bias context.

## Secondary confluences (ranked)

1. Fibonacci levels
2. Trend lines
3. Liquidity alerts
4. VWAP
5. EMA200

Secondary confluences increase confidence only; they cannot rescue failed primary gates.

## Excluded from decision core (annotation only)

- Order blocks
- Supply zones
- Similar zone-taxonomy variants not yet validated

---

## 5) Deterministic qualification logic

## Current runtime policy (implemented)

Entry gate order is deterministic:
1. `bias_permission` (expected side must match profile bias output)
2. `sr_first_retest` from SR Engine V2 query (`confirmed` zone + profile anchor eligibility + first/deviation-retest state)
3. `secondary_confluence` threshold
4. throttle/risk checks (daily cap, cooldown, active-risk cap)

Tiering after pass:
- 0-1 secondary hits -> `watch_only`
- 2-3 secondary hits -> `publish_candidate`
- 4-5 secondary hits -> `high_priority`

## Planned extension (tracked)

Add explicit regime-permission gate from anchor profile context before promotion.

---

## 6) Risk posture (current)

- No autonomous live execution in this runbook scope.
- Simulation and paper-trade journaling only.
- BE-aware active-risk cap enforced: `LIQUIDSNIPER_MAX_ACTIVE_RISK_POSITIONS=2` counts only open positions still in `stop_state=initial|trailing`.
- TP1 promotion to `stop_state=be` reduces active-risk usage without forcing immediate close.
- Keep hard guardrails from:
  - `docs/FEASIBILITY_AND_KILL_CRITERIA.md`
  - `docs/archive/2026-04-19-first-archive-pass/paper-runtime/GO_NO_GO_CHECKLIST.md`

---

## 7) Required decision payload fields (for automation)

At minimum, each candidate decision should carry:
- `symbol`
- `anchor_profile_id`
- `htf_anchor_tf`
- `runbook_primary_ok`
- `runbook_secondary_hits`
- `final_score`
- `decision`
- `rulebook_ref`
- `policy_version`

This preserves replayability and audit traceability.

---

## 8) Open action items linked to this runbook

1. Define schema contract for HTF-anchor profiles and regime permissions.
2. Map lecture-derived scoring buckets into deterministic payload fields.
3. Add profile-specific replay fixtures (1D-anchor and 1H-anchor cases).
4. Run adversarial validation before any progression beyond simulation/paper influence.

---

## 9) Notes on source strategy materials

This runbook is intentionally deterministic and implementation-oriented.
Lecture-derived strategy material can inform weighting and context, but production decisioning must remain schema-driven, replayable, and policy-gated.
