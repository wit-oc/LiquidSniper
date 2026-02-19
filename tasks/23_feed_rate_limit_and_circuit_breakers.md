# Task 23 — Feed rate-limit controls + circuit breakers

## Goal

Prevent feed instability or provider throttling from silently degrading strategy quality.

## Deliverables

- Per-provider rate budget manager (token/interval policy).
- Backoff + jitter retry policy for quota/server errors.
- Circuit-breaker state machine with reason codes and cooldown windows.
- Feed health event logging for operational review.

## Acceptance criteria

- Simulated quota errors produce graceful degradation (not crash loops).
- Circuit-breaker transitions are deterministic and observable.
- Decision engine receives feed health state and enforces fail-closed promotion rules when degraded.
