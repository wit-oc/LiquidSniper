# LiquidSniper Trading Strategy Runbook v1 (Stub)

Status: **Stub / pre-mentorship-ingestion**

## Scope
This runbook defines the current working confluence stack and what is explicitly out-of-scope until mentorship content is ingested and normalized.

## Primary confluences (highest priority)
1. **Support/Resistance first retest**
2. **Market structure (BoS / CHoCH)**

These are the only confluences treated as primary decision anchors in v1 stub.

## Secondary confluences (ranked)
Use in this order of value:
1. **Fibonacci levels**
2. **Trend lines**
3. **Liquidity alerts**
4. **VWAP**
5. **EMA200**

Secondary confluences can increase confidence but should not override failed primary structure conditions.

## Low-confidence / excluded from decision core
The following are currently **low confidence** and not part of trade qualification logic:
- Order blocks
- Supply zones
- Similar zone-taxonomy variants

They may be logged as annotations only.

## Minimal trade qualification logic (stub)
A candidate can be marked `publish_candidate` only if:
- Primary confluence #1 (S/R first retest) is present, and
- Primary confluence #2 (BoS/CHoCH context alignment) is present.

Then apply secondary confluences for confidence tiering:
- 0–1 aligned secondaries -> `watch_only`
- 2–3 aligned secondaries -> `publish_candidate`
- 4–5 aligned secondaries -> `high_priority`

## Risk posture (stub)
- No auto-execution.
- Simulation + paper-trade journaling only.
- Keep hard guardrails from `docs/FEASIBILITY_AND_KILL_CRITERIA.md` active.

## Next phase (separate action item)
Mentorship ingestion will refine/replace this stub with:
- explicit rulebook clauses,
- precise entry/exit logic,
- invalidation conditions,
- trade management flow,
- examples and counterexamples.
