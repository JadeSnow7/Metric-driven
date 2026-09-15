# Handoff

The independent evaluator consists of `evaluator.py`, its unittest coverage, and `calibration_cli.py`. The toy reads the shared `data/` directly and emits the public result protocol; it is calibration-only and makes no claim that the Rust/Node product or four algorithms have passed.

Run calibration without the formal group:

```bash
python3 test_evaluator.py
```

The evaluator accepts `--repo`, `--data`, `--output`, optional `--strategy`, and optional `--command-json`. Every child invocation is retained under `output/runs/`; `summary.json` contains concrete check IDs and reasons. Formal product evaluation should use the default npm argv and a fresh output directory so failed output is never overwritten.

Known limitation: this workspace contains no product implementation, so no formal 16-row product run, Rust/Node evidence, or documentation regression result is claimed here. The next dependency is the implementation team's finished product and its real command entrypoint.
