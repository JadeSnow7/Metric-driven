#!/bin/sh
set -u
root=/private/tmp/rein-production-candidate-03
out=/private/tmp/rein-ch06-v4-rust-evidence/raw
target=/private/tmp/rein-candidate03-build
run() {
  name=$1; shift
  start=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  "$@" >"$out/$name.stdout" 2>"$out/$name.stderr"
  code=$?
  end=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  python3 - "$name" "$start" "$end" "$code" "$out/$name.stdout" "$out/$name.stderr" "$@" <<'PY'
import json, pathlib, sys, os
name, start, end, code, stdout, stderr, *argv = sys.argv[1:]
record = {
    "name": name, "argv": argv, "cwd": os.getcwd(), "start": start,
    "end": end, "exit": int(code),
    "stdout": pathlib.Path(stdout).read_text(),
    "stderr": pathlib.Path(stderr).read_text(),
}
pathlib.Path(os.environ["EVIDENCE_JSON"]).write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
PY
}
export EVIDENCE_JSON=$out/fmt-check.json
run fmt-check cargo fmt --manifest-path "$root/rust/Cargo.toml" -- --check
export EVIDENCE_JSON=$out/cargo-test.json
run cargo-test env CARGO_TARGET_DIR="$target" cargo test --manifest-path "$root/rust/Cargo.toml"
for mode in normal budget duplicate zero tool-zero cancel-before cancel cancel-at-return cancel-between-tools timeout; do
  export EVIDENCE_JSON=$out/mode-$mode.json
  run "mode-$mode" env CARGO_TARGET_DIR="$target" cargo run --quiet --manifest-path "$root/rust/Cargo.toml" --example ch06_loop -- "$mode"
done
export EVIDENCE_JSON=$out/mode-unknown.json
run mode-unknown env CARGO_TARGET_DIR="$target" cargo run --quiet --manifest-path "$root/rust/Cargo.toml" --example ch06_loop -- unknown
python3 - "$out" <<'PY'
import json, pathlib, sys
directory = pathlib.Path(sys.argv[1])
records = [json.loads(p.read_text()) for p in sorted(directory.glob("*.json"))]
(directory / "index.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
PY
