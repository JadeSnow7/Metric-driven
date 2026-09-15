# REIN hybrid evidence archive

This directory is an archival copy of the three evidence directories listed below, made without changing their source directories. Each subdirectory contains a `MANIFEST.tsv` with the original absolute source path, relative path, byte count, source mode, and SHA256. Every copied file was read back and matched its source byte count and SHA256; file modes were also checked.

The archive preserves both earlier failures and later passing runs. File names containing `final`, `v2`, or similar labels are historical names only and do not establish final acceptance. Historical handoff records and some raw outputs may have incomplete argv, cwd, or timestamp metadata; no missing metadata was invented. Token accounting is unavailable and is recorded as null by omission. Final acceptance is determined by `main-review/` and any authorized backwrite checks.

The runtime evidence is archived as collected and is not mixed into the old `REIN-CH05-16` baseline scoring.

- `rein-hybrid-boundary-evidence/`: 12 files, 5965 bytes
- `rein-hybrid-runtime-final-evidence/`: 33 files, 16602 bytes
- `rein-hybrid-link-evidence/`: 8 files, 25326 bytes
