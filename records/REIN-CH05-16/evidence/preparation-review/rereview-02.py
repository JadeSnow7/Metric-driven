#!/usr/bin/env python3
"""Bounded independent preparation re-review; writes only this evidence directory and temporary copies."""
from pathlib import Path
import datetime, hashlib, importlib.util, json, runpy, shutil, subprocess, sys, tempfile
ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SPECS = ROOT / "records/REIN-CH05-16/evidence/specs"
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
def hashes():
    paths = [ROOT / "tools/rein_evaluate.py", ROOT / "tools/tests/test_rein_evaluate.py", ROOT / "tools/tests/test_rein_dataset.py", SPECS / "chapter-16-cases.json"]
    paths += [p for p in sorted((SPECS / "chapter-16").rglob("*")) if p.is_file()]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
ev = load("review_evaluate", ROOT / "tools/rein_evaluate.py")
ds = load("review_dataset", ROOT / "tools/tests/test_rein_dataset.py")
index = json.loads((SPECS / "chapter-16-cases.json").read_text())
report = {"reviewed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "scope": "Previous preparation findings only; trusted frozen argv; production excluded", "source_sha256_before": hashes(), "replay_argv": [sys.executable, "-B", str(Path(__file__).resolve())], "checks": []}
def record(name, expected, actual):
    report["checks"].append({"name": name, "expected": expected, "actual": actual, "matches_expectation": actual == expected})
def candidate(case_id, text, expected_pass):
    case = next(c for c in index["cases"] if c["id"] == case_id)
    source = SPECS / "chapter-16" / case_id / "workspace"
    oracle = json.loads((source.parent / "expected.json").read_text())
    with tempfile.TemporaryDirectory() as d:
        work = Path(d) / "workspace"
        shutil.copytree(source, work)
        (work / case["input_fault"]["file"]).write_text(text)
        outcome = ds.assertions_hold(case, work, oracle)
    report["checks"].append({"name": case_id, "candidate": text, "expected_oracle_pass": expected_pass, "actual_oracle_pass": outcome, "matches_expectation": outcome == expected_pass})
run = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tools/tests", "-v"], cwd=ROOT, text=True, capture_output=True)
report["existing_selftests"] = {"argv": [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tools/tests", "-v"], "exit": run.returncode, "stdout": run.stdout, "stderr": run.stderr}
original_outcomes = []
for case in index["cases"]:
    work = SPECS / "chapter-16" / case["id"] / "workspace"
    oracle = json.loads((work.parent / "expected.json").read_text())
    original_outcomes.append({"id": case["id"], "oracle_pass": ds.assertions_hold(case, work, oracle, require_unchanged=case["category"] == "no_change", before=ds.files_hash(work))})
report["original_outcomes"] = original_outcomes
record("original_oracle_pass_count", 3, sum(x["oracle_pass"] for x in original_outcomes))
for case_id in ["expired-command-01", "no-change-01"]:
    package = json.loads((SPECS / "chapter-16" / case_id / "workspace/package.json").read_text())
    record(case_id + " required npm script check exists", True, "check" in package.get("scripts", {}))
cli = SPECS / "chapter-16/parameter-change-01/workspace/src/cli.py"
parser = runpy.run_path(str(cli))["parser"]
try:
    parsed = vars(parser.parse_args(["--model", "gpt-4", "--timeout", "5"]))
    old_flag_rejected = False
except SystemExit as e:
    parsed = {"exit": e.code}
    old_flag_rejected = e.code != 0
record("old timeout flag rejected by fixture parser", True, old_flag_rejected)
report["old_timeout_parse_result"] = parsed
candidate("expired-command-03", "Use `npm run test` for tests.\n", True)
candidate("broken-relative-link-01", "See [the guide](./docs/guide.md).\n", True)
candidate("broken-relative-link-01", "See [Guide](docs/guide.md).\n", True)
candidate("expired-command-01", "npm run check validate the project\n", False)
candidate("parameter-change-02", "--workspace scanning\n", False)
candidate("broken-relative-link-01", "See [guide](docs/missing.md).\n<!-- [guide](docs/guide.md) -->\n", False)
candidate("parameter-change-03", "<!-- REIN_BASE_URL endpoint -->\n", False)
with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    (root / "test_skipped.py").write_text('import unittest\nclass T(unittest.TestCase):\n @unittest.skip("dependency unavailable")\n def test_required_behavior(self): self.fail("never reached")\n')
    fingerprint, _ = ev.source_fingerprint(root, ["test_skipped.py"])
    def evaluate(command, review):
        manifest = root / "manifest.json"
        manifest.write_text(json.dumps({"root": str(root), "source_paths": ["test_skipped.py"], "source_fingerprint": fingerprint, "commands": [command], "review": {"document_quality": review}}))
        return ev.evaluate(manifest, root / "report.json")
    skipped = evaluate({"id": "real-unittest-all-skipped", "argv": [sys.executable, "-B", "-m", "unittest", "discover"], "kind": "test", "runner": "unittest"}, "reviewed")
    report["all_skipped_report"] = skipped
    record("all skipped does not pass", "failed", skipped["status"])
    timeout = ev.run_command({"id": "actual-timeout-output", "argv": [sys.executable, "-u", "-c", 'import time; print("failure context",flush=True);time.sleep(2)'], "timeout_seconds": 0.1}, root)
    report["timeout_command"] = timeout
    record("timeout stdout preserved", "failure context\n", timeout["stdout"])
    record("timeout does not pass", "failed", timeout["status"])
    unreviewed = evaluate({"id": "technical-pass", "argv": [sys.executable, "-B", "-c", 'print("done")']}, "unreviewed")
    report["unreviewed_report"] = unreviewed
    record("document unreviewed status", "undetermined", unreviewed["status"])
    manual = evaluate({"id": "manual-pending", "argv": [sys.executable, "-B", "-c", 'print("done")'], "require_review": True}, "unreviewed")
    report["command_manual_review_report"] = manual
cargo = "test result: ok. 3 passed; 0 failed; 0 ignored\ntest result: ok. 5 passed; 0 failed; 0 ignored"
report["cargo_count_probe"] = {"input": cargo, "test_count": ev.test_count(cargo, ""), "test_stats": ev.test_stats(cargo, "")}
record("cargo total tests_run", 8, ev.test_count(cargo, ""))
report["source_sha256_after"] = hashes()
report["source_unchanged_during_review"] = report["source_sha256_before"] == report["source_sha256_after"]
output = OUT / "rereview-02-results.json"
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"output": str(output), "source_unchanged": report["source_unchanged_during_review"], "selftests_exit": run.returncode, "checks": report["checks"], "cargo_count_probe": report["cargo_count_probe"], "command_manual_review_status": manual["status"]}, ensure_ascii=False, indent=2))
