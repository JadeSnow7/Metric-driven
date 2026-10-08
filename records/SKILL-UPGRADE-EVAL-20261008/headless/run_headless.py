"""Round 2: run one cell with headless `claude -p` and native skill discovery.

    python3 -I run_headless.py <run_id> <duration|todo> <A|B> [--prompt TEXT] [--max-turns N] [--out-root DIR]

Reuses the fixture and skill installation from ../harness/run.py. The raw
stream-json transcript stays outside the repository (it carries session and
account metadata); the record keeps a redacted transcript, the grading and the
result fields reported by the CLI.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parent
sys.path.insert(0, str(EXPERIMENT / "harness"))
import run as round1  # noqa: E402  (fixture + skill setup shared with round 1)

WORK = round1.WORK.parent / "eval-headless"
MODEL = "claude-sonnet-5-5"
TIMEOUT_SECONDS = 20 * 60
# The desktop session exports these for itself; they would override the CLI's own login.
DROPPED_ENV = ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "ANTHROPIC_API_KEY")


def prepare(run_id: str, task: str, arm: str) -> Path:
    ws = WORK / run_id / "ws"
    if ws.exists():
        raise SystemExit(f"{run_id} already exists; runs are never overwritten")
    shutil.copytree(EXPERIMENT / "fixtures" / task, ws)
    round1.install_skill(round1.ARMS[arm], ws / ".claude/skills/veriflow")
    round1.git(ws, "init", "-q", "-b", "main")
    (ws / ".git/info/exclude").write_text(".claude/\n__pycache__/\n", encoding="utf-8")
    round1.git(ws, *round1.FIXTURE_IDENTITY, "add", "-A")
    round1.git(ws, *round1.FIXTURE_IDENTITY, "commit", "-q", "--no-verify", "-m", "fixture")
    return ws


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    parser.add_argument("task", choices=["duration", "todo"])
    parser.add_argument("arm", choices=sorted(round1.ARMS))
    parser.add_argument("--prompt")
    parser.add_argument("--max-turns", type=int, default=80)
    parser.add_argument("--out-root", default=str(HERE / "runs"))
    args = parser.parse_args()

    out = Path(args.out_root) / args.run_id
    if out.exists():
        raise SystemExit(f"{out} already exists; runs are never overwritten")
    ws = prepare(args.run_id, args.task, args.arm)
    out.mkdir(parents=True)
    raw = WORK / args.run_id / "transcript.raw.jsonl"
    prompt = args.prompt or "/veriflow " + round1.PROMPTS[args.task]
    argv = [
        "claude", "-p", prompt, "--model", MODEL, "--output-format", "stream-json", "--verbose",
        "--max-turns", str(args.max_turns), "--permission-mode", "acceptEdits",
        "--allowedTools", "Read", "Edit", "Write", "Glob", "Grep", "Bash", "Skill",
        "--disallowedTools", "WebFetch", "WebSearch", "Agent", "Task",
        "--setting-sources", "project,local",
    ]
    env = {key: value for key, value in os.environ.items() if key not in DROPPED_ENV}
    meta = {"run_id": args.run_id, "task": args.task, "arm": args.arm, "skill_revision": round1.ARMS[args.arm],
            "mode": "headless", "argv": argv, "dropped_env": list(DROPPED_ENV), "workspace": str(ws),
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    started = time.monotonic()
    with raw.open("w", encoding="utf-8") as stdout, (WORK / args.run_id / "stderr.txt").open("w", encoding="utf-8") as stderr:
        try:
            process = subprocess.run(argv, cwd=ws, env=env, stdout=stdout, stderr=stderr,
                                     stdin=subprocess.DEVNULL, timeout=TIMEOUT_SECONDS)
            meta.update(exit_code=process.returncode, timed_out=False)
        except subprocess.TimeoutExpired:
            meta.update(exit_code=None, timed_out=True)
    meta["wall_seconds"] = round(time.monotonic() - started, 1)

    result = {}
    for line in raw.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "result":
            result = event
    meta["result"] = {key: result.get(key) for key in
                      ("subtype", "is_error", "num_turns", "duration_ms", "duration_api_ms", "total_cost_usd", "usage", "terminal_reason")}
    meta["result"]["model_usage_models"] = sorted((result.get("modelUsage") or {}).keys())

    round1.git(ws, "add", "-A")
    (out / "diff.patch").write_text(round1.git(ws, "diff", "--cached", "--stat") + "\n" + round1.git(ws, "diff", "--cached"), encoding="utf-8")
    shutil.copytree(ws, out / "workspace", ignore=shutil.ignore_patterns(".git", ".claude", "__pycache__"))
    subprocess.run([sys.executable, "-I", str(EXPERIMENT / "harness/redact.py"), str(raw), str(out / "transcript.redacted.jsonl")], check=True)
    for name, script, target in (("grade.json", "grade.py", ws), ("process.json", "analyze.py", raw)):
        graded = subprocess.run([sys.executable, "-I", str(EXPERIMENT / "grader" / script), args.task, str(target)],
                                text=True, capture_output=True)
        (out / name).write_text(graded.stdout or json.dumps({"error": graded.stderr}), encoding="utf-8")
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run_id": args.run_id, "exit_code": meta["exit_code"], "timed_out": meta["timed_out"],
                      "wall_seconds": meta["wall_seconds"], "cost": meta["result"]["total_cost_usd"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
