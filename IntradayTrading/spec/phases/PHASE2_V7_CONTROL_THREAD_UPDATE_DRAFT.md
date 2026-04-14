Phase 2 update: proposing V7 zone-first refactor under Phase-2 umbrella (approval requested)

Context:
- v6.2.5 diagnostics isolated repeated 72k-band misses to downstream governance loops despite accepted/kept evidence.
- Current candle/anchor-first pipeline is proving brittle for battle-zone intent.

Proposal:
- Pivot to V7 zone-first hybrid architecture:
  1) structure-seeded events (from v3.3 semantics)
  2) base/battle-range events as primary geometry
  3) Foxian excursion as supporting evidence channel
  4) zone-level scoring/classification (`STRUCTURAL_ZONE` vs `TRADEABLE_ZONE`)

Artifacts on branch `phase2-v7-zone-first-20260307`:
- `IntradayTrading/spec/phases/PHASE2_V7_ZONE_FIRST_REFACTOR_PROPOSAL_2026-03-07.md`
- `IntradayTrading/spec/phases/PHASE2_V7A_ZONE_FIRST_CONTRACT.md`

Approval asks:
1) Approve V7 pivot (zone-first object model)
2) Approve phased sequence V7A->V7F under current Phase-2 track
3) Keep v6.2.5 as fallback baseline while V7A proceeds on isolated branch
4) Approve Pine semantic lock before Python/bot parity port

If approved, execution starts with V7A implementation contract and deterministic debug/acceptance pack for BTC/ETH 1D.