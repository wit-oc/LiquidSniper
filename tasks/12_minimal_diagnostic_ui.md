# Task 12 — Minimal diagnostic UI for backend decisions

## Goal

Expose backend decision stream in a lightweight debug terminal UI.

## Deliverables

- Inbox cards include:
  - final score
  - decision status
  - prominent `!` badge for `publish_candidate`
- Filters:
  - would-alert only
  - score threshold
  - status
- Card detail includes:
  - confluence breakdown
  - analysis run history
  - screenshot links

## Acceptance criteria

- User can see exactly what WOULD have been sent to channel and why.
- UI remains functional/debug-focused (no heavy presentation work).
