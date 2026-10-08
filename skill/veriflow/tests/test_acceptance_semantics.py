"""Schema 1.3 acceptance semantics: pre-implementation evidence, spec_satisfaction and deferred metrics."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_scenarios import ScenarioRepository

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_task.py"
RECORDER = ROOT / "scripts/record_execution.py"
IMPLEMENTED_CHECK = "import sys; sys.exit(0 if open('app.txt').read() == 'implemented\\n' else 1)"


def prepare() -> ScenarioRepository:
    """A completed 1.3 record with one condition bound to MET-001 and no evidence yet."""

    repo = ScenarioRepository()
    repo.make_completed()
    state = repo.state
    state["schema_version"] = "1.3"
    state["metrics"] = [state["metrics"][0]]
    state["main_tasks"][0]["metric_ids"] = ["MET-001"]
    state["implementation_tasks"][0]["acceptance"] = ["MET-001"]
    state["implementation_tasks"][0]["evidence_ids"] = []
    state["metrics"][0]["evidence_ids"] = []
    state["overall_acceptance"].update({"metric_ids": ["MET-001"], "evidence_ids": []})
    state["evidence"] = []
    (repo.root / "SPEC.md").write_text("contract-v1\n")
    state["spec"] = {
        "version": "SPEC-TEST",
        "authority": "state.spec",
        "source_ids": ["SRC-001"],
        "goal_ref": "discovery.expected_outcome",
        "scope_ref": "discovery.scope",
        "constraints": ["preserve behavior"],
        "exceptions": [],
        "conditions": [{"id": "SC-01", "metric_ids": ["MET-001"], "deliverables": ["app.txt"]}],
        "contracts": ["SPEC.md"],
        "open_items": [],
    }
    state["binding"] = {"receipt_paths": ["records/TASK-001/STATUS.md"]}
    state["changes"][0].update({"evidence_ids": [], "paths": [*state["changes"][0]["paths"], "SPEC.md", "records/TASK-001/STATUS.md"]})
    repo.bind_current_revision()
    return repo


def add_metric(repo: ScenarioRepository, metric_id: str, kind: str, status: str, *, bind: bool = True, **extra: Any) -> None:
    """Add a metric, bound to SC-01 by default; call before recording evidence because metrics enter the Spec digest."""

    repo.state["metrics"].append(
        {
            "id": metric_id,
            "main_task_id": "MT-001",
            "kind": kind,
            "name": f"{metric_id} check",
            "baseline": "measured before implementation",
            "target": "meets the agreed target",
            "method": "run the recorded check",
            "environment_data": "scenario repository",
            "evidence_ids": [],
            "status": status,
            "verification": "execution",
            **extra,
        }
    )
    repo.state["main_tasks"][0]["metric_ids"].append(metric_id)
    if bind:
        repo.state["spec"]["conditions"][0]["metric_ids"].append(metric_id)
    repo.write_state()


def record(
    repo: ScenarioRepository,
    evidence_id: str,
    metric_id: str,
    result: str,
    code: str,
    *,
    link: bool = True,
) -> dict[str, Any]:
    """Run `code` through record_execution.py and register it as execution evidence."""

    output = repo.records / "evidence" / f"{evidence_id.lower()}.json"
    subprocess.run(
        [
            sys.executable, str(RECORDER), "--output", str(output), "--repo", str(repo.root),
            "--state", str(repo.manifest), "--cwd", str(repo.root), "--source", "app.txt",
            "--", sys.executable, "-c", code,
        ],
        cwd=repo.root,
        capture_output=True,
        text=True,
    )
    item = {
        "id": evidence_id,
        "path": str(output.relative_to(repo.root)),
        "kind": "execution",
        "supports": [metric_id],
        "status": "current",
        "result": result,
        "observed_at": "2026-01-01T00:00:00Z",
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }
    repo.state["evidence"].append(item)
    if link:
        metric = next(item for item in repo.state["metrics"] if item["id"] == metric_id)
        metric["evidence_ids"].append(evidence_id)
        repo.state["changes"][0]["evidence_ids"].append(evidence_id)
        if metric_id == "MET-001":
            repo.state["implementation_tasks"][0]["evidence_ids"].append(evidence_id)
            repo.state["overall_acceptance"]["evidence_ids"].append(evidence_id)
    repo.bind_current_revision()
    return item


def validate(repo: ScenarioRepository, gate: str = "acceptance", *extra: str) -> tuple[int, dict[str, Any]]:
    process = subprocess.run(
        [sys.executable, str(VALIDATOR), str(repo.manifest), "--repo", str(repo.root), "--gate", gate, *extra],
        cwd=repo.root,
        capture_output=True,
        text=True,
    )
    return process.returncode, json.loads(process.stdout)


def codes(result: dict[str, Any], bucket: str = "errors") -> list[str]:
    return [issue["code"] for issue in result[bucket]]


class PreImplementationEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = prepare()
        # Product back at its baseline: the check must fail before implementation.
        (self.repo.root / "app.txt").write_text("baseline\n", encoding="utf-8")
        self.repo.bind_current_revision()
        self.pre = record(self.repo, "EVD-PRE", "MET-001", "failed", IMPLEMENTED_CHECK, link=False)
        (self.repo.root / "app.txt").write_text("implemented\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.repo.close()

    def test_pre_implementation_record_must_be_marked_stale_after_the_product_changes(self) -> None:
        self.repo.bind_current_revision()
        _, result = validate(self.repo, "record")
        self.assertIn("EXECUTION_REVISION_STALE", codes(result))

    def test_stale_pre_implementation_record_outside_evidence_ids_keeps_acceptance_open(self) -> None:
        self.pre.update({"status": "stale", "stale_reason": "pre-implementation baseline; product changed"})
        record(self.repo, "EVD-POST", "MET-001", "passed", IMPLEMENTED_CHECK)
        returncode, result = validate(self.repo)
        self.assertEqual(returncode, 0, result)
        self.assertEqual(result["spec_satisfaction"], "satisfied")

    def test_pre_implementation_record_listed_in_evidence_ids_blocks_acceptance(self) -> None:
        self.pre.update({"status": "stale", "stale_reason": "pre-implementation baseline; product changed"})
        record(self.repo, "EVD-POST", "MET-001", "passed", IMPLEMENTED_CHECK)
        self.repo.state["metrics"][0]["evidence_ids"].insert(0, "EVD-PRE")
        self.repo.write_state()
        _, result = validate(self.repo)
        self.assertIn("METRIC_EVIDENCE_NOT_CURRENT", codes(result))
        self.assertIn("METRIC_EVIDENCE_RESULT", codes(result))
        message = next(issue["message"] for issue in result["errors"] if issue["code"] == "METRIC_EVIDENCE_NOT_CURRENT")
        self.assertIn("out of evidence_ids", message)
        self.assertEqual(result["spec_satisfaction"], "not_assessed")


class SpecSatisfactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = prepare()

    def tearDown(self) -> None:
        self.repo.close()

    def defer_mandatory_metric(self, *, decided: bool = True, in_overall: bool = False) -> None:
        extra = {"decision_id": "DEC-001"} if decided else {}
        if decided:
            self.repo.state["decisions"] = [{"id": "DEC-001", "summary": "user accepts delivery before the benchmark host returns"}]
        add_metric(self.repo, "MET-PERF", "mandatory_gate", "deferred", **extra)
        if in_overall:
            self.repo.state["overall_acceptance"]["metric_ids"].append("MET-PERF")
        record(self.repo, "EVD-POST", "MET-001", "passed", IMPLEMENTED_CHECK)

    def test_all_condition_metrics_passed_is_satisfied_only_at_acceptance(self) -> None:
        record(self.repo, "EVD-POST", "MET-001", "passed", IMPLEMENTED_CHECK)
        returncode, result = validate(self.repo)
        self.assertEqual(returncode, 0, result)
        self.assertEqual((result["spec_satisfaction"], result["spec_unmet_conditions"]), ("satisfied", []))
        _, result = validate(self.repo, "record")
        self.assertEqual(result["spec_satisfaction"], "not_assessed")

    def test_decided_deferral_with_passing_overall_scenario_is_partial(self) -> None:
        self.defer_mandatory_metric()
        returncode, result = validate(self.repo)
        self.assertEqual(returncode, 0, result)
        self.assertEqual(result["spec_satisfaction"], "partial")
        self.assertEqual(result["spec_unmet_conditions"], [{"id": "SC-01", "metric_ids": ["MET-PERF"]}])
        self.assertIn("METRIC_DEFERRED", codes(result, "warnings"))

    def test_deferral_without_decision_is_not_assessed(self) -> None:
        self.defer_mandatory_metric(decided=False)
        returncode, result = validate(self.repo)
        self.assertEqual(returncode, 1)
        self.assertIn("DEFERRED_DECISION_MISSING", codes(result))
        self.assertEqual(result["spec_satisfaction"], "not_assessed")

    def test_overall_acceptance_cannot_pass_through_a_deferred_metric(self) -> None:
        self.defer_mandatory_metric(in_overall=True)
        returncode, result = validate(self.repo)
        self.assertEqual(returncode, 1)
        self.assertIn("OVERALL_METRIC_DEFERRED", codes(result))
        self.assertEqual(result["spec_satisfaction"], "not_assessed")

    def test_condition_bound_improvement_target_must_pass_even_with_a_decision(self) -> None:
        # An accepted miss is tolerated only for metrics outside Spec conditions;
        # inside a condition it leaves the Spec unmet and blocks 1.3 acceptance.
        self.repo.state["decisions"] = [{"id": "DEC-001", "summary": "user accepts the missed improvement target"}]
        add_metric(self.repo, "MET-IMP", "improvement_target", "failed", decision_id="DEC-001")
        record(self.repo, "EVD-POST", "MET-001", "passed", IMPLEMENTED_CHECK)
        record(self.repo, "EVD-IMP", "MET-IMP", "failed", "import sys; sys.exit(1)")
        returncode, result = validate(self.repo)
        self.assertEqual(returncode, 1)
        self.assertIn("SPEC_METRIC_EVIDENCE_MISSING", codes(result))
        self.assertEqual(result["spec_satisfaction"], "not_assessed")
        self.assertEqual(result["spec_unmet_conditions"], [{"id": "SC-01", "metric_ids": ["MET-IMP"]}])

    def test_unbound_improvement_target_may_miss_with_a_decision(self) -> None:
        self.repo.state["decisions"] = [{"id": "DEC-001", "summary": "user accepts the missed improvement target"}]
        add_metric(self.repo, "MET-IMP", "improvement_target", "failed", bind=False, decision_id="DEC-001")
        record(self.repo, "EVD-POST", "MET-001", "passed", IMPLEMENTED_CHECK)
        record(self.repo, "EVD-IMP", "MET-IMP", "failed", "import sys; sys.exit(1)")
        returncode, result = validate(self.repo)
        self.assertEqual(returncode, 0, result)
        self.assertEqual(result["spec_satisfaction"], "satisfied")


class ActionGateDeferralTests(unittest.TestCase):
    """The action gate may run before acceptance, so only deferral decisions of blocking metrics stop it."""

    def setUp(self) -> None:
        self.repo = ScenarioRepository()
        self.repo.state["authorization"]["migrate"] = {"status": "authorized", "source_id": "SRC-001", "scope": ["db:staging"]}
        self.repo.state["decisions"] = [{"id": "DEC-001", "summary": "user accepts verifying later"}]
        self.repo.write_state()

    def tearDown(self) -> None:
        self.repo.close()

    def validate_action(self) -> tuple[int, dict[str, Any]]:
        return validate(self.repo, "action", "--action", "migrate", "--target", "db:staging")

    def test_unverified_metrics_do_not_block_a_pre_acceptance_action(self) -> None:
        self.assertEqual(self.repo.state["metrics"][0]["status"], "undetermined")
        returncode, result = self.validate_action()
        self.assertEqual(returncode, 0, result)

    def test_deferred_blocking_metric_stops_the_action_but_improvement_target_does_not(self) -> None:
        self.repo.state["metrics"][1].update({"status": "deferred", "decision_id": "DEC-001"})
        self.repo.write_state()
        returncode, result = self.validate_action()
        self.assertEqual(returncode, 0, result)
        self.repo.state["metrics"][0].update({"status": "deferred", "decision_id": "DEC-001"})
        self.repo.write_state()
        _, result = self.validate_action()
        self.assertIn("METRIC_DEFERRED_BLOCKS", codes(result))


if __name__ == "__main__":
    unittest.main()
