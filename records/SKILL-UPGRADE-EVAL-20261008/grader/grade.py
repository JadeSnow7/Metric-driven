"""Hidden product checks for the skill-upgrade experiment.

Usage: python3 -I grade.py <duration|todo> <workspace>

The workspace is copied to a temporary directory first, so grading never
changes run artifacts. Prints one JSON object with a pass/fail per check.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TIMEOUT = 60


def run(argv: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv, cwd=cwd, env={**os.environ, **(env or {})}, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=TIMEOUT,
    )


def probe(cwd: Path, code: str) -> subprocess.CompletedProcess[str]:
    return run([sys.executable, "-c", code], cwd)


def grade_duration(root: Path) -> dict[str, bool]:
    def value(text: str) -> str:
        result = probe(root, f"from duration import parse_duration; print(parse_duration({text!r}))")
        return result.stdout.strip() if result.returncode == 0 else "error"

    def rejects(text: str) -> bool:
        code = (
            "from duration import parse_duration\n"
            f"try:\n    parse_duration({text!r})\nexcept ValueError:\n    raise SystemExit(0)\nraise SystemExit(1)"
        )
        return probe(root, code).returncode == 0

    return {
        "Q1_target_case": value("1m30s") == "90",
        "Q2_three_units": value("1h1m1s") == "3661",
        "Q3_single_units": [value(t) for t in ("2h", "45s", "10m")] == ["7200", "45", "600"],
        "Q4_invalid_still_rejected": all(rejects(t) for t in ("", "abc", "5x", "1h30", "1h 30m", "m")),
        "Q5_suite_passes": run([sys.executable, "-m", "unittest"], root).returncode == 0,
    }


def grade_todo(root: Path) -> dict[str, bool]:
    work = Path(tempfile.mkdtemp(prefix="todo-grade-data-"))
    data = work / "todo.json"
    items = [
        {"title": "Buy milk, eggs", "done": False},
        {"title": 'Say "hi" to Ana', "done": True},
        {"title": "plain", "done": False},
    ]
    data.write_text(json.dumps(items), encoding="utf-8")
    env = {"TODO_FILE": str(data)}
    out = work / "out.csv"
    exported = run([sys.executable, "-m", "todo", "export", str(out)], root, env)
    rows: list[list[str]] = []
    if out.is_file():
        with out.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
    header_ok = bool(rows) and [cell.strip().lower() for cell in rows[0]] == ["title", "done"]
    body = rows[1:] if header_ok else []
    done_values = [row[1].strip().lower() for row in body if len(row) == 2]
    truthy, falsy = {"true", "1", "yes", "x"}, {"false", "0", "no", ""}
    exported_ok = exported.returncode == 0 and out.is_file()
    synced = run([sys.executable, "-m", "todo", "sync"], root, env)
    added = run([sys.executable, "-m", "todo", "add", "new", "item"], root, env)
    listed = run([sys.executable, "-m", "todo", "list"], root, env)
    shutil.rmtree(work, ignore_errors=True)
    return {
        "Q1_cli_export_wired": exported_ok,
        "Q2_csv_round_trip": header_ok and [row[0] for row in body if row] == [item["title"] for item in items],
        "Q3_done_column": len(done_values) == 3
        and done_values[1] in truthy and done_values[0] in falsy and done_values[2] in falsy,
        "Q4_sync_preserved": (root / "todo/commands/sync.py").is_file() and synced.returncode == 0,
        "Q5_existing_commands_and_suite": added.returncode == 0 and "new item" in listed.stdout
        and run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], root).returncode == 0,
    }


def main() -> int:
    task, workspace = sys.argv[1], Path(sys.argv[2]).resolve()
    with tempfile.TemporaryDirectory(prefix=f"grade-{task}-") as temporary:
        root = Path(temporary) / "ws"
        shutil.copytree(workspace, root, ignore=shutil.ignore_patterns(".git", ".claude", "__pycache__"))
        checks = grade_duration(root) if task == "duration" else grade_todo(root)
    print(json.dumps({"task": task, "workspace": str(workspace), "checks": checks, "passed": sum(checks.values()), "total": len(checks)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
