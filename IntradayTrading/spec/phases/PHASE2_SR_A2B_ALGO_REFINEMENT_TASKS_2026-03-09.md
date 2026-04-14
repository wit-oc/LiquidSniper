# Phase 2 — SR A.2b Algorithm-Only Refinement Tasks (2026-03-09)

Status: APPROVED FOR EXECUTION  
Scope: Phase 2 support/resistance analytics only. No trigger-entry logic, no execution logic.

## Control intent
We are refining the Python S/R engine so it generalizes across **100s of trading pairs**.  
No operator-bias layer. No symbol-specific hardcoded removals or preferred ranges.

## Primary problem statement
The engine still overfires in dense Daily bands and sometimes picks the wrong representative level.
BTC Daily review cases are the current diagnostic examples (for evaluation only, not hardcoded rules):
- `60k` vs `65k`
- `74k` vs `80k`
- `98k` vs `104k/110k/115k`

Current failure modes to address:
1. repeated interaction still over-ranks "spent" zones,
2. binary first-retest gating can suppress otherwise meaningful levels (e.g. `98k`),
3. nearby valid shelves are not competing within a broader band; too many survive together,
4. reaction quality does not dominate enough when a level has fewer but cleaner reactions.

---

## Hard guardrails
1. Repo lock: `/Users/wit/.openclaw/workspace/LiquidSniper`
2. Branch lock: `phase2-v7-zone-first-20260307`
3. No dependency installs
4. No destructive resets/cleanups
5. No symbol-specific or price-specific logic in production path
6. BTC examples above may be used for diagnostics/regression evaluation only
7. Final result must be pushed to remote branch

---

## Files most likely in scope
- `liquidsniper/core/sr_engine_v2.py`
- `liquidsniper/ops/sr_bootstrap.py`
- `liquidsniper/config/sr_bootstrap.default.json`
- tests if needed

---

## Task sequence

### T1 — Explain current failure mechanically
Before changing logic, inspect current code and identify exactly why:
- `74k` was historically under-ranked versus nearby bands,
- `98k` is currently excluded from Daily majors,
- `60/65`, `74/80`, and `104/110/115` all survive together.

Required output in thread:
- concise explanation tied to exact functions/fields, not vibes.

### T2 — Add reaction-efficiency / over-testing correction
Implement a general scoring correction so heavily re-tested zones do not automatically dominate cleaner reaction zones.

Acceptable approaches include:
- reaction-efficiency metric,
- spent-zone penalty,
- body-close / wick-heaviness weighting,
- diminishing returns on touch count.

Constraint:
- must remain generic across symbols.

### T3 — Replace binary Daily retest kill with softer major-zone logic
The current Daily major filter is too binary for some candidates.

Goal:
- `accept` should not be a free pass,
- but it also should not automatically kill a potentially meaningful macro level.

Implement a more nuanced weighting or eligibility model.

### T4 — Add Daily local-band arbitration
Add a general algorithm that lets nearby Daily candidates compete within a broader band so only the dominant representative(s) survive.

Examples of acceptable logic:
- ATR/bps-based local clustering,
- band representative selection,
- keep top N per dense band,
- band-level pruning based on composite score.

Constraint:
- must be generic; no BTC-specific ranges.

### T5 — Regression/evaluation pass
Run the updated bootstrap and inspect BTC Daily outputs.

Evaluation objective (not exact hardcoded acceptance):
- `74k` should become more competitive relative to `80k`
- `98k` should be explainable (either re-enters or has a clear computational reason it still loses)
- `60/65` and `104/110/115` should show better band competition and fewer redundant survivors

If still blocked or ambiguous after one serious pass, stop and produce a design-review brief suitable for external GPT 5.4 Pro review.

### T6 — Final handoff with exact code map
Final report must include:
1. what changed,
2. why it changed,
3. exact files + functions that now power the behavior,
4. commit hashes,
5. updated BTC Daily major outputs,
6. remaining disagreements / next algorithmic question.

This code map is mandatory.

---

## Validation requirements
Run at minimum:
- relevant pytest subset already used in this repo for SR work
- bootstrap rerun for BTC/ETH
- container rebuild/restart if behavior surfaced in Streamlit depends on changed code

---

## Blocker protocol
If blocked, respond exactly:
`BLOCKED: <specific blocker> | NEXT: <smallest unblocked step>`
