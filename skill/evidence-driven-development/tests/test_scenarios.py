from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = SKILL_ROOT / "scripts/validate_task.py"
TEMPLATE = SKILL_ROOT / "assets/templates/task-state.example.json"


def run(command: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


class ScenarioRepository:
    def __init__(self) -> None:
        self._temporary = tempfile.TemporaryDirectory(prefix="edd-scenario-")
        self.root = Path(self._temporary.name)
        run(["git", "init", "-b", "main"], self.root)
        run(["git", "config", "user.name", "Scenario Test"], self.root)
        run(["git", "config", "user.email", "scenario@example.invalid"], self.root)
        (self.root / "app.txt").write_text("baseline\n", encoding="utf-8")
        run(["git", "add", "app.txt"], self.root)
        run(["git", "commit", "-m", "baseline"], self.root)
        self.base = run(["git", "rev-parse", "HEAD"], self.root).stdout.strip()
        self.manifest = self.root / "records/task-state.json"
        self.manifest.parent.mkdir(parents=True)
        self.state: dict[str, Any] = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        self.state["baseline"]["git_ref"] = self.base
        self.state["baseline"]["prepared_at"] = "2026-01-01T00:00:00Z"
        self.write_state()

    def close(self) -> None:
        self._temporary.cleanup()

    def write_state(self) -> None:
        self.manifest.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def validate(self, gate: str) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        result = run(
            ["python3", str(VALIDATOR), str(self.manifest), "--repo", str(self.root), "--gate", gate],
            self.root,
            check=False,
        )
        return result, json.loads(result.stdout)

    def revision(self) -> str:
        result = run(
            ["python3", str(VALIDATOR), str(self.manifest), "--repo", str(self.root), "--print-revision"],
            self.root,
        )
        return result.stdout.strip()

    def make_completed(self) -> None:
        (self.root / "app.txt").write_text("implemented\n", encoding="utf-8")
        evidence_path = self.root / "evidence/result.txt"
        evidence_path.parent.mkdir(parents=True)
        evidence_path.write_text("behavior and end-to-end checks passed\n", encoding="utf-8")
        self.state["task"]["status"] = "verified"
        self.state["main_tasks"][0]["status"] = "verified"
        self.state["implementation_tasks"][0]["status"] = "verified"
        self.state["implementation_tasks"][0]["evidence_ids"] = ["EVD-001"]
        for metric in self.state["metrics"]:
            metric["status"] = "passed"
            metric["evidence_ids"] = ["EVD-001"]
        self.state["evidence"] = [
            {
                "id": "EVD-001",
                "path": "evidence/result.txt",
                "kind": "test_report",
                "supports": ["MET-001", "MET-002"],
                "revision": "pending",
                "status": "current",
                "result": "passed",
                "observed_at": "2026-01-01T01:00:00Z",
            }
        ]
        self.state["changes"] = [
            {
                "id": "CHG-001",
                "implementation_task_ids": ["IT-001"],
                "paths": ["app.txt", "evidence/result.txt"],
                "evidence_ids": ["EVD-001"],
                "revision": "pending",
                "status": "reviewed",
            }
        ]
        self.state["overall_acceptance"] = {
            "metric_ids": ["MET-001", "MET-002"],
            "evidence_ids": ["EVD-001"],
            "status": "passed",
        }
        self.state["authorization"]["commit"] = {
            "status": "authorized",
            "source_id": "SRC-001",
        }
        self.state["delivery"]["local_validation"] = "passed"
        self.write_state()
        revision = self.revision()
        self.state["evidence"][0]["revision"] = revision
        self.state["changes"][0]["revision"] = revision
        self.write_state()


class EvidenceDrivenScenarios(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = ScenarioRepository()

    def tearDown(self) -> None:
        self.repo.close()

    @staticmethod
    def codes(result: dict[str, Any]) -> set[str]:
        return {item["code"] for item in result["errors"]}

    def test_vague_request_blocks_implementation_but_record_is_valid(self) -> None:
        self.repo.state["discovery"] = {"status": "needs_clarification"}
        self.repo.state["main_tasks"] = []
        self.repo.state["metrics"] = []
        self.repo.state["implementation_tasks"] = []
        self.repo.state["overall_acceptance"] = {
            "metric_ids": [],
            "evidence_ids": [],
            "status": "undetermined",
        }
        self.repo.write_state()
        record_process, record = self.repo.validate("record")
        implementation_process, implementation = self.repo.validate("implementation")
        self.assertEqual(record_process.returncode, 0, record)
        self.assertNotEqual(implementation_process.returncode, 0)
        self.assertIn("DISCOVERY_NOT_READY", self.codes(implementation))
        self.assertIn("MAIN_TASKS_MISSING", self.codes(implementation))

    def test_metric_cannot_exist_before_its_main_task(self) -> None:
        self.repo.state["main_tasks"] = []
        self.repo.write_state()
        process, result = self.repo.validate("record")
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("CROSSREF_MAIN_TASK", self.codes(result))

    def test_read_only_revision_preserves_preexisting_dirty_change(self) -> None:
        user_file = self.repo.root / "app.txt"
        user_file.write_text("owner's uncommitted work\n", encoding="utf-8")
        before = user_file.read_bytes()
        status_before = run(["git", "status", "--porcelain=v1"], self.repo.root).stdout
        token = self.repo.revision()
        status_after = run(["git", "status", "--porcelain=v1"], self.repo.root).stdout
        self.assertTrue(token.startswith("patch:"))
        self.assertEqual(user_file.read_bytes(), before)
        self.assertEqual(status_after, status_before)

    def test_evidence_becomes_stale_after_implementation_change(self) -> None:
        self.repo.make_completed()
        passed_process, passed = self.repo.validate("local-commit")
        self.assertEqual(passed_process.returncode, 0, passed)
        (self.repo.root / "app.txt").write_text("changed after validation\n", encoding="utf-8")
        stale_process, stale = self.repo.validate("local-commit")
        self.assertNotEqual(stale_process.returncode, 0)
        self.assertIn("EVIDENCE_STALE", self.codes(stale))

    def test_status_and_log_updates_do_not_invalidate_behavioral_evidence(self) -> None:
        self.repo.make_completed()
        revision_before = self.repo.revision()
        summary = self.repo.root / "records/task-summary.md"
        log = self.repo.root / "records/work-log.md"
        summary.write_text("# Current verified state\n", encoding="utf-8")
        log.write_text("# Append-only verification event\n", encoding="utf-8")
        self.repo.state["changes"][0]["paths"].extend(
            ["records/task-summary.md", "records/work-log.md"]
        )
        self.repo.write_state()
        revision_after = self.repo.revision()
        process, result = self.repo.validate("local-commit")
        self.assertEqual(revision_after, revision_before)
        self.assertEqual(process.returncode, 0, result)

    def test_root_manifest_does_not_exclude_root_delivery_names(self) -> None:
        self.repo.make_completed()
        old_manifest = self.repo.manifest
        self.repo.manifest = self.repo.root / "task-state.json"
        self.repo.write_state()
        old_manifest.unlink()
        revision_before = self.repo.revision()
        (self.repo.root / "index.md").write_text("real deliverable\n", encoding="utf-8")
        revision_after = self.repo.revision()
        self.assertNotEqual(revision_after, revision_before)

    def test_undetermined_mandatory_gate_is_not_passed(self) -> None:
        self.repo.make_completed()
        self.repo.state["metrics"][0]["status"] = "undetermined"
        self.repo.write_state()
        process, result = self.repo.validate("local-commit")
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("MANDATORY_GATE", self.codes(result))

    def test_verified_subtask_does_not_override_failed_overall_result(self) -> None:
        self.repo.make_completed()
        self.repo.state["overall_acceptance"]["status"] = "failed"
        self.repo.write_state()
        process, result = self.repo.validate("local-commit")
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("OVERALL_NOT_PASSED", self.codes(result))

    def test_existing_commit_authorization_satisfies_local_gate(self) -> None:
        self.repo.make_completed()
        process, result = self.repo.validate("local-commit")
        self.assertEqual(process.returncode, 0, result)
        self.assertNotIn("AUTH_COMMIT", self.codes(result))

    def test_unauthorized_deploy_is_blocked(self) -> None:
        self.repo.make_completed()
        self.repo.state["delivery"].update(
            {"local_commit": "completed", "push": "completed", "remote_ci": "passed", "merge": "completed"}
        )
        self.repo.state["authorization"]["push"] = {"status": "authorized", "source_id": "SRC-001"}
        self.repo.state["authorization"]["merge"] = {"status": "authorized", "source_id": "SRC-001"}
        self.repo.write_state()
        process, result = self.repo.validate("deploy")
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("AUTH_DEPLOY", self.codes(result))

    def test_duplicate_side_effect_key_blocks_resume_record(self) -> None:
        action = {
            "kind": "push",
            "status": "completed",
            "authorization_action": "push",
            "idempotency_key": "push:TASK-001:origin-main",
            "receipt": "remote-ref-1",
        }
        first = copy.deepcopy(action)
        first["id"] = "ACT-001"
        second = copy.deepcopy(action)
        second["id"] = "ACT-002"
        self.repo.state["actions"] = [first, second]
        self.repo.write_state()
        process, result = self.repo.validate("record")
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("ACTION_KEY_DUPLICATE", self.codes(result))

    def test_completed_push_is_not_repeated_on_resume(self) -> None:
        self.repo.make_completed()
        self.repo.state["delivery"]["local_commit"] = "completed"
        self.repo.state["delivery"]["push"] = "completed"
        self.repo.state["authorization"]["push"] = {
            "status": "authorized",
            "source_id": "SRC-001",
        }
        self.repo.state["actions"] = [
            {
                "id": "ACT-001",
                "kind": "push",
                "status": "completed",
                "authorization_action": "push",
                "idempotency_key": "push:TASK-001:origin-main",
                "receipt": "origin/main@example-commit",
            }
        ]
        self.repo.write_state()
        run(["git", "add", "."], self.repo.root)
        run(["git", "commit", "-m", "completed task record"], self.repo.root)
        process, result = self.repo.validate("push")
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("DELIVERY_ALREADY_COMPLETED", self.codes(result))

    def test_unreviewed_changed_path_blocks_local_commit(self) -> None:
        self.repo.make_completed()
        (self.repo.root / "unowned.txt").write_text("not in CHG paths\n", encoding="utf-8")
        revision = self.repo.revision()
        self.repo.state["evidence"][0]["revision"] = revision
        self.repo.state["changes"][0]["revision"] = revision
        self.repo.write_state()
        process, result = self.repo.validate("local-commit")
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("CHANGED_PATH_UNREVIEWED", self.codes(result))


if __name__ == "__main__":
    unittest.main()
