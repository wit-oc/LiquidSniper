# Task 11 — TradingView artifact capture model + links

## Goal

Store and surface TV screenshot artifacts as auditable links tied to analysis runs.

## Deliverables

- Artifact storage contract:
  - path/URL, timeframe, capture_ts, source chart URL, hash
- Shared mount path contract for both agent process and UI container.
- UI-ready query returning per-run artifact links for 15m/1h/4h/1D/1W.

## Acceptance criteria

- Artifacts can be written by backend process and read by UI via shared mount.
- Card/run detail can list clickable artifact links.
