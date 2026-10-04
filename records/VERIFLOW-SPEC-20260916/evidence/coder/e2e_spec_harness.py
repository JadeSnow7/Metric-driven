#!/usr/bin/env python3
"""Small offline recorder/validator/action-state smoke run for the parent review."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
VALIDATE = ROOT / "skill/veriflow/scripts/validate_task.py"
RECORD = ROOT / "skill/veriflow/scripts/record_execution.py"
TEMPLATE = ROOT / "skill/veriflow/assets/templates/task-state.example.json"


def run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False)
    print(json.dumps({"argv": argv, "cwd": str(cwd), "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr}, ensure_ascii=False))
    return result


with tempfile.TemporaryDirectory(prefix="veriflow-e2e-") as raw:
    repo = Path(raw)
    run(["git", "init", "-q"], repo)
    run(["git", "config", "user.email", "e2e@example.invalid"], repo)
    run(["git", "config", "user.name", "Veriflow E2E"], repo)
    (repo / "app.txt").write_text("base\n", encoding="utf-8")
    run(["git", "add", "app.txt"], repo)
    run(["git", "commit", "-qm", "baseline"], repo)
    base = run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    state = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    state["baseline"]["git_ref"] = base
    state["baseline"]["prepared_at"] = "2026-09-16T00:00:00Z"
    state["sources"][0]["reference"] = "e2e:harness"
    state["implementation_tasks"][0]["file_scope"] = ["app.txt"]
    manifest = repo / "records/TASK-001/task-state.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps(state, indent=2), encoding="utf-8")
    (repo / "app.txt").write_text("implemented\n", encoding="utf-8")
    output = manifest.parent / "evidence/run.json"
    result = run([sys.executable, str(RECORD), "--output", str(output), "--repo", str(repo), "--state", str(manifest), "--cwd", str(repo), "--source", "app.txt", "--", sys.executable, "-c", "print('e2e')"], repo)
    assert result.returncode == 0
    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["result"] == "passed" and record["revision"] == record["revision_after"]
    check = run([sys.executable, str(VALIDATE), str(manifest), "--repo", str(repo), "--gate", "record"], repo)
    assert check.returncode == 0
    print(json.dumps({"assertions": ["recorder_passed", "record_validation_passed", "no_external_service"], "ok": True}))
