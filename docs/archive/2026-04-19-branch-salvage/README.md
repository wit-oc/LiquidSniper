# Branch Salvage Notes (2026-04-19)

This archive bucket preserves the small amount of material judged worth keeping from stale branches during the Surveyor / Arbiter repo refocus.

## Archived branch outcomes

### `task-03-mobchart-parser`
- Status: branch content archived, branch can be deleted
- Preserved artifact:
  - `HYBRID_CONFLUENCE_PIPELINE_SPEC_LEGACY.md`
- Why archived instead of kept active:
  - it describes an older OpenClaw + Mobchart + TradingView-heavy product posture
  - some ideas may still be historically useful, but it does not match the current Surveyor / Arbiter center

### `feat/sr-engine-v2-initiative-plan`
- Status: summarized only, branch can be deleted
- Unique content was limited to tracker normalization in `TASK_BOARD.md` and `WORK_ITEMS.md`
- Why not preserved as active content:
  - the repo has moved beyond that exact board shape, and the useful sequencing ideas are already reflected elsewhere

### `chore/lane-cleanup-task18-closeout`
- Status: summarized only, branch can be deleted
- Unique content was old paper-runtime behavior around daily trade-cap overrides and PnL realization handling
- Why not preserved as active content:
  - those changes belong to the old paper-runtime lane, which is no longer the product center
  - if we ever need them again, the commit remains in Git history and can be recovered by hash

### `feat/paper-runtime-controls-thread`
- Status: merged historical lane; delete after worktree cleanup
- This branch was already fully merged into `main`, but it persisted because of an attached local worktree
- Why it is being removed:
  - it represents legacy paper-runtime scope rather than active Surveyor / Arbiter scope

## Operating principle

During refocus, preserve historical ideas as explicit archive docs, not as zombie active branches.
