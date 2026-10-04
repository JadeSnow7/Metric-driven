from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import supplemental_check as sc


class SupplementalTests(unittest.TestCase):
    def test_estimate_constants_and_tool_fields(self):
        arguments = {"中文": [1, True, False, None, {"数字": 2}]}
        expected_json = 2 + (2 + len("中文".encode()) + 1 + (2 + (8 + 4 + 5 + 4 + (2 + (2 + len("数字".encode()) + 1 + 8)) + 4)))
        message = {"role": "tool", "content": "来源", "tool_call_id": "非空", "tool_calls": [{"id": "i", "name": "n", "arguments": arguments}]}
        expected = 8 + len("tool".encode()) + len("来源".encode()) + len("非空".encode()) + 8 + 1 + 1 + expected_json
        self.assertEqual(sc.estimated_message(message), expected)
        self.assertEqual(sc.estimated_message({"role": "user", "content": "x", "tool_call_id": None}), 13)
        with self.assertRaises(ValueError):
            sc.estimated_message({"role": "tool", "content": "x", "toolCallId": "c", "tool_call_id": "c"})

    def test_real_wire_sample_is_171_and_changed_value_is_174(self):
        messages = [
            {"role": "system", "content": "规则甲"},
            {"role": "system", "content": "规则乙"},
            {"role": "user", "content": "字段是什么？"},
            {"role": "assistant", "content": "", "toolCalls": [{"id": "c", "name": "read", "arguments": {"path": "docs/source.md"}}]},
            {"role": "tool", "content": "[来源:doc-1]\n字段：值", "toolCallId": "c"},
        ]
        self.assertEqual(sc.estimated_units(messages), 171)
        messages[-1]["content"] = "[来源:doc-1]\n字段：新值"
        self.assertEqual(sc.estimated_units(messages), 174)

    def test_full_run_and_required_failures(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data = root / "data"
            self._make_data(data)
            run = root / "run.json"
            self._write_run(run, data)
            completed = self._invoke(run, data, 2400)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["checked_rows"], 16)

            cases = [
                ("estimate", lambda rows: rows[0].__setitem__("estimatedUnits", rows[0]["estimatedUnits"] + 1), "CHECK_ESTIMATE"),
                ("grounded", lambda rows: rows[0]["answer"]["claims"].__getitem__(0).__setitem__("value", "无依据"), "CHECK_CLAIM_GROUNDED"),
                ("quality", lambda rows: rows[0].__setitem__("quality", 0), "CHECK_QUALITY_EXACT"),
            ]
            for name, mutate, check_id in cases:
                case_run = root / f"{name}.json"
                self._write_run(case_run, data)
                record = json.loads(case_run.read_text())
                rows = json.loads(record["stdout"])["results"]
                mutate(rows)
                record["stdout"] = json.dumps({"unit": "estimated-bytes-v1", "serviceTokens": None, "results": rows}, ensure_ascii=False)
                case_run.write_text(json.dumps(record, ensure_ascii=False))
                result = self._invoke(case_run, data, 2400)
                self.assertNotEqual(result.returncode, 0, name)
                self.assertEqual(json.loads(result.stdout)["failed_checks"][0]["check_id"], check_id, name)

            changed = root / "changed.json"
            changed_data = root / "changed-data"
            self._make_data(changed_data, source_value="新值")
            self._write_run(changed, changed_data, source_value="新值", claim_value="新值", quality=1)
            result = self._invoke(changed, changed_data, 2400)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["failed_checks"][0]["check_id"], "CHECK_QUALITY_EXACT")

            stale = root / "stale.json"
            self._write_run(stale, changed_data, source_value="值", claim_value="值")
            result = self._invoke(stale, changed_data, 2400)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["failed_checks"][0]["check_id"], "CHECK_CLAIM_CURRENT_SOURCE")

            changed_ok = root / "changed-ok.json"
            self._write_run(changed_ok, changed_data, source_value="新值", claim_value="新值", quality=0)
            self.assertEqual(self._invoke(changed_ok, changed_data, 2400).returncode, 0)

            zero = root / "zero.json"
            self._write_run(zero, data, budget0=True)
            self.assertEqual(self._invoke(zero, data, 0).returncode, 0)

            failed = root / "failed.json"
            self._write_run(failed, data, exit_code=2)
            result = self._invoke(failed, data, 2400)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["failed_checks"][0]["check_id"], "CHECK_RUN_EXIT_CODE")

    def _invoke(self, run, data, budget):
        return subprocess.run([sys.executable, str(Path(__file__).parents[1] / "supplemental_check.py"), "--run", str(run), "--data", str(data), "--budget", str(budget)], text=True, capture_output=True)

    def _make_data(self, data, source_value="值"):
        (data / "docs").mkdir(parents=True)
        (data / "docs/source.md").write_text(f"字段：{source_value}\n", encoding="utf-8")
        tasks = [{"id": f"task-{i}", "question": "字段是什么？", "rules": [], "expectedFacts": [{"field": "字段", "value": "值", "source": "doc-1"}], "unknown": False} for i in range(1, 5)]
        (data / "tasks.json").write_text(json.dumps({"tasks": tasks}, ensure_ascii=False), encoding="utf-8")
        (data / "index.json").write_text(json.dumps({"documents": [{"id": "doc-1", "path": "docs/source.md"}]}, ensure_ascii=False), encoding="utf-8")

    def _write_run(self, path, data, source_value="值", claim_value=None, quality=1, budget0=False, exit_code=0):
        tasks = json.loads((data / "tasks.json").read_text())["tasks"]
        rows = []
        for task in tasks:
            for strategy in ("on-demand", "window", "summary", "retrieval"):
                if budget0:
                    rows.append({"taskId": task["id"], "strategy": strategy, "question": task["question"], "budget": 0, "status": "context_budget_exhausted", "messages": [], "estimatedUnits": 0, "selectedSources": [], "operations": [], "answer": None, "quality": None, "unsupportedClaims": [], "elapsedMs": 0, "serviceTokens": None, "modelCalls": 0, "callRecords": []})
                    continue
                messages = [{"role": "user", "content": task["question"], "toolCallId": None, "toolCalls": []}, {"role": "assistant", "content": "", "toolCalls": [{"id": "call-1", "name": "read", "arguments": {"path": "docs/source.md"}}]}, {"role": "tool", "content": f"[来源:doc-1]\n字段：{source_value}", "toolCallId": "call-1"}]
                rows.append({"taskId": task["id"], "strategy": strategy, "question": task["question"], "budget": 2400, "status": "completed", "messages": messages, "estimatedUnits": sc.estimated_units(messages), "selectedSources": [], "operations": [], "answer": {"rawAnswer": source_value, "claims": [{"field": "字段", "value": claim_value if claim_value is not None else source_value, "source": "doc-1"}], "insufficientEvidence": False}, "quality": quality, "unsupportedClaims": [], "elapsedMs": 0, "serviceTokens": None, "modelCalls": 1, "callRecords": []})
        record = {"exit_code": exit_code, "timed_out": False, "stdout": json.dumps({"unit": "estimated-bytes-v1", "serviceTokens": None, "results": rows}, ensure_ascii=False), "stderr": ""}
        path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
