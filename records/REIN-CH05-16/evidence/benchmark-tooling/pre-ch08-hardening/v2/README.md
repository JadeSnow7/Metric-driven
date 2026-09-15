# Pre-CH08 benchmark tooling evidence v2

This bundle was produced by invoking `rein_benchmark.run_one` with controlled fake executables. Each run retains the generated `run.json`, incremental `events.jsonl` and `stderr.txt`; wrapper records retain the command, cwd, start/end, exit code and paths to the raw streams. The normal run exercises the updated argv, including `--skip-git-repo-check`. The missing `codex` run exercises version-query failure before process spawn.

No real chapter or model was started. The evidence is for primary-thread review and does not establish chapter acceptance or a full no-`.git` live run.
