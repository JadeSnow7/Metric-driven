from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/authorization_snapshot.py"
spec = importlib.util.spec_from_file_location("authorization_snapshot", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def state() -> dict:
    return {
        "authorization": {"push": {"status": "authorized", "source_id": "SRC-1", "scope": ["origin/main"]}},
        "sources": [{"id": "SRC-1", "kind": "user_requirement", "adoption": "accepted", "reference": "test:authorization", "summary": "push this revision"}],
    }


class AuthorizationSnapshotTests(unittest.TestCase):
    def test_capture_and_historical_audit_survive_current_revocation(self):
        original = state()
        snapshot = module.capture_snapshot(original, "push", "origin/main", "rev-1")
        record = {"authorization_action": "push", "target": "origin/main", "revision": "rev-1"}
        original["authorization"]["push"]["status"] = "not_authorized"
        original["sources"][0]["adoption"] = "superseded"
        self.assertEqual(module.audit_snapshot(snapshot, record), [])

    def test_capture_rejects_unauthorized_agent_source_and_scope(self):
        for mutate, target in ((lambda s: s["authorization"]["push"].update(status="not_authorized"), "origin/main"),
                               (lambda s: s["sources"][0].update(kind="agent_inference"), "origin/main"),
                               (lambda s: None, "other")):
            candidate = state(); mutate(candidate)
            with self.assertRaises(ValueError): module.capture_snapshot(candidate, "push", target, "rev-1")

    def test_missing_and_tampering_are_distinguished(self):
        record = {"authorization_action": "push", "target": "origin/main", "revision": "rev-1"}
        self.assertEqual(module.audit_snapshot(None, record)[0]["code"], "AUTH_SNAPSHOT_UNKNOWN")
        snapshot = module.capture_snapshot(state(), "push", "origin/main", "rev-1")
        for field, value in (("target", "other"), ("revision", "rev-2"), ("source_id", "SRC-x")):
            tampered = copy.deepcopy(snapshot); tampered[field] = value
            self.assertTrue(any(item["code"] == "AUTH_SNAPSHOT_HASH" for item in module.audit_snapshot(tampered, record)))

    def test_audit_malformed_json_never_raises_and_captured_scope_is_authoritative(self):
        record = {"authorization_action": "push", "target": "origin/allowed", "revision": "rev-1"}
        malformed = {"schema_version": 1, "captured_at": "2026-01-01T00:00:00Z", "action": "push", "target": "origin/allowed", "revision": "rev-1", "authorization": {"status": "authorized", "source_id": "SRC-1", "scope": ["origin/allowed"]}, "source": "bad", "source_id": "SRC-1", "scope": [], "source_content": "bad", "content_sha256": "0" * 64}
        self.assertTrue(module.audit_snapshot(malformed, record))
        snapshot = module.capture_snapshot(state(), "push", "origin/main", "rev-1")
        snapshot["scope"] = []
        snapshot["target"] = "other"
        snapshot["content_sha256"] = module._digest(snapshot)
        self.assertTrue(any(item["code"] == "AUTH_SNAPSHOT_SCOPE" for item in module.audit_snapshot(snapshot, {**record, "target": "other"})))

    def test_capture_rejects_empty_fields_and_audit_rejects_real_invalid_time(self):
        for field in ("target", "revision"):
            candidate = state()
            with self.assertRaises(ValueError): module.capture_snapshot(candidate, "push", "" if field == "target" else "origin/main", "" if field == "revision" else "rev-1")
        candidate = state(); candidate["sources"][0]["reference"] = ""
        with self.assertRaises(ValueError): module.capture_snapshot(candidate, "push", "origin/main", "rev-1")
        snapshot = module.capture_snapshot(state(), "push", "origin/main", "rev-1")
        snapshot["captured_at"] = "2026-99-99T99:99:99Z"; snapshot["content_sha256"] = module._digest(snapshot)
        self.assertTrue(any(item["code"] == "AUTH_SNAPSHOT_TIME" for item in module.audit_snapshot(snapshot, {"authorization_action": "push", "target": "origin/main", "revision": "rev-1"})))

    def test_boolean_schema_and_nan_are_issues(self):
        snapshot = module.capture_snapshot(state(), "push", "origin/main", "rev-1")
        snapshot["schema_version"] = True
        self.assertTrue(any(item["code"] == "AUTH_SNAPSHOT_SCHEMA" for item in module.audit_snapshot(snapshot, {"authorization_action": "push", "target": "origin/main", "revision": "rev-1"})))
        snapshot = module.capture_snapshot(state(), "push", "origin/main", "rev-1"); snapshot["source"]["bad"] = float("nan")
        self.assertTrue(module.audit_snapshot(snapshot, {"authorization_action": "push", "target": "origin/main", "revision": "rev-1"}))

    def test_unhashable_source_kind_and_duplicate_scope_are_issues(self):
        record = {"authorization_action": "push", "target": "origin/main", "revision": "rev-1"}
        for kind in ([], {}):
            candidate = state(); candidate["sources"][0]["kind"] = kind
            with self.assertRaises(ValueError): module.capture_snapshot(candidate, "push", "origin/main", "rev-1")
            snapshot = module.capture_snapshot(state(), "push", "origin/main", "rev-1")
            snapshot["source"]["kind"] = kind
            self.assertTrue(module.audit_snapshot(snapshot, record))
        snapshot = module.capture_snapshot(state(), "push", "origin/main", "rev-1")
        snapshot["scope"] = []
        self.assertTrue(any(item["code"] == "AUTH_SNAPSHOT_SCOPE_COPY" for item in module.audit_snapshot(snapshot, record)))

    def test_audit_rejects_empty_action_target_and_revision(self):
        snapshot = module.capture_snapshot(state(), "push", "origin/main", "rev-1")
        for field in ("target", "revision"):
            record = {"authorization_action": "push", "target": "", "revision": "rev-1"}
            if field == "revision": record = {"authorization_action": "push", "target": "origin/main", "revision": ""}
            tampered = {**snapshot, field: ""}
            self.assertTrue(module.audit_snapshot(tampered, record))

    def test_cli_outputs_snapshot_and_does_not_execute_action(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"; path.write_text(json.dumps(state()), encoding="utf-8")
            result = subprocess.run([sys.executable, str(MODULE_PATH), "--state", str(path), "--action", "push", "--target", "origin/main", "--revision", "rev-1"], capture_output=True, text=True, env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1"})
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["action"], "push")


if __name__ == "__main__":
    unittest.main()
