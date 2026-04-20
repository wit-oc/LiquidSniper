# Branch Reconciliation Snapshot

Date: 2026-04-19  
Base: `origin/main` at `73538ee`

This note records the branch state after the Surveyor checkpoint merge and the start of the repo-refocus pass.

During this pass, the obviously merged local branches were deleted, the matching merged remotes were pruned where they still existed, the stale one-commit branches were reviewed and pruned, and the extra worktree tied to the merged paper-runtime branch was removed. The notes below record what was triaged and why.

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

These branches each showed exactly one commit not present on `main` at review time.
They were treated as historical artifacts, not active lanes.

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

Outcome:
- `task-03-mobchart-parser`: preserved as archived doc material under `docs/archive/2026-04-19-branch-salvage/`, then deleted
- `feat/sr-engine-v2-initiative-plan`: no active content preserved beyond summary notes, then deleted
- `chore/lane-cleanup-task18-closeout`: no active content preserved beyond summary notes, then deleted

---

## 3) Practical next actions

Cleanup actions completed in this pass:

1. Deleted merged local branches that were no longer needed
2. Removed merged remote branches that no longer provided value
3. Reviewed the three one-commit branches above
4. Preserved the only worth-keeping historical doc in `docs/archive/2026-04-19-branch-salvage/`
5. Cleaned up the extra worktree tied to `feat/paper-runtime-controls-thread`
6. Deleted the merged `feat/paper-runtime-controls-thread` branch after worktree cleanup

---

## 4) Operating principle

The repo is being refocused around Surveyor and Arbiter.
Branch hygiene should follow that same rule.

Current result after cleanup:
- active local branches: `main`, `chore/surveyor-arbiter-repo-refocus`
- active remote branches: `origin/main`, `origin/chore/surveyor-arbiter-repo-refocus`

If a branch does not represent:
- active Surveyor work,
- active Arbiter work,
- canonical feed/storage work,
- or the packet/replay/backtesting foundation,

it should probably be archived in docs or deleted, not kept alive as if it were still central.
