# Branch Reconciliation Snapshot

Date: 2026-04-19  
Base: `origin/main` at `73538ee`

This note records the branch state after the Surveyor checkpoint merge and the start of the repo-refocus pass.

During this pass, the obviously merged local branches were deleted, and the matching merged remotes were pruned where they still existed. The remaining branch list below is the part that still needs deliberate treatment.

---

## Summary

The branch backlog is a mix of:
- branches already fully merged into `main`,
- old branches whose upstream remotes are already gone,
- and a small number of stale branches with one unique commit not present on `main`.

Recommendation:
- clean up merged branches aggressively,
- do a small evidence review for the few one-commit stragglers,
- and avoid carrying the old branch list as if it were still active product scope.

---

## 1) Fully merged into `main`

These branches had `0` commits ahead of `main`.
Most were pruned during this pass.

Already pruned locally and/or remotely:
- `chore/cleanup-branch-reconciliation-20260410`
- `feat/tv-alpha-daily-swing-scaffold`
- `intraday-trading-migration-20260302`
- `phase2-v7-zone-first-20260307`
- `phase2-zone-engine-v3`

Still remaining because it is attached to a local worktree:
- `feat/paper-runtime-controls-thread`

Note:
- `feat/paper-runtime-controls-thread` is merged, but it cannot be deleted until the extra worktree at `/Users/wit/.openclaw/workspace/LiquidSniper-thread1476` is cleaned up deliberately.

---

## 2) Not merged into `main`, but only one unique commit ahead

These branches each show exactly one commit not present on `main`.
They should not be treated as active lanes by default, but they are worth a quick human glance before deletion.

### `chore/lane-cleanup-task18-closeout`
- unique commit: `14193fd`
- subject: `fix(paper): disable entry PnL realization, add TP2 closes, lane-specific daily cap override`
- upstream remote: gone

### `feat/sr-engine-v2-initiative-plan`
- unique commit: `bdfff6c`
- subject: `Normalize board lanes and add deterministic 3-lane execution plan`
- upstream remote: gone

### `task-03-mobchart-parser`
- unique commit: `ab3b873`
- subject: `Add hybrid confluence pipeline spec with OpenClaw + TV artifact model`
- upstream remote: still exists

Recommendation:
- inspect these as historical artifacts, not active product branches
- if the single unique commit is still useful, preserve it by moving the relevant doc/change into `docs/archive/` or another explicit archive surface
- otherwise delete the branch after confirmation

---

## 3) Practical next actions

Recommended cleanup order:

1. Delete merged local branches that are no longer needed
2. Remove merged remote branches that no longer provide value
3. Review the three one-commit branches above
4. Preserve any still-useful historical content in archive docs, not active product lanes
5. Clean up the extra worktree tied to `feat/paper-runtime-controls-thread`

---

## 4) Operating principle

The repo is being refocused around Surveyor and Arbiter.
Branch hygiene should follow that same rule.

If a branch does not represent:
- active Surveyor work,
- active Arbiter work,
- canonical feed/storage work,
- or the packet/replay/backtesting foundation,

it should probably be archived in docs or deleted, not kept alive as if it were still central.
