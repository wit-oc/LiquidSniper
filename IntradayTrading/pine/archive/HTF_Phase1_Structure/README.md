# HTF Phase 1 Structure — Archive

This folder contains superseded `HTF_Phase1_Structure*` Pine variants kept for history, audit, and rollback.

## Active canonical file
- `../../HTF_Phase1_Structure_v3_3.pine`

## Active user guide
- `../../HTF_Phase1_Structure_v3_3_USER_GUIDE.md`

## Why these files were archived
- Multiple iterations (`v2`, `v3`, forks, and debug variants) were used during Phase 1 certification.
- `v3_3` was selected as the certified baseline.
- Keeping legacy versions in root `pine/` increases accidental import/use risk.

## Archived versions
- `HTF_Phase1_Structure.pine`
- `HTF_Phase1_Structure_v2.pine`
- `HTF_Phase1_Structure_v2.2.pine`
- `HTF_Phase1_Structure_v3.pine`
- `HTF_Phase1_Structure_v3_1.pine`
- `HTF_Phase1_Structure_v3_2.pine`
- `HTF_Phase1_Structure_v3_cb_fork.pine`

## Indicator docs convention (for more indicators)
As additional indicators are added (e.g., Support/Resistance), keep their usage docs in `pine/` using:
- `<INDICATOR_NAME>_USER_GUIDE.md`

This keeps importable scripts and their operator docs easy to find together.
