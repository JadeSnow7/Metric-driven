"""(v3) Process observations from a `claude -p --output-format stream-json` transcript.

Usage: python3 -I analyze.py <duration|todo> <transcript.jsonl>

Also reads Claude Code subagent transcripts (subagents/agent-*.jsonl), which carry
the same message.content blocks but no final `result` event; for those, completion
and usage come from the operator's meta.json, and the hand-back text is captured.
Only tool calls recorded in the transcript count; the agent's own report is not used.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
PRODUCT = {"duration": re.compile(r"(^|/)duration\.py$"), "todo": re.compile(r"(^|/)todo/(?!.*test)[^ ]*\.(py|cfg)$")}
TEST_FILE = re.compile(r"(^|/)(tests/|test_)[^ ]*\.py$")
# v2: paths mentioned inside Bash commands are not end-anchored (v1 missed heredoc edits).
PRODUCT_IN_COMMAND = {"duration": re.compile(r"(?<![\w])duration\.py"),
                      "todo": re.compile(r"todo/(commands/\w+\.py|plugins\.cfg|cli\.py|store\.py|registry\.py|__main__\.py)")}
TEST_IN_COMMAND = re.compile(r"(tests/\w+\.py|test_\w+\.py)")
REDIRECT_TARGET = re.compile(r"(?<![0-9&])>{1,2}\s*([^\s&|;]+)")
PYTHON_WRITE = re.compile(r"sed -i|\btee\b|write_text|open\([^)]*['\"][wa]['\"]")
RUN = re.compile(r"unittest|pytest|-m todo|parse_duration|python3? [^|]*test")
RECORD = re.compile(r"(^|/)records/|task-state\.json|task-summary\.md|work-log\.md")


def events(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def analyze(task: str, path: Path) -> dict:
    steps: list[dict] = []
    result: dict = {}
    init: dict = {}
    skill_loaded = False
    reference_reads: list[str] = []
    handback = ""
    for event in events(path):
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init":
            init = event
        if kind == "result":
            result = event
        if kind == "assistant" and not init.get("model") and isinstance(event.get("message"), dict):
            init = {**init, "model": event["message"].get("model")}
        content = event.get("message", {}).get("content") if isinstance(event.get("message"), dict) else None
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            text = json.dumps(block, ensure_ascii=False)
            if "Base directory for this skill" in text or ("veriflow" in text.lower() and block.get("type") == "tool_use" and block.get("name") == "Skill"):
                skill_loaded = True
            if block.get("type") != "tool_use":
                continue
            name, data = block.get("name"), block.get("input") or {}
            if name == "SubagentHandback":
                handback = json.dumps(data, ensure_ascii=False)
                continue
            file_path = str(data.get("file_path", ""))
            command = str(data.get("command", ""))
            if name == "Read" and "/.claude/skills/veriflow/" in file_path:
                reference_reads.append(file_path.split("/.claude/skills/veriflow/")[-1])
            step = {"tool": name}
            if name in EDIT_TOOLS:
                step["edit"] = "product" if PRODUCT[task].search(file_path) else "test" if TEST_FILE.search(file_path) else "other"
                step["path"] = file_path
                step["record"] = bool(RECORD.search(file_path))
            elif name == "Bash":
                step["run"] = bool(RUN.search(command))
                # v3: when a command redirects into files, classify by those targets only;
                # heredoc bodies (e.g. test code) may mention product paths without writing them.
                file_targets = [t for t in REDIRECT_TARGET.findall(command) if PRODUCT_IN_COMMAND[task].search(t) or TEST_IN_COMMAND.search(t)]
                writes = bool(PYTHON_WRITE.search(command))
                if file_targets:
                    if any(PRODUCT_IN_COMMAND[task].search(t) for t in file_targets):
                        step["edit"] = "product"
                    else:
                        step["edit"] = "test"
                elif writes and PRODUCT_IN_COMMAND[task].search(command):
                    step["edit"] = "product"
                elif writes and TEST_IN_COMMAND.search(command):
                    step["edit"] = "test"
                step["bash_write"] = "edit" in step
                # A check run placed after the last heredoc terminator executes after the write.
                tail = command.rsplit("\nEOF", 1)[-1] if "<<" in command else command
                step["run_after_write"] = step["bash_write"] and bool(RUN.search(tail)) and tail != command
                step["record"] = bool(RECORD.search(command)) and bool(re.search(r"mkdir|>|touch|Write", command))
                step["command"] = command[:300]
            steps.append(step)

    def first(predicate) -> int | None:
        return next((index for index, step in enumerate(steps) if predicate(step)), None)

    product_edit = first(lambda s: s.get("edit") == "product")
    bash_write = first(lambda s: s.get("bash_write"))
    first_run = first(lambda s: s.get("run"))
    test_edit = first(lambda s: s.get("edit") == "test")
    check_before = (
        product_edit is not None and test_edit is not None and test_edit < product_edit
        and (steps[test_edit].get("run_after_write") or any(steps[i].get("run") for i in range(test_edit + 1, product_edit)))
    )
    usage = result.get("usage")
    skill_loaded = skill_loaded or "SKILL.md" in reference_reads
    return {
        "task": task,
        "transcript": str(path),
        "model": init.get("model"),
        "skill_loaded": skill_loaded,
        "skill_reference_reads": reference_reads,
        "completed": (result.get("subtype") == "success" and not result.get("is_error")) if result else None,
        "result_subtype": result.get("subtype"),
        "tool_calls": len(steps),
        "first_product_edit_step": product_edit,
        "bash_product_or_test_write_step": bash_write,
        "first_run_step": first_run,
        "P1_ran_before_product_edit": first_run is not None and (product_edit is None or first_run < product_edit),
        "P2_wrote_and_ran_check_before_product_edit": check_before,
        "P3_record_artifacts": any(step.get("record") for step in steps),
        "num_turns": result.get("num_turns"),
        "duration_ms": result.get("duration_ms"),
        "total_cost_usd": result.get("total_cost_usd"),
        "usage": usage,
        "final_text": (result.get("result") or handback)[:6000],
    }


def main() -> int:
    print(json.dumps(analyze(sys.argv[1], Path(sys.argv[2])), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
