# REIN hybrid prior-run archive

Archived source evidence:

- Rust source: `/private/tmp/rein-hybrid-rust-evidence`; four immutable logs (`stdio_host-20260915.log`, `v2`, `v3`, `v4`) are preserved under `rust/`.
- TypeScript/docs source: `/private/tmp/rein-hybrid-ts-evidence`; 27 evidence files are preserved under `ts/`.
- `MANIFEST` records archived path, byte size, and mode. `SHA256SUMS` was verified with `shasum -a 256 -c`.

The Rust v4 run is the first archive entry with the corrected eight-test suite: 7 passed and 1 failed (`ignore_cancel` observed `Cancelled`, expected `OutcomeUnknown`). v1–v3 contain earlier test revisions and are retained as historical evidence; their assertions and coverage were known incomplete. The hybrid runtime was not accepted as complete by these runs.

The archive contains no runtime source snapshot and must not be mixed into the older REIN-CH05–16 benchmark scoring. Where an earlier evidence file does not contain raw argv or timestamps, that absence is preserved rather than reconstructed.

Archive totals: 31 evidence files, 14,460 bytes, excluding `index.md`, `MANIFEST`, and `SHA256SUMS`.
