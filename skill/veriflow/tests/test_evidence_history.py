import hashlib
import importlib.util
import tempfile
import unittest
import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_task.py"
sys.path.insert(0, str(SCRIPT.parent))
RECORDER = SCRIPT.with_name("record_execution.py")
TEMPLATE = SCRIPT.parents[1] / "assets" / "templates" / "task-state.example.json"
spec = importlib.util.spec_from_file_location("validate_task", SCRIPT)
validate_task = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(validate_task)


class EvidenceHistoryTests(unittest.TestCase):
    def _repo_state(self, root, external=None):
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "t@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "T"], check=True)
        (root / "input.txt").write_text("input\n")
        subprocess.run(["git", "-C", str(root), "add", "input.txt"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "base"], check=True)
        state = json.loads(TEMPLATE.read_text())
        # Keep these regressions pinned to the schema 1.2 record shape.
        state["schema_version"] = "1.2"
        state.pop("spec", None)
        state.pop("binding", None)
        state["baseline"]["git_ref"] = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
        state["baseline"]["prepared_at"] = "2026-01-01T00:00:00Z"
        state["sources"][0]["reference"] = "conversation:test"
        if external is not None:
            state["baseline"]["external_inputs"] = [external]
        manifest = root / "records" / "TASK-001" / "task-state.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps(state))
        return manifest

    def test_recorder_rejects_undeclared_external_before_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            manifest = self._repo_state(root)
            outside = root.parent / "outside.txt"
            outside.write_text("outside\n")
            marker = root / "marker"
            output = root / "records" / "TASK-001" / "evidence.json"
            result = subprocess.run([sys.executable, str(RECORDER), "--output", str(output), "--repo", str(root), "--state", str(manifest), "--fixture", str(outside), "--", sys.executable, "-c", f"open({str(marker)!r}, 'w').write('ran')"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(marker.exists())

    def test_recorder_marks_ignored_fixture_changed_during_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            manifest = self._repo_state(root)
            fixture = root / "fixture.txt"
            fixture.write_text("before\n")
            (root / ".gitignore").write_text("fixture.txt\n")
            declaration = {"path": str(fixture.resolve()), "sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(), "identity": "fixture", "reproduction": "fixture"}
            state = json.loads(manifest.read_text())
            state["baseline"]["external_inputs"] = [declaration]
            manifest.write_text(json.dumps(state))
            output = root / "records" / "TASK-001" / "changed.json"
            result = subprocess.run([sys.executable, str(RECORDER), "--output", str(output), "--repo", str(root), "--state", str(manifest), "--fixture", str(fixture), "--", sys.executable, "-c", f"open({str(fixture)!r}, 'w').write('after\\n')"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            record = json.loads(output.read_text())
            self.assertEqual(record["result"], "revision_changed")

    def test_stale_input_is_integrity_only_when_old_file_is_gone(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            errors = []
            validate_task.validate_input_declaration(
                repo, {"baseline": {"external_inputs": []}}, "/old/missing-fixture", {"sha256": "a" * 64},
                historical=True, evidence_id="EVD-OLD", errors=errors,
            )
            self.assertEqual(errors, [])

    def test_stale_input_with_tampered_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors = []
            validate_task.validate_input_declaration(
                Path(tmp), {"baseline": {}}, "/old/input", {"sha256": "bad"},
                historical=True, evidence_id="EVD-OLD", errors=errors,
            )
            self.assertTrue(any(item["code"] == "EXECUTION_INPUT_DECLARATION" for item in errors))

    def test_external_fixture_requires_complete_matching_declaration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            fixture = root / "external" / "fixture.txt"
            fixture.parent.mkdir()
            fixture.write_text("fixture\n")
            path = str(fixture.resolve())
            sha = hashlib.sha256(fixture.read_bytes()).hexdigest()
            declaration = {"path": path, "sha256": sha, "identity": "fixture-1", "reproduction": "copy fixture-1"}
            state = {"baseline": {"external_inputs": [declaration]}}
            errors = []
            validate_task.validate_input_declaration(
                repo, state, path, {"kind": "fixture", **declaration},
                historical=False, evidence_id="EVD-CURRENT", errors=errors,
            )
            self.assertEqual(errors, [])
            errors = []
            validate_task.validate_input_declaration(
                repo, state, path, {"kind": "fixture", **{**declaration, "identity": "wrong"}},
                historical=False, evidence_id="EVD-CURRENT", errors=errors,
            )
            self.assertTrue(any(item["code"] == "EXECUTION_INPUT_DECLARATION" for item in errors))


if __name__ == "__main__":
    unittest.main()
