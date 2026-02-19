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
- `docs/DATA_FEED_STRATEGY_V1.md`
- `docs/OPENCLAW_ORCHESTRATION.md`
- `docs/TRADINGVIEW_ADAPTER_CONTRACT.md`
- `docs/SIGNAL_DELIVERY_AND_DRYRUN.md`
- `docs/GO_NO_GO_CHECKLIST.md`

## C) Strategy + alignment references

- `docs/TRADING_STRATEGY_RUNBOOK_V1.md`
- `docs/AUTOMATED_TRADING_AGENT_ALIGNMENT_V1.md`
- `docs/EXECUTION_CORE_COMMAND_CONTRACT_V1.md`

## D) Task contracts

- `tasks/09_analysis_run_contract.md` ... `tasks/13_openclaw_skill_orchestration.md`
- `tasks/14_htf_anchor_rulebook_contract.md` ... `tasks/18_execution_core_packaging_boundary.md`
- `tasks/19_market_data_provider_contract.md` ... `tasks/26_feed_benchmark_and_gate_evidence.md`

---

## 3) Current state snapshot

### Completed foundation

- Tasks 05–13 are complete (integration hardening + hybrid backend pipeline + orchestration).
- Strategy alignment docs are added and linked into task tracking.
- Egress-isolation policy is now included in alignment and go/no-go controls.

### Open work that still blocks paper-MVP certification

- Integration/runtime gate re-validation on current baseline.
- Canonical OHLCV feed baseline tasks (Tasks 19–22).
- Strategy/governance tasks on top of canonical feed (Tasks 14–18).
- Feed reliability + benchmark evidence tasks (Tasks 23–26).
- Adversarial gate artifacts + profile-parity evidence.

## Dependency default/stub matrix (paper-MVP fail-closed baseline)

| Dependency area | Default/stub status | Fail-closed behavior | Owner to unblock |
|---|---|---|---|
| Blofin account + API credentials | **Stubbed / absent by default** | No account binding, no credential loading, no order path activation. Paper/sim only. | Redact (operator) |
| Exchange egress posture (Surfshark static/dedicated) | **Unverified by default** | Treat egress as non-compliant for promotion; block any transition beyond paper-mode validation. | Redact (operator) |
| On-chain venue allowlist (chains/protocols) | **Disabled by default** | No on-chain routing assumptions promoted to executable scope; simulation remains constrained to documented placeholders. | Redact (operator) |
| Promotion/sign-off authority | **Required and unresolved by default** | No progression beyond paper evidence package without explicit human sign-off checkpoint. | Redact (operator) |

This matrix is the canonical baseline for sequence execution in this document and is intentionally fail-closed until operator-owned inputs are explicitly provided.

---

## 4) Re-sequenced canonical order (to avoid losing out-of-sequence items)

## Phase 0 — Baseline gate cleanup (must run first)

1. Re-run integration sanity suite on Python 3.11 baseline.
2. Reconfirm local quality gate and compose reproducibility.
3. Update `docs/GO_NO_GO_CHECKLIST.md` with current status evidence.

Why first: avoids building strategy logic on unstable runtime assumptions.

---

## Phase 1 — Canonical feed baseline (Tasks 19–22)

4. Implement market-data provider contract + candle schema (Task 19).
5. Implement CCXT OHLCV backfill + incremental scheduler (Task 20).
6. Implement candle quality gates + aggregation policy (Task 21).
7. Integrate strategy path to canonical candles; keep trigger feed contextual only (Task 22).

Output: strategy-grade OHLCV baseline independent of Telegram trigger availability.

---

## Phase 2 — Strategy contract + score lock (Tasks 14–15)

8. Formalize and wire HTF-anchor profile schema/rulebook contract (Task 14).
9. Map lecture-derived bucket scoring into deterministic decision payload fields (Task 15).

Output: deterministic profile and scoring model grounded in canonical feed data.

---

## Phase 3 — Dependency + feed hardening (Tasks 16, 23, 24)

10. Finalize strategy/policy/execution non-bypass contract (Task 16).
11. Add feed rate-limit budgets + circuit breakers + health events (Task 23).
12. Finalize trigger-feed decoupling and rationale traceability (Task 24).
13. Ensure audit payload includes `trace_id`, `policy_version`, `rulebook_ref`, and egress context.

Output: enforceable dependency and reliability boundary with fail-closed behavior.

---

## Phase 4 — Adversarial + evidence gates (Tasks 17, 26)

14. Run two-pass adversarial validation (strategy/microstructure + systems/governance) (Task 17).
15. Produce feed benchmark and replay evidence artifact for gate review (Task 26).

Output: promotion blocker/allow evidence package grounded in feed and strategy behavior.

---

## Phase 5 — Packaging boundary + conditional fallback (Tasks 18, 25)

16. Make explicit integrated-vs-separate execution-core decision with fork triggers (Task 18).
17. Implement native Blofin adapter fallback only if CCXT gap assessment requires it (Task 25).

Output: architecture decision record plus conditional venue-specific fallback path.

---

## Phase 6 — MVP paper certification run

18. Run paper-mode window with no live execution.
19. Evaluate against feasibility + go/no-go gates (data quality, determinism, expectancy realism, adversarial pass status).
20. Produce recommendation: **GO paper continuation / HOLD / NO-GO**.

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

Start with **Phase 0 + Phase 1 (Tasks 19 -> 22)** in one focused lane:
- close runtime gate ambiguity,
- land canonical OHLCV feed baseline,
- then lock strategy contract/scoring (Tasks 14 -> 15),
- then proceed through governance/reliability gates.

This order prevents trigger-only drift and keeps strategy implementation tied to actual candle-based market structure inputs.
