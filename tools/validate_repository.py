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
    "skill/veriflow/SKILL.md",
    "skill/veriflow/agents/openai.yaml",
    "skill/veriflow/references/workflow.md",
    "skill/veriflow/references/records.md",
    "skill/veriflow/references/metrics-and-evidence.md",
    "skill/veriflow/references/delegation-and-handoffs.md",
    "skill/veriflow/references/examples.md",
    "skill/veriflow/assets/templates/task-state.example.json",
    "skill/veriflow/assets/templates/task-summary.md",
    "skill/veriflow/assets/templates/work-log.md",
    "skill/veriflow/assets/templates/handoff.md",
    "skill/veriflow/assets/templates/writing-handoff.md",
    "skill/veriflow/scripts/validate_task.py",
    "skill/veriflow/tests/test_scenarios.py",
    "tools/validate_repository.py",
)
TASK_VALIDATOR = "skill/veriflow/scripts/validate_task.py"

MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
UNFINISHED = re.compile(r"\[(?:TODO|PLACEHOLDER):|Briefly describe|Add the task-specific", re.IGNORECASE)

ARCHIVED_DOCUMENT_PREFIXES = (
    # Preserved chapter/product captures from the REIN-CH05-16 evidence set.
    ("records", "REIN-CH05-16", "production", "ch06", "final-evidence", "body-evidence", "body-v1-preserved"),
    ("records", "REIN-CH05-16", "production", "ch06", "final-evidence", "body-evidence", "body-v2-preserved"),
    ("records", "REIN-CH05-16", "production", "ch07", "evidence", "rein-ch07-rust-v1-preserved"),
    ("records", "REIN-CH05-16", "production", "support-stage1-a2", "evidence", "v4", "before"),
    ("records", "REIN-CH05-16", "production", "support-stage1-a2", "evidence", "v5", "before"),
    # Sealed/preparation book copies are captured products, not maintained docs.
    ("records", "REIN-CH08-EDD-20260915", "preparation", "book-initial"),
    ("records", "REIN-CH08-EDD-20260915", "preparation", "common", "book"),
    ("records", "REIN-CH08-EDD-20260915", "production", "final-book", "book"),
    ("records", "REIN-CH08-EDD-20260915", "production", "final-book-full-source", "book"),
)


def visible_markdown(text: str) -> str:
    """Remove code examples before checking links in maintained prose."""
    text = re.sub(r"```.*?```|~~~.*?~~~", "", text, flags=re.DOTALL)
    return re.sub(r"`[^`]*`", "", text)


def is_maintained_document(root: Path, path: Path) -> bool:
    """Return whether local-link checks apply to this repository document.

    Fixture workspaces, captured inputs, and chapter-16 specs are test data;
    later experiment/snapshot product copies are likewise validated by their
    owning experiment.  Preparation transcripts and handoff archives are
    generated evidence carriers, not maintained repository documentation.
    """
    relative = path.resolve().relative_to(root.resolve())
    parts = relative.parts
    if any(parts[: len(prefix)] == prefix for prefix in ARCHIVED_DOCUMENT_PREFIXES):
        return False
    if (
        len(parts) >= 6
        and parts[:3] == ("records", "REIN-CH08-EDD-20260915", "formal")
        and parts[3] == "seals"
        and parts[5] == "work"
    ):
        return False
    if parts[:3] == ("records", "REIN-CH05-16", "work"):
        return False
    if parts[:4] == ("records", "REIN-CH05-16", "evidence", "inputs"):
        return False
    if parts[:5] == ("records", "REIN-CH05-16", "evidence", "specs", "chapter-16"):
        return False
    if parts[:3] in {
        ("records", "REIN-CH05-16", "experiments"),
        ("records", "REIN-CH05-16", "snapshots"),
    }:
        return False
    if parts[:4] == ("records", "REIN-CH05-16", "evidence", "preparation-review"):
        return False
    if parts[:3] == ("records", "REIN-CH05-16", "handoffs"):
        return False
    return True


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
        if not is_maintained_document(root, markdown):
            continue
        text = markdown.read_text(encoding="utf-8")
        visible = visible_markdown(text)
        if UNFINISHED.search(visible):
            errors.append(f"unfinished scaffold marker: {markdown.relative_to(root)}")
        for match in MARKDOWN_LINK.finditer(visible):
            target = match.group(1).strip().strip("<>").split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "sandbox:")):
                continue
            destination = (markdown.parent / target).resolve()
            if not destination.exists():
                errors.append(
                    f"broken local link in {markdown.relative_to(root)}: {match.group(1)}"
                )

    template = root / "skill/veriflow/assets/templates/task-state.example.json"
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

    openai_yaml = root / "skill/veriflow/agents/openai.yaml"
    if openai_yaml.is_file():
        text = openai_yaml.read_text(encoding="utf-8")
        if "$veriflow" not in text:
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
