from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from rein_evaluate import evaluate, source_fingerprint, test_count, test_stats  # noqa: E402
import unittest


def write_manifest(tmp_path: Path, command: dict, *, review: str = "unreviewed") -> Path:
    (tmp_path / "input.txt").write_text("source\n", encoding="utf-8")
    fingerprint, _ = source_fingerprint(tmp_path, ["input.txt"])
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"root": str(tmp_path), "source_paths": ["input.txt"], "source_fingerprint": fingerprint, "commands": [command], "review": {"document_quality": review}}))
    return manifest


def python_command(code: str, **extra: object) -> dict:
    return {"id": "case", "argv": [sys.executable, "-c", code], **extra}


class ReinEvaluateTests(unittest.TestCase):
  def test_success_records_streams_duration_and_artifact(self) -> None:
    tmp_path = Path(__import__('tempfile').mkdtemp())
    artifact = tmp_path / "answer.txt"
    artifact.write_text("ok\n", encoding="utf-8")
    (tmp_path / "test_ok.py").write_text("import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n", encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    command = {"id": "case", "argv": [sys.executable, "-m", "unittest", "discover"], "kind": "test", "runner": "unittest", "expected_artifacts": [{"path": "answer.txt", "sha256": digest}]}
    manifest = write_manifest(tmp_path, command, review="reviewed")
    report = evaluate(manifest, tmp_path / "out.json")
    self.assertEqual(report["status"], "passed")
    self.assertEqual(report["commands"][0]["tests_run"], 1)
    self.assertIsNotNone(report["commands"][0]["duration_ms"])
    self.assertEqual(json.loads((tmp_path / "out.json").read_text())["status"], "passed")


  def test_fake_pass_zero_tests_and_bad_artifact_fail(self) -> None:
    for command in [
        python_command("print('passed')", kind="test"),
        python_command("raise SystemExit(2)"),
        {"id": "missing", "argv": [sys.executable, "-c", "print('1 passed')"], "expected_artifacts": ["missing.txt"]},
    ]:
      tmp_path = Path(__import__('tempfile').mkdtemp())
      manifest = write_manifest(tmp_path, command, review="reviewed")
      self.assertEqual(evaluate(manifest, tmp_path / "out.json")["status"], "failed")


  def test_disabled_required_command_is_not_run_and_fails_gate(self) -> None:
    tmp_path = Path(__import__('tempfile').mkdtemp())
    manifest = write_manifest(tmp_path, python_command("print('1 passed')", kind="test", enabled=False), review="reviewed")
    report = evaluate(manifest, tmp_path / "out.json")
    self.assertEqual(report["commands"][0]["status"], "not_run")
    self.assertEqual(report["status"], "failed")


  def test_stale_hash_fails(self) -> None:
    tmp_path = Path(__import__('tempfile').mkdtemp())
    artifact = tmp_path / "answer.txt"
    artifact.write_text("new", encoding="utf-8")
    manifest = write_manifest(tmp_path, python_command("print('done')", expected_artifacts=[{"path": "answer.txt", "sha256": "0" * 64}]), review="reviewed")
    report = evaluate(manifest, tmp_path / "out.json")
    self.assertTrue(any("hash mismatch" in reason for reason in report["commands"][0]["reasons"]))
    self.assertEqual(report["status"], "failed")


  def test_quality_review_never_auto_passes(self) -> None:
    tmp_path = Path(__import__('tempfile').mkdtemp())
    manifest = write_manifest(tmp_path, python_command("print('ok')"))
    report = evaluate(manifest, tmp_path / "out.json")
    self.assertEqual(report["status"], "undetermined")
    self.assertIn("unreviewed", " ".join(report["reasons"]))

  def test_empty_and_no_required_commands_fail(self) -> None:
    tmp_path = Path(__import__('tempfile').mkdtemp())
    (tmp_path / "input.txt").write_text("source\n", encoding="utf-8")
    fingerprint, _ = source_fingerprint(tmp_path, ["input.txt"])
    for commands in ([], [{"id": "optional", "required": False, "argv": [sys.executable, "-c", "print('ok')"]}]):
      manifest = tmp_path / ("empty.json" if not commands else "optional.json")
      manifest.write_text(json.dumps({"root": str(tmp_path), "source_paths": ["input.txt"], "source_fingerprint": fingerprint, "commands": commands, "review": {"document_quality": "reviewed"}}))
      self.assertEqual(evaluate(manifest, tmp_path / "out.json")["status"], "failed")

  def test_source_mutation_makes_old_report_stale(self) -> None:
    tmp_path = Path(__import__('tempfile').mkdtemp())
    manifest = write_manifest(tmp_path, python_command("print('ok')"), review="reviewed")
    (tmp_path / "input.txt").write_text("mutated\n", encoding="utf-8")
    report = evaluate(manifest, tmp_path / "out.json")
    self.assertIn("source fingerprint is missing or stale", report["reasons"])

  def test_all_skipped_unittest_does_not_pass(self) -> None:
    tmp_path = Path(__import__('tempfile').mkdtemp())
    (tmp_path / "test_skip.py").write_text("import unittest\nclass T(unittest.TestCase):\n @unittest.skip('fixture')\n def test_skip(self): pass\n", encoding="utf-8")
    manifest = write_manifest(tmp_path, {"id":"skip", "argv":[sys.executable,"-m","unittest","discover"], "kind":"test", "runner":"unittest"}, review="reviewed")
    report = evaluate(manifest, tmp_path / "out.json")
    self.assertEqual(report["commands"][0]["test_stats"]["passed"], 0)
    self.assertEqual(report["status"], "failed")

  def test_runner_bound_counts_accumulate_cargo_harnesses(self) -> None:
    output = "test result: ok. 3 passed; 0 failed; 2 ignored\ntest result: ok. 5 passed; 0 failed; 1 ignored"
    self.assertEqual(test_count(output, "", "cargo-test"), 8)
    self.assertEqual(test_stats(output, "", "cargo-test"), {"executed": 8, "passed": 8, "failed": 0, "skipped": 3})

  def test_unittest_failures_errors_and_skips_are_not_passed(self) -> None:
    stats = test_stats("Ran 5 tests\nFAILED (failures=1, errors=1, skipped=1)", "", "unittest")
    self.assertEqual(stats, {"executed": 4, "passed": 2, "failed": 2, "skipped": 1})

  def test_summary_parsers_use_runner_specific_final_lines(self) -> None:
    self.assertEqual(
      test_stats("test_example.py::test_one PASSED\n1 failed, 2 passed, 3 skipped in 0.1s", "", "pytest"),
      {"executed": 3, "passed": 2, "failed": 1, "skipped": 3},
    )
    self.assertEqual(
      test_stats("Test Files 2 passed (2)\nTests 8 passed | 1 skipped (9)", "", "vitest"),
      {"executed": 8, "passed": 8, "failed": 0, "skipped": 1},
    )

  def test_unittest_executed_excludes_skipped(self) -> None:
    self.assertEqual(
      test_stats("Ran 3 tests\nOK (skipped=2)", "", "unittest"),
      {"executed": 1, "passed": 1, "failed": 0, "skipped": 2},
    )

  def test_required_manual_review_is_undetermined_not_failed(self) -> None:
    tmp_path = Path(__import__('tempfile').mkdtemp())
    manifest = write_manifest(tmp_path, python_command("print('ok')", require_review=True), review="reviewed")
    report = evaluate(manifest, tmp_path / "out.json")
    self.assertEqual(report["commands"][0]["status"], "undetermined")
    self.assertEqual(report["status"], "undetermined")

  def test_real_unittest_failure_is_not_counted_as_passed(self) -> None:
    tmp_path = Path(__import__('tempfile').mkdtemp())
    (tmp_path / "test_failure.py").write_text(
      "import unittest\nclass T(unittest.TestCase):\n def test_failure(self): self.fail('fixture')\n",
      encoding="utf-8",
    )
    manifest = write_manifest(tmp_path, {"id":"failure", "argv":[sys.executable,"-m","unittest","discover"], "kind":"test", "runner":"unittest"}, review="reviewed")
    report = evaluate(manifest, tmp_path / "out.json")
    command = report["commands"][0]
    self.assertEqual(command["tests_run"], 1)
    self.assertEqual(command["test_stats"]["passed"], 0)
    self.assertEqual(command["test_stats"]["failed"], 1)
    self.assertEqual(report["status"], "failed")

  def test_unittest_zero_tests_does_not_pass(self) -> None:
    tmp_path = Path(__import__('tempfile').mkdtemp())
    manifest = write_manifest(tmp_path, {"id":"empty", "argv":[sys.executable,"-m","unittest","discover"], "kind":"test", "runner":"unittest"}, review="reviewed")
    report = evaluate(manifest, tmp_path / "out.json")
    self.assertEqual(report["commands"][0]["tests_run"], 0)
    self.assertEqual(report["status"], "failed")


if __name__ == "__main__":
  unittest.main()
