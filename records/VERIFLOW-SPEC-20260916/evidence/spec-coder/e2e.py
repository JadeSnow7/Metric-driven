#!/usr/bin/env python3
"""Small local recorder/validator/action harness for the 1.3 binding."""
from __future__ import annotations
import json, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
VALIDATOR = ROOT / "skill/veriflow/scripts/validate_task.py"
RECORDER = ROOT / "skill/veriflow/scripts/record_execution.py"

def run(argv: list[str], cwd: Path, log_dir: Path, name: str) -> dict:
    started = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    p = subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ended = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    result = {"argv": argv, "cwd": str(cwd), "started_at": started, "ended_at": ended,
              "stdout": p.stdout, "stderr": p.stderr, "exit_code": p.returncode}
    destination = log_dir / f"{name}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result

def main() -> int:
    with tempfile.TemporaryDirectory(prefix="veriflow-1.3-e2e-") as tmp:
        repo = Path(tmp); logs = ROOT / "records/VERIFLOW-SPEC-20260916/evidence/spec-coder"
        run(["git", "init", "-q", "-b", "main"], repo, logs, "01-init")
        (repo / "probe.py").write_text("print('probe')\n", encoding="utf-8")
        run(["git", "add", "probe.py"], repo, logs, "02-add")
        run(["git", "-c", "user.name=Veriflow", "-c", "user.email=veriflow@example.invalid", "commit", "-qm", "baseline"], repo, logs, "03-baseline")
        (repo / "state.json").write_text(json.dumps({"schema_version": "1.3"}) + "\n", encoding="utf-8")
        # The full state is supplied by the caller's acceptance harness; these
        # immutable command logs demonstrate the reproducible local boundary.
        run([sys.executable, str(RECORDER), "--output", str(repo / "execution.json"), "--cwd", str(repo), "--", sys.executable, "probe.py"], repo, logs, "04-record")
        run([sys.executable, str(VALIDATOR), str(repo / "state.json"), "--repo", str(repo), "--gate", "record"], repo, logs, "05-validate")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
