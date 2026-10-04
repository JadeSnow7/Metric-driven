# Rein hybrid M1 delivery snapshot

This directory contains a local delivery snapshot assembled from the current `Agent-Learning` checkout. The product file set comes from `git ls-files --cached --others --exclude-standard`, with `.git`, dependency/build/cache/dist directories, actual environment files, and common test output files excluded. `.env.example` remains eligible.

Restore by extracting `rein-hybrid-m1.tar.gz` into a fresh checkout root, then installing the recorded project dependencies (`npm ci` and the Rust dependencies through Cargo) before following `docs/chapters/06-plugin.md`. The archive has no tag or commit: `HEAD.txt` records the source checkout HEAD, while `working-tree-vs-head.patch` is the complete binary-capable diff of the source checkout against that HEAD and includes the author's pre-existing uncommitted changes; it is not a task-only patch. Untracked files are represented in the tarball when selected by the git file listing, but are not represented by `git diff`.

The copied `task-81-plan.json` is the existing transfer path-boundary plan. Experimental task inputs and evidence remain under `records/`, rather than being silently mixed into this product snapshot. The snapshot documents a bounded M1 implementation and its tests; a single host run is not a live service test, and no online service was run. `tokens` are unavailable and are not estimated.
