# Chapter 05 final text evidence

Scope: `/private/tmp/rein-production-candidate-03/docs/chapters/05.md` and `05-rust.md` only.

The same temporary `$REIN_CH05_DIR` shape was used for the TypeScript and Rust runs:

```bash
export REIN_CH05_DIR="$(mktemp -d)"
printf 'marker: README alpha\n' > "$REIN_CH05_DIR/README.md"
printf 'marker: NOTES beta\n' > "$REIN_CH05_DIR/notes.md"
```

TypeScript `npm run typecheck` and all six `ch05:offline` modes exited 0. Rust `cargo fmt --manifest-path rust/Cargo.toml -- --check` exited 0. Rust first attempts to run the example were blocked by the environment's configured `/Volumes/Data` target path (`Operation not permitted`), recorded in `rust-*.txt`; reruns with the temporary validation-only `CARGO_TARGET_DIR=/private/tmp/rein-ch05-final-text-evidence/cargo-target` exited 0 for `multi`, `single`, `recovery`, `empty`, `exhausted`, and `limit`, recorded in `rust-*-retry.txt`.

Observed outputs include the exact multi-file answer `多文件摘要：marker: README alpha | marker: NOTES beta`, both read contents with their input newline, a third request containing both read results, `path_invalid` followed by recovery, and terminal reasons `final_answer`, `empty_final`, `model_error`, and `max_turns`, each with a final `stopped` event. No live command or service request was run.

Final-text replay evidence is in `final-ts-multi.raw`, `final-ts-single.raw`, `final-rust-multi.raw`, and `final-rust-single.raw`. Each records the exact argv, cwd, UTC start/end timestamps, exit code, and raw stdout/stderr. All four commands exited 0 and produced the expected multi/single answers. The final Rust commands used the validation-only `CARGO_TARGET_DIR` already described above; the documented command remains unchanged.
