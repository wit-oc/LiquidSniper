# LiquidSniper — MVP Paper Path Sequence (v1)

Status: Proposed canonical execution order (2026-02-18)  
Owner: Redact + Wit  
Scope: reach an implementation-ready, auditable **paper-mode MVP** for the Blofin + on-chain strategy architecture.

---

## 1) What “MVP paper version” means (explicit)

For this sequence, MVP paper means:
- deterministic strategy scoring and candidate decisions are running end-to-end,
- no autonomous live order execution,
- outputs are auditable/replayable,
- guarded-pilot gates are evaluated from evidence,
- we can safely decide GO / HOLD / NO-GO for next stage.

---

## 2) Source-of-truth document set (accounting for created docs)

## A) Architecture / safety references

- `docs/ARCHITECTURE.md`
- `docs/MVP.md`
- `docs/MVP_ARCHITECTURE_DECISIONS.md`
- `docs/FEASIBILITY_AND_KILL_CRITERIA.md`
- `docs/trusted_trading_core_v0.md` (workspace-level, outside repo)
- `initiatives/artifacts/blofin-onchain-trading-bot-proposal-v1.md` (workspace-level, outside repo)

## B) Pipeline / runtime references

- `docs/HYBRID_CONFLUENCE_PIPELINE_SPEC.md`
- `docs/PHASE2_CONFLUENCE_RESEARCH_SPEC.md`
- `docs/OPENCLAW_ORCHESTRATION.md`
- `docs/TRADINGVIEW_ADAPTER_CONTRACT.md`
- `docs/SIGNAL_DELIVERY_AND_DRYRUN.md`
- `docs/GO_NO_GO_CHECKLIST.md`

## C) Strategy + alignment references

- `docs/TRADING_STRATEGY_RUNBOOK_V1.md`
- `docs/AUTOMATED_TRADING_AGENT_ALIGNMENT_V1.md`

## D) Task contracts

- `tasks/09_analysis_run_contract.md` ... `tasks/13_openclaw_skill_orchestration.md`
- `tasks/14_htf_anchor_rulebook_contract.md` ... `tasks/18_execution_core_packaging_boundary.md`

---

## 3) Current state snapshot

### Completed foundation

- Tasks 05–13 are complete (integration hardening + hybrid backend pipeline + orchestration).
- Strategy alignment docs are added and linked into task tracking.
- Egress-isolation policy is now included in alignment and go/no-go controls.

### Open work that still blocks paper-MVP certification

- Integration/runtime gate re-validation on current baseline.
- Tasks 14–18 (HTF-anchor contract through packaging decision).
- Adversarial gate artifacts + profile-parity evidence.

---

## 4) Re-sequenced canonical order (to avoid losing out-of-sequence items)

## Phase 0 — Baseline gate cleanup (must run first)

1. Re-run integration sanity suite on Python 3.11 baseline.
2. Reconfirm local quality gate and compose reproducibility.
3. Update `docs/GO_NO_GO_CHECKLIST.md` with current status evidence.

Why first: avoids building strategy logic on unstable runtime assumptions.

---

## Phase 1 — Strategy contract lock (Task 14)

4. Formalize HTF-anchor profile schema and rulebook contract.
5. Add profile validation and replay fixture requirements (at least 1D-anchor + 1H-anchor cases).

Output: deterministic profile contract and invalid-combo rejection behavior.

---

## Phase 2 — Score mapping lock (Task 15)

6. Map lecture-derived bucket scoring into canonical decision payload fields.
7. Add deterministic reason-code transitions and migration notes from current runbook policy.

Output: replay-safe decision object and score traceability.

---

## Phase 3 — Boundary + dependency hardening (Task 16)

8. Finalize strategy/policy/execution non-bypass contract.
9. Finalize Blofin egress isolation contract (static/dedicated preferred).
10. Ensure audit payload includes `trace_id`, `policy_version`, `rulebook_ref`, and egress context.

Output: enforceable dependency and network-risk boundary.

---

## Phase 4 — Two-pass adversarial validation (Task 17)

11. Pass 1 (strategy/microstructure): profile drift, cost tails, trigger inflation.
12. Pass 2 (systems/governance): policy pinning, replay parity, override drift, boundary checks.
13. Attach machine-readable pass/fail artifacts to gate review.

Output: promotion blocker/allow evidence.

---

## Phase 5 — Packaging boundary decision (Task 18)

14. Make explicit integrated-vs-separate execution-core decision with fork triggers.
15. Record decision in docs/tracker and tie to gating outcomes.

Output: architecture decision record with future fork criteria.

---

## Phase 6 — MVP paper certification run

16. Run paper-mode window with no live execution.
17. Evaluate against feasibility + go/no-go gates (data quality, determinism, expectancy realism, adversarial pass status).
18. Produce recommendation: **GO paper continuation / HOLD / NO-GO**.

Output: auditable paper-MVP verdict package.

---

## 5) What depends on Redact (required engagement)

These are operator decisions/inputs I can’t safely infer:

1. **Blofin isolation setup**
   - Dedicated test account confirmation
   - Trade-only API permissions (no withdrawal)
2. **Egress posture decision**
   - Surfshark mode selected (prefer Static IP/dedicated)
   - Confirmation main account will not use bot egress path
3. **Strategy policy confirmation**
   - Approve initial anchor profiles to ship first (`1D` + `1H` recommended)
   - Confirm risk envelope defaults for paper evaluation
4. **Venue scope confirmation**
   - On-chain venue/chain allowlist for paper-mode simulation assumptions
5. **Promotion authority**
   - Explicit sign-off checkpoint before any mode transition beyond paper

Without these, I can still do docs/tests/schemas, but cannot close final pilot gates.

---

## 6) Immediate next step (single clearest move)

Start with **Phase 0 + Task 14** in one focused lane:
- close runtime gate ambiguity,
- then lock HTF-anchor contract,
- then proceed sequentially to Tasks 15 -> 16 -> 17 -> 18.

This order minimizes rework and keeps strategy, risk, and operational controls aligned.
