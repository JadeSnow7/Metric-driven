"""Prepare and finalize one experiment cell.

    python3 -I run.py prepare <run_id> <duration|todo> <A|B>   # fresh fixture + skill copy, prints the agent prompt
    python3 -I run.py finalize <run_id> <agent_id> <usage-json>  # diff, workspace snapshot, transcript, grading

The agent itself is a Claude Code subagent (model: sonnet) launched by the
experiment operator with the printed prompt; see PLAN.md for why headless
`claude -p` was not used.
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

EXPERIMENT = Path(__file__).resolve().parents[1]
REPO = EXPERIMENT.parents[1]
WORK = Path("/private/tmp/claude-501/-Users-huaodong-workspace-Veriflow/55a80e45-cbb6-41ae-9888-8b9c8170841d/scratchpad/eval")
TRANSCRIPTS = Path.home() / ".claude/projects/-Users-huaodong-workspace-Veriflow/55a80e45-cbb6-41ae-9888-8b9c8170841d/subagents"
ARMS = json.loads((EXPERIMENT / "harness/arms.json").read_text(encoding="utf-8"))
PROMPTS = json.loads((EXPERIMENT / "harness/prompts.json").read_text(encoding="utf-8"))
AGENT_PROMPT = (EXPERIMENT / "harness/agent-prompt.txt").read_text(encoding="utf-8")
FIXTURE_IDENTITY = ("-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false")


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True).stdout


def install_skill(revision: str, target: Path) -> None:
    archive = subprocess.run(["git", "archive", revision, "skill/veriflow"], cwd=REPO, check=True, capture_output=True).stdout
    staging = target.parent / "_extract"
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        bundle.extractall(staging, filter="data")
    shutil.move(str(staging / "skill/veriflow"), target)
    shutil.rmtree(staging)


def prepare(run_id: str, task: str, arm: str) -> None:
    out, ws = EXPERIMENT / "runs" / run_id, WORK / run_id / "ws"
    if out.exists() or ws.exists():
        raise SystemExit(f"{run_id} already exists; runs are never overwritten")
    out.mkdir(parents=True)
    shutil.copytree(EXPERIMENT / "fixtures" / task, ws)
    install_skill(ARMS[arm], ws / ".claude/skills/veriflow")
    git(ws, "init", "-q", "-b", "main")
    (ws / ".git/info/exclude").write_text(".claude/\n__pycache__/\n", encoding="utf-8")
    git(ws, *FIXTURE_IDENTITY, "add", "-A")
    git(ws, *FIXTURE_IDENTITY, "commit", "-q", "--no-verify", "-m", "fixture")
    prompt = AGENT_PROMPT.replace("{WS}", str(ws)).replace("{REQUEST}", PROMPTS[task])
    meta = {"run_id": run_id, "task": task, "arm": arm, "skill_revision": ARMS[arm], "workspace": str(ws),
            "prepared_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "prompt": prompt}
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(prompt)


def finalize(run_id: str, agent_id: str, usage: str) -> None:
    out = EXPERIMENT / "runs" / run_id
    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    ws = Path(meta["workspace"])
    git(ws, "add", "-A")
    (out / "diff.patch").write_text(git(ws, "diff", "--cached", "--stat") + "\n" + git(ws, "diff", "--cached"), encoding="utf-8")
    shutil.copytree(ws, out / "workspace", ignore=shutil.ignore_patterns(".git", ".claude", "__pycache__"))
    shutil.copy(TRANSCRIPTS / f"agent-{agent_id}.jsonl", out / "transcript.jsonl")
    meta.update({"agent_id": agent_id, "usage_reported": json.loads(usage), "finalized_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, script, target in (("grade.json", "grade.py", ws), ("process.json", "analyze.py", out / "transcript.jsonl")):
        result = subprocess.run([sys.executable, "-I", str(EXPERIMENT / "grader" / script), meta["task"], str(target)],
                                text=True, capture_output=True)
        (out / name).write_text(result.stdout or json.dumps({"error": result.stderr}), encoding="utf-8")
    print((out / "grade.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    command, *rest = sys.argv[1:]
    {"prepare": prepare, "finalize": finalize}[command](*rest)
