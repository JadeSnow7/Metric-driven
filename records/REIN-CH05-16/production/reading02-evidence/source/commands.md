# reading02 snapshot verification

This verification was run from `/private/tmp/rein-production-candidate-03` on
2026-09-14. It followed the same shell ordering described in the reading:
extract both archives, return to `REIN_BOOK_ROOT` for the manifest check, then
extract the pre-ch05 archive into a fresh directory, run `git init -q`, and
apply the Git binary patch with `git apply --binary`. The temporary extraction
directory was removed after the checks.

The exact command metadata and captured stdout/stderr are in
`raw-run.json`. Each step records `script`, `argv`, `cwd`, `start`,
`end`, `exit`, `stdout`, and `stderr`.

The following results were observed:

- manifest hash for `docs/chapters/05.md`: expected and actual
  `16bb9258c31ce754ab119ee35d1e8f360ba8bcddc84f24d53756f6fcc5efea6a)
- Git patch applied successfully with exit 0
- patched TypeScript chapter hash:
  `16bb9258c31ce754ab119ee35d1e8f360ba8bcddc84f24d53756f6fcc5efea6a`
- patched Rust chapter hash:
  `c444825584aec7f6869baea9b6132d12424530011cdc59984d17160cc5e4e9fc`
- all six recorded steps exited 0

No npm install, Cargo build, network request, Git commit, tag, push, or
publish was performed by this verification. The snapshot and patch checks are
`passed` for this run; this evidence does not claim that the ch05 runtime
tests or live service passed.

