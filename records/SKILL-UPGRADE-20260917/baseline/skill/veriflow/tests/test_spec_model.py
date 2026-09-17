from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_model():
    path = ROOT / "scripts/spec_contract.py"
    spec = importlib.util.spec_from_file_location("spec_contract_model", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class SpecModelTests(unittest.TestCase):
    def setUp(self):
        self.model = load_model()
        self.state = json.loads((ROOT / "assets/templates/task-state.example.json").read_text())

    def test_normative_and_nested_result_changes_bind_runtime_changes_do_not(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.state["binding"]["receipt_paths"] = ["records/run.json"]
            first = self.model.spec_digest(self.state, repo)
            self.state["metrics"][0]["result"] = {"value": 1}
            self.assertNotEqual(first, self.model.spec_digest(self.state, repo))
            second = self.model.spec_digest(self.state, repo)
            self.state["metrics"][0]["status"] = "passed"
            self.state["metrics"][0]["evidence_ids"] = ["EVD-1"]
            self.assertEqual(second, self.model.spec_digest(self.state, repo))
            self.state["binding"]["receipt_paths"] = ["records/other.json"]
            self.assertNotEqual(second, self.model.spec_digest(self.state, repo))

    def test_canonical_paths_and_symlink_parent_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            for value in ("./a", "a//b", "a/"):
                self.state["spec"]["conditions"][0]["deliverables"] = [value]
                self.assertTrue(self.model.validate_spec(self.state, repo))
            (repo / "real").mkdir()
            (repo / "alias").symlink_to(repo / "real", target_is_directory=True)
            self.state["spec"]["conditions"][0]["deliverables"] = ["alias/file.md"]
            self.assertTrue(self.model.validate_spec(self.state, repo))

    def test_foreign_prefix_conflicts_and_contract_deliverable_overlap(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            contract = repo / "docs/api.json"
            contract.parent.mkdir()
            contract.write_text("{}")
            self.state["spec"]["contracts"] = ["docs/api.json"]
            self.state["spec"]["conditions"][0]["deliverables"] = ["docs/api.json"]
            self.state["baseline"]["foreign_paths"] = ["docs"]
            codes = {item["code"] for item in self.model.validate_spec(self.state, repo)}
            self.assertIn("SPEC_PATH_CONFLICT", codes)
            self.state["baseline"]["foreign_paths"] = []
            self.assertNotIn("SPEC_PATH_CONFLICT", {item["code"] for item in self.model.validate_spec(self.state, repo)})

    def test_authority_and_each_condition_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            authority = repo / "SPEC.md"
            authority.write_text("spec")
            self.state["spec"]["authority"] = "SPEC.md"
            self.assertIn("SPEC_AUTHORITY", {item["code"] for item in self.model.validate_spec(self.state, repo)})
            self.state["spec"]["contracts"] = ["SPEC.md"]
            self.state["spec"]["conditions"].append({"id": "SC-2", "metric_ids": ["MET-002"], "deliverables": ["b.md"]})
            self.assertIn("SPEC_METRIC_BINDING", {item["code"] for item in self.model.validate_spec(self.state, repo)})

    def test_bad_refs_and_open_items_are_reported(self):
        self.state["spec"]["goal_ref"] = "discovery.nope"
        self.state["spec"]["open_items"] = [{"question": "pending"}]
        codes = {item["code"] for item in self.model.validate_spec(self.state, Path(tempfile.mkdtemp()))}
        self.assertIn("SPEC_REFERENCE", codes)
        self.assertIn("SPEC_OPEN_ITEMS_PENDING", codes)


if __name__ == "__main__":
    unittest.main()
