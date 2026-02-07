# Spec 06 — Web UI (Streamlit)

## Goal

A Streamlit app that surfaces symbol Cards as "cards" with actions and detail views.

## Pages

### Inbox

- List cards with `status=inbox`
- Columns:
  - symbol
  - last_signal_ts
  - # confluences
  - venues present
- Actions:
  - Activate
  - Archive/Delete

### Card detail

- Show card metadata
- Show confluences grouped by venue/market
- Show raw recent signal lines (optional)

### Active

- List cards with `status=active`
- Show editable trade fields:
  - entry
  - stop_loss
  - tp_final
  - rr_best
  - status
  - notes

## UI constraints

- Keep UI logic thin.
- All DB operations go through core `db` module.

## Acceptance criteria

- Inbox shows cards within seconds of ingest.
- Buttons update state and refresh.
- Active page supports editing and persists.
