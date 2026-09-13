from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = SKILL_ROOT / "scripts/validate_task.py"
TEMPLATE = SKILL_ROOT / "assets/templates/task-state.example.json"
RECORD_DIR = "records/TASK-001"


def run(command: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ScenarioRepository:
    def __init__(self) -> None:
        self._temporary = tempfile.TemporaryDirectory(prefix="edd-scenario-")
        self.root = Path(self._temporary.name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Scenario Test")
        self.git("config", "user.email", "scenario@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        (self.root / "app.txt").write_text("baseline\n", encoding="utf-8")
        self.git("add", "app.txt")
        self.git("commit", "--no-verify", "-m", "baseline")
        self.base = self.head()
        self.records = self.root / RECORD_DIR
        self.manifest = self.records / "task-state.json"
        self.records.mkdir(parents=True)
        self.state: dict[str, Any] = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        self.state["baseline"]["git_ref"] = self.base
        self.state["baseline"]["prepared_at"] = "2026-01-01T00:00:00Z"
        self.state["sources"][0]["reference"] = "conversation:scenario-test"
        self.state["implementation_tasks"][0]["file_scope"] = ["app.txt", "feature.txt"]
        self.state["recovery_strategy"]["owner"] = "scenario-owner"
        self.write_state()

    def close(self) -> None:
        self._temporary.cleanup()

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return run(["git", *args], self.root)

    def head(self) -> str:
        return self.git("rev-parse", "HEAD").stdout.strip()

    def commit_all(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "--no-verify", "-m", message)
        return self.head()

    def reset_baseline_to_head(self) -> None:
        self.base = self.head()
        self.state["baseline"]["git_ref"] = self.base
        self.write_state()

    def write_state(self) -> None:
        self.manifest.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def invoke(self, *args: str) -> subprocess.CompletedProcess[str]:
        return run(
            [sys.executable, str(VALIDATOR), str(self.manifest), "--repo", str(self.root), *args],
            self.root,
            check=False,
        )

    def validate(self, gate: str) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        result = self.invoke("--gate", gate)
        return result, json.loads(result.stdout)

    def revision(self) -> str:
        result = self.invoke("--print-revision")
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        return result.stdout.strip()

    def write_evidence(
        self,
        evidence_id: str,
        relative_path: str,
        text: str,
        supports: list[str],
    ) -> dict[str, Any]:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        item = {
            "id": evidence_id,
            "path": relative_path,
            "kind": "test_report",
            "supports": supports,
            "revision": "pending",
            "sha256": sha256_file(path),
            "status": "current",
            "result": "passed",
            "observed_at": "2026-01-01T01:00:00Z",
        }
        self.state["evidence"].append(item)
        return item

    def bind_current_revision(self) -> str:
        self.write_state()
        revision = self.revision()
        for item in self.state["evidence"]:
            if item.get("status") == "current":
                item["revision"] = revision
        for item in self.state["changes"]:
            item["revision"] = revision
        self.write_state()
        return revision

    def authorize(self, action: str) -> None:
        self.state["authorization"][action] = {"status": "authorized", "source_id": "SRC-001"}

    def record_action(self, action_id: str, action: str, receipt: str, kind: str | None = None) -> None:
        self.state["actions"].append(
            {
                "id": action_id,
                "kind": kind or action,
                "status": "completed",
                "authorization_action": action,
                "idempotency_key": f"{action}:TASK-001:{action_id}",
                "receipt": receipt,
            }
        )

    def make_completed(self) -> None:
        (self.root / "app.txt").write_text("implemented\n", encoding="utf-8")
        (self.root / "feature.txt").write_text("new behavior\n", encoding="utf-8")
        self.state["evidence"] = []
        self.write_evidence(
            "EVD-001",
            f"{RECORD_DIR}/evidence/result.txt",
            "behavior and end-to-end checks passed\n",
            ["MET-001", "MET-002"],
        )
        self.state["task"]["status"] = "verified"
        self.state["main_tasks"][0]["status"] = "verified"
        self.state["implementation_tasks"][0]["status"] = "verified"
        self.state["implementation_tasks"][0]["evidence_ids"] = ["EVD-001"]
        for metric in self.state["metrics"]:
            metric["status"] = "passed"
            metric["evidence_ids"] = ["EVD-001"]
        self.state["changes"] = [
            {
                "id": "CHG-001",
                "implementation_task_ids": ["IT-001"],
                "paths": ["app.txt", "feature.txt", f"{RECORD_DIR}/evidence"],
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
        self.authorize("commit")
        self.state["delivery"]["local_validation"] = "passed"
        self.bind_current_revision()


class EvidenceDrivenScenarios(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = ScenarioRepository()

    def tearDown(self) -> None:
        self.repo.close()

    @staticmethod
    def codes(result: dict[str, Any]) -> set[str]:
        return {item["code"] for item in result["errors"]}

    @staticmethod
    def warning_codes(result: dict[str, Any]) -> set[str]:
        return {item["code"] for item in result["warnings"]}

    # --- discovery, structure and baseline -------------------------------

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

    def test_confirmed_dirty_dependency_allows_implementation(self) -> None:
        self.repo.state["baseline"]["worktree_status"] = "dirty_dependency_confirmed"
        self.repo.write_state()
        process, result = self.repo.validate("implementation")
        self.assertEqual(process.returncode, 0, result)

        self.repo.state["baseline"]["worktree_status"] = "unknown"
        self.repo.write_state()
        process, result = self.repo.validate("implementation")
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("BASELINE_NOT_CLEAN", self.codes(result))

    def test_schema_1_0_is_rejected_with_migration_hint(self) -> None:
        self.repo.state["schema_version"] = "1.0"
        self.repo.write_state()
        process, result = self.repo.validate("record")
        self.assertNotEqual(process.returncode, 0)
        messages = [item["message"] for item in result["errors"] if item["code"] == "SCHEMA_VERSION"]
        self.assertTrue(messages and "1.1" in messages[0], result)

    def test_task_status_and_mode_are_validated(self) -> None:
        self.repo.state["task"]["status"] = "done"
        self.repo.state["task"]["mode"] = "first-run"
        self.repo.write_state()
        process, result = self.repo.validate("record")
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("TASK_RECORD_STATUS", self.codes(result))
        self.assertIn("TASK_MODE", self.codes(result))

    def test_template_placeholders_warn_on_record_and_block_implementation(self) -> None:
        self.repo.state = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        self.repo.state["baseline"]["git_ref"] = self.repo.base
        self.repo.write_state()
        record_process, record = self.repo.validate("record")
        self.assertEqual(record_process.returncode, 0, record)
        self.assertIn("PLACEHOLDER_VALUE", self.warning_codes(record))
        implementation_process, implementation = self.repo.validate("implementation")
        self.assertNotEqual(implementation_process.returncode, 0)
        self.assertIn("PLACEHOLDER_VALUE", self.codes(implementation))

    def test_malformed_types_are_reported_without_crashing(self) -> None:
        mutations = {
            "task is a list": lambda state: state.__setitem__("task", ["oops"]),
            "metric_ids is null": lambda state: state["main_tasks"][0].__setitem__("metric_ids", None),
            "main_task_id is a list": lambda state: state["metrics"][0].__setitem__("main_task_id", ["MT-001"]),
            "acceptance holds objects": lambda state: state["implementation_tasks"][0].__setitem__(
                "acceptance", [{"id": "MET-001"}]
            ),
            "authorization is a string": lambda state: state.__setitem__("authorization", "yes"),
            "change paths is a string": lambda state: state.__setitem__(
                "changes",
                [
                    {
                        "id": "CHG-001",
                        "implementation_task_ids": ["IT-001"],
                        "paths": "app.txt",
                        "evidence_ids": [],
                        "revision": "pending",
                        "status": "reviewed",
                    }
                ],
            ),
        }
        original = copy.deepcopy(self.repo.state)
        for label, mutate in mutations.items():
            with self.subTest(label):
                self.repo.state = copy.deepcopy(original)
                mutate(self.repo.state)
                self.repo.write_state()
                for gate in ("record", "local-commit", "deploy"):
                    process = self.repo.invoke("--gate", gate)
                    self.assertNotIn("Traceback", process.stderr)
                    self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
                    self.assertTrue(json.loads(process.stdout)["errors"])

    # --- revision fingerprint ---------------------------------------------

    def test_read_only_revision_preserves_preexisting_dirty_change(self) -> None:
        user_file = self.repo.root / "app.txt"
        user_file.write_text("owner's uncommitted work\n", encoding="utf-8")
        before = user_file.read_bytes()
        status_before = self.repo.git("status", "--porcelain=v1").stdout
        token = self.repo.revision()
        status_after = self.repo.git("status", "--porcelain=v1").stdout
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

    def test_staging_and_committing_new_files_keeps_revision_stable(self) -> None:
        self.repo.make_completed()
        untracked = self.repo.revision()
        self.repo.git("add", "-A")
        staged = self.repo.revision()
        self.repo.git("commit", "--no-verify", "-m", "implement")
        committed = self.repo.revision()
        self.assertEqual(staged, untracked)
        self.assertEqual(committed, untracked)
        process, result = self.repo.validate("local-commit")
        self.assertEqual(process.returncode, 0, result)

    def test_revision_ignores_local_diff_configuration(self) -> None:
        self.repo.make_completed()
        before = self.repo.revision()
        self.repo.git("config", "diff.noprefix", "true")
        self.repo.git("config", "diff.algorithm", "patience")
        self.repo.git("config", "diff.renames", "copies")
        self.repo.git("config", "diff.context", "10")
        self.assertEqual(self.repo.revision(), before)

    def test_additional_evidence_does_not_invalidate_existing_evidence(self) -> None:
        self.repo.make_completed()
        first_revision = self.repo.state["evidence"][0]["revision"]
        second = self.repo.write_evidence(
            "EVD-002",
            f"{RECORD_DIR}/evidence/end-to-end.txt",
            "end-to-end acceptance passed\n",
            ["MET-001"],
        )
        second["revision"] = self.repo.revision()
        self.repo.state["overall_acceptance"]["evidence_ids"].append("EVD-002")
        self.repo.write_state()
        self.assertEqual(second["revision"], first_revision)
        process, result = self.repo.validate("local-commit")
        self.assertEqual(process.returncode, 0, result)

    def test_status_and_log_updates_do_not_invalidate_behavioral_evidence(self) -> None:
        self.repo.make_completed()
        revision_before = self.repo.revision()
        summary = self.repo.records / "task-summary.md"
        log = self.repo.records / "work-log.md"
        summary.write_text("# Current verified state\n", encoding="utf-8")
        log.write_text("# Append-only verification event\n", encoding="utf-8")
        self.repo.state["changes"][0]["paths"].extend(
            [f"{RECORD_DIR}/task-summary.md", f"{RECORD_DIR}/work-log.md"]
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
        for deliverable in ("index.md", "evidence/report.txt"):
            with self.subTest(deliverable):
                revision_before = self.repo.revision()
                path = self.repo.root / deliverable
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("real deliverable\n", encoding="utf-8")
                self.assertNotEqual(self.repo.revision(), revision_before)

    # --- evidence integrity -----------------------------------------------

    def test_edited_evidence_content_is_detected(self) -> None:
        self.repo.make_completed()
        evidence_file = self.repo.records / "evidence/result.txt"
        evidence_file.write_text("behavior checks FAILED\n", encoding="utf-8")
        process, result = self.repo.validate("record")
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("EVIDENCE_HASH_MISMATCH", self.codes(result))

    def test_missing_evidence_hash_warns_on_record_and_blocks_local_commit(self) -> None:
        self.repo.make_completed()
        del self.repo.state["evidence"][0]["sha256"]
        self.repo.write_state()
        record_process, record = self.repo.validate("record")
        self.assertEqual(record_process.returncode, 0, record)
        self.assertIn("EVIDENCE_HASH_MISSING", self.warning_codes(record))
        commit_process, commit = self.repo.validate("local-commit")
        self.assertNotEqual(commit_process.returncode, 0)
        self.assertIn("EVIDENCE_HASH_MISSING", self.codes(commit))

    def test_evidence_outside_record_directory_warns(self) -> None:
        self.repo.make_completed()
        self.repo.write_evidence("EVD-002", "benchmarks/latency.txt", "p95 unchanged\n", ["MET-002"])
        self.repo.state["changes"][0]["paths"].append("benchmarks/latency.txt")
        self.repo.bind_current_revision()
        process, result = self.repo.validate("record")
        self.assertEqual(process.returncode, 0, result)
        self.assertIn("EVIDENCE_OUTSIDE_RECORD_DIR", self.warning_codes(result))

    def test_print_sha256_matches_recorded_hash(self) -> None:
        self.repo.make_completed()
        relative = self.repo.state["evidence"][0]["path"]
        process = self.repo.invoke("--print-sha256", relative)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertEqual(process.stdout.strip(), self.repo.state["evidence"][0]["sha256"])

    # --- metrics and acceptance -------------------------------------------

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

    # --- review coverage --------------------------------------------------

    def test_unreviewed_changed_path_blocks_local_commit(self) -> None:
        self.repo.make_completed()
        (self.repo.root / "unowned.txt").write_text("not in CHG paths\n", encoding="utf-8")
        self.repo.bind_current_revision()
        process, result = self.repo.validate("local-commit")
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("CHANGED_PATH_UNREVIEWED", self.codes(result))

    def test_renamed_file_requires_review_of_original_path(self) -> None:
        (self.repo.root / "legacy.txt").write_text("legacy line\n" * 20, encoding="utf-8")
        self.repo.commit_all("add legacy file")
        self.repo.reset_baseline_to_head()
        self.repo.make_completed()
        self.repo.git("mv", "legacy.txt", "renamed.txt")
        self.repo.state["changes"][0]["paths"].append("renamed.txt")
        self.repo.bind_current_revision()
        process, result = self.repo.validate("local-commit")
        self.assertNotEqual(process.returncode, 0)
        unreviewed = [
            item["message"] for item in result["errors"] if item["code"] == "CHANGED_PATH_UNREVIEWED"
        ]
        self.assertTrue(any("legacy.txt" in message for message in unreviewed), result)

    # --- authorization and side effects -----------------------------------

    def test_existing_commit_authorization_satisfies_local_gate(self) -> None:
        self.repo.make_completed()
        process, result = self.repo.validate("local-commit")
        self.assertEqual(process.returncode, 0, result)
        self.assertNotIn("AUTH_COMMIT", self.codes(result))

    def test_authorization_requires_accepted_source(self) -> None:
        self.repo.make_completed()
        self.repo.state["sources"].append(
            {
                "id": "SRC-002",
                "kind": "user_requirement",
                "reference": "conversation:earlier-request",
                "summary": "an instruction the user later withdrew",
                "adoption": "superseded",
            }
        )
        self.repo.state["authorization"]["commit"] = {"status": "authorized", "source_id": "SRC-002"}
        self.repo.write_state()
        process, result = self.repo.validate("local-commit")
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("AUTH_SOURCE_NOT_ACCEPTED", self.codes(result))

    def test_unauthorized_deploy_is_blocked(self) -> None:
        self.repo.make_completed()
        self.repo.state["delivery"].update(
            {"local_commit": "completed", "push": "completed", "remote_ci": "passed", "merge": "completed"}
        )
        self.repo.authorize("push")
        self.repo.authorize("merge")
        self.repo.write_state()
        process, result = self.repo.validate("deploy")
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("AUTH_DEPLOY", self.codes(result))

    def test_unauthorized_executed_action_warns_on_record_and_blocks_push(self) -> None:
        self.repo.make_completed()
        self.repo.record_action("ACT-001", "deploy", "deployment-42")
        self.repo.write_state()
        record_process, record = self.repo.validate("record")
        self.assertEqual(record_process.returncode, 0, record)
        self.assertIn("ACTION_UNAUTHORIZED", self.warning_codes(record))
        commit_process, commit = self.repo.validate("local-commit")
        self.assertEqual(commit_process.returncode, 0, commit)
        self.assertIn("ACTION_UNAUTHORIZED", self.warning_codes(commit))
        _, push = self.repo.validate("push")
        self.assertIn("ACTION_UNAUTHORIZED", self.codes(push))

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
        self.repo.authorize("push")
        self.repo.record_action("ACT-001", "push", "origin/main@example-commit")
        self.repo.write_state()
        self.repo.commit_all("completed task record")
        process, result = self.repo.validate("push")
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(self.codes(result), {"DELIVERY_ALREADY_COMPLETED"}, result)

    def test_repeat_detection_uses_authorization_action_not_kind(self) -> None:
        self.repo.make_completed()
        self.repo.commit_all("implement")
        self.repo.state["delivery"]["local_commit"] = "completed"
        self.repo.authorize("push")
        self.repo.record_action("ACT-001", "push", "origin/feature@abc", kind="git push to origin")
        self.repo.write_state()
        process, result = self.repo.validate("push")
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("DELIVERY_ALREADY_COMPLETED", self.codes(result))

    def test_full_delivery_chain_passes_when_honestly_recorded(self) -> None:
        self.repo.make_completed()
        process, result = self.repo.validate("local-commit")
        self.assertEqual(process.returncode, 0, result)

        commit = self.repo.commit_all("implement task")
        self.repo.state["delivery"]["local_commit"] = "completed"
        self.repo.record_action("ACT-001", "commit", commit)
        self.repo.authorize("push")
        self.repo.write_state()
        _, repeat = self.repo.validate("local-commit")
        self.assertEqual(self.codes(repeat), {"DELIVERY_ALREADY_COMPLETED"}, repeat)
        process, result = self.repo.validate("push")
        self.assertEqual(process.returncode, 0, result)

        self.repo.state["delivery"].update({"push": "completed", "remote_ci": "passed"})
        self.repo.record_action("ACT-002", "push", f"origin/task@{commit}")
        self.repo.authorize("merge")
        self.repo.write_state()
        process, result = self.repo.validate("merge")
        self.assertEqual(process.returncode, 0, result)

        self.repo.state["delivery"]["merge"] = "completed"
        self.repo.record_action("ACT-003", "merge", "pull-request-7")
        self.repo.authorize("deploy")
        self.repo.write_state()
        process, result = self.repo.validate("deploy")
        self.assertEqual(process.returncode, 0, result)


if __name__ == "__main__":
    unittest.main()
