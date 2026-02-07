# Task 04 — Card engine (cards + confluences + trades)

## Goal

Implement the card upsert + confluence append + activate/archive behavior.

## Deliverables

- `liquidsniper/core/card_engine.py`
- Functions:
  - `upsert_card_for_event(event)`
  - `append_confluence(event)`
  - `activate_card(symbol)` / `archive_card(symbol)`
  - `get_card(symbol)` / `list_cards(status=...)`
- Unit tests:
  - new symbol creates inbox card
  - subsequent event updates timestamps
  - confluences accumulate and are queryable
  - activate creates trade row

## Acceptance criteria

- Given a parsed event, the correct DB rows are created/updated
