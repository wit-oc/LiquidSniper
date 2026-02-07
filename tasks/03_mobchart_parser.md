# Task 03 — Mobchart payload parser

## Goal

Implement the Mobchart parser per Spec 04.

## Deliverables

- `liquidsniper/core/parser_mobchart.py`
- Parsing helpers:
  - K/M/B USD parsing
  - scientific notation parsing
  - age parsing (`13h+`, `1h 22m` → minimum seconds)
  - multiline batch inheritance of venue/market
- Unit tests using examples from `docs/TELEGRAM_PAYLOADS.md`
  - single-line
  - multiline batch
  - malformed line handling

## Acceptance criteria

- Tests cover the common formats
- Parser never throws on unexpected input; returns parse-error result
