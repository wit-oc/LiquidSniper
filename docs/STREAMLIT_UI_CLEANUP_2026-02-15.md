# Streamlit UI Cleanup — 2026-02-15

## Scope (Task 06)

Small cleanup pass on the existing diagnostic/card Streamlit UI to align presentation with current analysis outputs and screenshot artifact linking.

## Changes

- Updated inbox section title to **Diagnostic inbox** for clarity.
- Added inbox summary caption:
  - total runs shown
  - would-alert candidate count
- Standardized screenshot artifact display order in card detail:
  - `15m`, `1h`, `4h`, `1D`, `1W`
  - missing links are shown explicitly as `_(missing)_`.

## Files touched

- `liquidsniper/web/app.py`

## Notes

- No schema or runtime behavior changes.
- This pass is presentation-only and reversible.
