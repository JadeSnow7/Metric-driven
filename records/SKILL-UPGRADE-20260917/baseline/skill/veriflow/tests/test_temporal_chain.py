import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_task.py"
SNAPSHOT = ROOT / "scripts" / "authorization_snapshot.py"
TEMPLATE = ROOT / "assets" / "templates" / "task-state.example.json"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class TemporalChainTests(unittest.TestCase):
    def setUp(self):
        self.validator = load(VALIDATOR, "temporal_validator")
        self.snapshot = load(SNAPSHOT, "temporal_snapshot")

    def test_revoked_prior_commit_snapshot_supports_new_push(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.invalid"], check=True)
            (repo / "app.txt").write_text("baseline\n")
            subprocess.run(["git", "-C", str(repo), "add", "app.txt"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
            state = json.loads(TEMPLATE.read_text())
            state["schema_version"] = "1.3"
            state["sources"][0].update(reference="conversation:test", adoption="accepted")
            state["authorization"]["commit"].update(status="authorized", source_id="SRC-001")
            revision = "patch:base:verified"
            record = {"authorization_action": "commit", "target": "local", "revision": revision}
            snap = self.snapshot.capture_snapshot(state, "commit", "local", revision)
            action = {**record, "status": "completed", "authorization_snapshot": snap}
            state["authorization"]["commit"]["status"] = "not_authorized"
            indexes = {"actions": {"ACT-C": action}}
            self.assertTrue(self.validator.historical_action_authorized(state, indexes, "commit", revision))
            self.assertFalse(self.validator.historical_action_authorized(state, indexes, "commit", "patch:other"))

    def test_missing_snapshot_does_not_support_prior_action(self):
        state = json.loads(TEMPLATE.read_text())
        state["schema_version"] = "1.3"
        action = {"authorization_action": "push", "status": "completed", "revision": "rev-1"}
        self.assertFalse(self.validator.historical_action_authorized(state, {"actions": {"ACT-P": action}}, "push", "rev-1"))

    def test_current_revoked_action_remains_blocked(self):
        state = json.loads(TEMPLATE.read_text())
        state["schema_version"] = "1.3"
        state["authorization"]["push"]["status"] = "not_authorized"
        errors = []
        self.validator.check_side_effect(state, {"actions": {}}, "push", "rev-1", "origin/main", False, errors)
        self.assertIn("AUTH_PUSH", {item["code"] for item in errors})


if __name__ == "__main__":
    unittest.main()
