# Main review, 2026-09-15

The first M1 handoff with eight passing stdio tests is not yet accepted. Direct source inspection found a second cancellation branch while waiting for `started` that accepts unbound cancelled terminals and ignores the wait result. The ordinary cancellation branch does not inspect trailing stdout. Frame buffering is local to a dropped future, and a missing caller deadline permits unbounded waits. These are substantive gaps in the requested cross-process boundary.

Call-record fields must come from observed lifecycle transitions. Deriving dispatched/reaped/exit_code from the final enum fabricates dispatch and exit for local permission rejection and hides reaping after a pre-ready crash. The implementation owner has been assigned one unified cancellation/terminal path, bounded framing and writes, unique run identifiers, and actual process observations with targeted fault tests.

The CLI must serialize the existing snake_case enums rather than lowercasing Debug names. The preceding handoff's snake_case descriptions do not match its source and are not accepted as evidence.

Original repository recheck: all 124 entries in bootstrap/original-file-manifest.json still match the original workspace. No original write has occurred. The protected first chapter in the integration tree still hashes to e07a2850ab31ca132fed9214256ccd746776bddfca2e48458fb25515ff8ea32d.

The prior-runs archive SHA256SUMS was independently checked in the main thread; every listed entry passed. This verifies archive integrity, not the accuracy of the historical claims inside those files. In particular docs-v2-run.json's navigation argv does not match the actual nav-config-v2 output and remains a known historical metadata defect.

The link checker v2 was rejected: hash-only URLs resolved to a directory, and its missing-page self-test forgot to await filesystem existence. v3 checked 2,179 actual built-page/config links with zero reported failures, but its relative-source self-test still needed to use a real built page and the shared validator. A final bounded correction was assigned without modifying author links.
