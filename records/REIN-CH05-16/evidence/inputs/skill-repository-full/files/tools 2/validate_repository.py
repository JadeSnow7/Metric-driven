#!/usr/bin/env python3
"""Validate this repository's maintained structure and local references."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType


REQUIRED = (
    "README.md",
    "LICENSE",
    ".github/workflows/ci.yml",
    "skill/evidence-driven-development/SKILL.md",
    "skill/evidence-driven-development/agents/openai.yaml",
    "skill/evidence-driven-development/references/workflow.md",
    "skill/evidence-driven-development/references/records.md",
    "skill/evidence-driven-development/references/metrics-and-evidence.md",
    "skill/evidence-driven-development/references/delegation-and-handoffs.md",
    "skill/evidence-driven-development/references/examples.md",
    "skill/evidence-driven-development/assets/templates/task-state.example.json",
    "skill/evidence-driven-development/assets/templates/task-summary.md",
    "skill/evidence-driven-development/assets/templates/work-log.md",
    "skill/evidence-driven-development/assets/templates/handoff.md",
    "skill/evidence-driven-development/assets/templates/writing-handoff.md",
    "skill/evidence-driven-development/scripts/validate_task.py",
    "skill/evidence-driven-development/tests/test_scenarios.py",
    "tools/validate_repository.py",
)
TASK_VALIDATOR = "skill/evidence-driven-development/scripts/validate_task.py"

MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
UNFINISHED = re.compile(r"\[(?:TODO|PLACEHOLDER):|Briefly describe|Add the task-specific", re.IGNORECASE)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_task_validator(root: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("validate_task", root / TASK_VALIDATOR)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {TASK_VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True  # keep the shipped skill directory free of __pycache__
    spec.loader.exec_module(module)
    return module


def main() -> int:
    root = repository_root()
    errors: list[str] = []

    for relative in REQUIRED:
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")

    for markdown in sorted(root.rglob("*.md")):
        if ".git" in markdown.parts:
            continue
        text = markdown.read_text(encoding="utf-8")
        if UNFINISHED.search(text):
            errors.append(f"unfinished scaffold marker: {markdown.relative_to(root)}")
        for match in MARKDOWN_LINK.finditer(text):
            target = match.group(1).strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "sandbox:")):
                continue
            destination = (markdown.parent / target).resolve()
            if not destination.exists():
                errors.append(
                    f"broken local link in {markdown.relative_to(root)}: {match.group(1)}"
                )

    template = root / "skill/evidence-driven-development/assets/templates/task-state.example.json"
    if template.is_file() and (root / TASK_VALIDATOR).is_file():
        validator = load_task_validator(root)
        try:
            data = json.loads(template.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"task-state template is invalid JSON: {exc}")
        else:
            missing = sorted(set(validator.ROOT_FIELDS) - set(data))
            if missing:
                errors.append(f"task-state template missing keys: {', '.join(missing)}")
            if data.get("schema_version") != validator.SCHEMA_VERSION:
                errors.append(
                    f"task-state template schema_version must be {validator.SCHEMA_VERSION!r}"
                )

    openai_yaml = root / "skill/evidence-driven-development/agents/openai.yaml"
    if openai_yaml.is_file():
        text = openai_yaml.read_text(encoding="utf-8")
        if "$evidence-driven-development" not in text:
            errors.append("agents/openai.yaml default_prompt must name the skill")

    if errors:
        print("repository validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"repository validation passed ({len(REQUIRED)} required files, local links checked)")
    print("note: this proves repository consistency, not workflow behavior or delivery authorization")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
