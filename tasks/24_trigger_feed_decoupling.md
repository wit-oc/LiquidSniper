# Task 24 — Trigger feed decoupling (Mobchart as context)

## Goal

Decouple trigger ingestion from canonical strategy data so Telegram alerts do not act as the core market-data source.

## Deliverables

- Explicit trigger-context model linked to analysis runs via trace ids.
- Decision flow where canonical candle availability is mandatory for promotion.
- Documentation update clarifying trigger vs canonical data responsibilities.

## Acceptance criteria

- Missing trigger feed does not break canonical strategy scoring.
- Missing canonical feed blocks promotion regardless of trigger signal presence.
- Trigger influence is transparent in persisted rationale and reason codes.
