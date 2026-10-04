# Pre-CH08 benchmark tooling main review

`tests.json` is the primary thread's raw record for the independently run 13 focused tests. The tests cover fake CLI protocol output, version-query failure metadata, interrupted-process cleanup, nested cache pruning, symlink handling, and snapshot patch recovery. `index.json` records the copied file's SHA-256 and mode; the copy was verified against `/private/tmp/rein-pre-ch08-tool-main-review`.

The record does not establish a real no-`.git` model or chapter run. The later CH06 preparation uses `--skip-git-repo-check` and explicit `--sandbox workspace-write`; the archived CH05 a/b launches used snapshots that had `.git` and did not explicitly include `--sandbox`. These are cross-chapter environment differences, not acceptance evidence. The current test set also does not cover a normal CLI exit whose descendant retains an inherited pipe; the bounded drain behavior remains a stated limitation.
