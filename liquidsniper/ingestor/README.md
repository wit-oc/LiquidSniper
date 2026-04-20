# Legacy Surface Note

`liquidsniper/ingestor/` is a legacy path retained during the Surveyor / Arbiter refocus.

Why it still exists:
- historical Telegram / Mobchart ingestion code still references this package path
- related parser, migration, and smoke-test surfaces still exist

Current posture:
- not part of the primary repo center
- kept path-stable for now to avoid breaking imports/tests while cleanup continues

See:
- `docs/LEGACY_SURFACES_STATUS_2026-04-19.md`
- `docs/SECOND_ARCHIVE_PASS_CODE_ARTIFACT_TRIAGE_2026-04-20.md`
