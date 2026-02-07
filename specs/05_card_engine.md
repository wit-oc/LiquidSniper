# Spec 05 — Card Engine (symbol-centric)

## Goal

Turn parsed `signal_events` into symbol-centric **Cards** with aggregated cross-venue confluences.

## Definitions

- A **Card** is keyed by `symbol`.
- A **Confluence** is a venue/market/side/level instance attached to a card.

## Workflow

When a new `signal_event` arrives:
1) Upsert `cards(symbol)`
   - if new: create with `status=inbox`
   - update `updated_ts` and `last_signal_ts`
2) Insert `confluences` row linked to card
   - If we decide to dedupe: update `ts_last_seen` instead

## Card actions

- Activate:
  - set `cards.status=active`
  - create `trades` row if missing

- Archive/Delete:
  - default: `cards.status=archived`
  - UI may optionally expose hard-delete later

## Confluence grouping in UI

Card detail should show confluences grouped by:
- venue
- market_type

## Acceptance criteria

- New signals create/update the right card.
- Confluences accumulate under the right symbol.
- Activate/Archive are reflected immediately in UI.
