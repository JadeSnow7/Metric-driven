# CH06 production rework archive

This directory preserves completed CH06 rework evidence for primary-thread review. It is an archive of source evidence, not an acceptance record and not a final CH06 source snapshot.

`rework-index.json` lists 12 source entries. Ten `/private/tmp` directories were copied under `sources/` (196 files total), and the two earlier production rounds were indexed against the already preserved `attempt-2-preserved/evidence-v1` and `evidence-v2` trees (41 + 40 files; no duplicate copy). Every manifest records each file's relative path, SHA-256, and mode. Copy and index checks compared SHA-256 values per relative path before recording `verification.source_and_archived_files_sha256_match: true`.

The Rust v3 directory contains only the hand-written `verification.md` summary. The later Rust v4 `raw/` and `dynamic/` outputs, plus the `v4-rust-evidence-search-error` raw outputs, are retained as separate sources. The TS v4 final evidence includes the `edge-v2-*` runs.

Known missing material is recorded in `rework-index.json`: the old v1 source snapshot is absent, and `/private/tmp/rein-ch05-v3-ts-preserved` does not exist and was not treated as a CH05 source. Missing time fields remain `null`; no current source was substituted for a historical snapshot.

CH06 is a production chapter and is not a formal first-round CH05/CH08/CH12/CH14 record. Final CH06 acceptance remains for the primary thread to review.
