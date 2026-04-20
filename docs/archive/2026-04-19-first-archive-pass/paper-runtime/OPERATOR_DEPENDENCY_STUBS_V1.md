# OPERATOR_DEPENDENCY_STUBS_V1

Status: Draft (Fail-Closed Defaults)
Scope: Paper MVP dependency stubs only (no live credentials, no live execution)
Owner: Operator (Redact)

## Purpose

Define explicit default stubs for operator-owned dependencies so development and paper-mode validation can continue safely while external/operator prerequisites remain unresolved.

## Core Policy

- System defaults are fail-closed.
- No transition beyond paper mode is allowed when any required dependency is unresolved.
- No live trading actions, account linking, or secret material are permitted in this stage.

## Dependency Stub Matrix

| Dependency | Default Stub Value | Current Gate State | Blocked Transition(s) | Required Owner Action |
|---|---|---|---|---|
| Blofin account + API credentials | `BLOFIN_ENABLED=false`; key/secret/passphrase placeholders only | BLOCKED | Paper -> testnet/live exchange routing | Provide valid account + API triplet, confirm scope/permissions, rotate into secure secret path (not repo) |
| Egress verification (Surfshark static/dedicated IP) | `EGRESS_VERIFIED=false`; `EGRESS_PROFILE=UNVERIFIED_STUB` | BLOCKED | Any venue/IP allowlist-dependent connectivity promotion | Confirm final egress method and stable outbound identity; provide verification evidence |
| On-chain allowlist decisions | `ONCHAIN_ENABLED=false`; allowlist set empty | BLOCKED | Enabling any on-chain execution path | Provide chain list + wallet policy + explicit allowlist decisions |
| Operator sign-off for non-paper progression | `OPERATOR_SIGNOFF_REQUIRED=true`; `OPERATOR_SIGNOFF_GRANTED=false` | BLOCKED | Paper -> any non-paper environment | Provide explicit signed go/no-go approval with date/time and scope |

## Stage Gates

### Gate G0 — Paper-Only Baseline (OPEN)

Allowed:
- Documentation, scaffolding, profile contracts, and paper/sim logic wiring
- Validation work that does not require live creds or external side effects

Denied:
- Any live order/execution path
- Any account linking/auth attempts
- Any environment promotion requiring unresolved dependencies

### Gate G1 — Dependency Resolution (CLOSED until all actions complete)

Entrance criteria (all required):
1. Blofin credentials delivered through secure operator path and validated by owner process
2. Egress verification confirmed and recorded
3. On-chain allowlist decisions finalized and documented
4. Operator sign-off granted explicitly for scoped progression

If any criterion is missing, remain in G0.

### Gate G2 — Promotion Eligibility (CLOSED by default)

G2 may only be considered after G1 completion and explicit checklist pass in go/no-go controls.

## Block Conditions (Hard Stops)

Progression beyond paper must stop immediately if any of the following is true:

- `BLOFIN_ENABLED != true`
- `EGRESS_VERIFIED != true`
- `ONCHAIN_ENABLED != true` for any plan requiring on-chain actions
- `OPERATOR_SIGNOFF_GRANTED != true`

## Owner Action Checklist

Operator must provide:

1. Blofin account/API readiness package (credential presence + permission intent)
2. Final egress confirmation (static/dedicated profile + verification result)
3. On-chain allowlist decision record (what is allowed, what remains denied)
4. Explicit sign-off statement authorizing the next stage

Until then, all defaults remain stubbed and fail-closed.

## Audit Notes

- This document intentionally contains no real secrets, keys, account IDs, or wallet addresses.
- All placeholder values are non-operational by design.
- Any future updates should preserve fail-closed defaults unless replaced by verified operator-provided inputs.
