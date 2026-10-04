# ch08 supplemental adjudication check

`supplemental_check.py` is a read-only supplement for evaluator SHA256
`6ed1a9d09fd40871b8e4e0bfed7cb2d2f64a4a3eb9f5ff762bb0566cda6fe86b`.
Run it with `--run RUN.json --data DATA_ROOT --budget N`. It rejects a
nonzero run, verifies the 4x4 task/strategy matrix and budget, recomputes the
Rust-style message estimate including tool calls, and treats source-bearing
tool messages as user-visible evidence for claim grounding. It never rewrites
the original run.

This is an adjudication supplement, not a replacement for the frozen
evaluator. It covers the estimate and tool-source normalization gaps found in
the shared specification; other evaluator checks and live model performance
remain outside its evidence.
