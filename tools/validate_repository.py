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
    "skill/veriflow/agents/claude-code/veriflow-coder.md",
    "skill/veriflow/agents/claude-code/veriflow-reviewer.md",
    "skill/veriflow/references/claude-code.md",
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
    "skill/veriflow/scripts/record_execution.py",
    "skill/veriflow/scripts/integrate_boundary.py",
    "skill/veriflow/tests/test_scenarios.py",
    "skill/veriflow/tests/test_tools.py",
    "tools/validate_repository.py",
    "claude-code/.claude-plugin/plugin.json",
)
TASK_VALIDATOR = "skill/veriflow/scripts/validate_task.py"
SKILL_DIR = "skill/veriflow"
CLAUDE_AGENT_DIR = "skill/veriflow/agents/claude-code"
CLAUDE_PLUGIN_DIR = "claude-code"
CLAUDE_SUBAGENT_MODEL = "sonnet"
# Subagents may not delegate further; the reviewer must stay read-only.
FORBIDDEN_AGENT_TOOLS = {"Agent", "Task"}
WRITE_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
READ_ONLY_AGENTS = {"veriflow-reviewer"}
DESCRIPTION_LIMIT = 1024

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


def frontmatter(text: str) -> dict[str, str] | None:
    """Parse the flat ``key: value`` YAML frontmatter used by skills and agents."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.startswith((" ", "#")):
            continue
        key, separator, value = line.partition(":")
        if not separator:
            return None
        fields[key.strip()] = value.strip()
    return fields


def check_claude_code(root: Path) -> list[str]:
    """Check the Claude Code skill entry, Sonnet subagents, and plugin wrapper."""
    errors: list[str] = []
    skill = root / SKILL_DIR / "SKILL.md"
    if skill.is_file():
        fields = frontmatter(skill.read_text(encoding="utf-8"))
        if fields is None:
            errors.append("SKILL.md frontmatter is missing or malformed")
        else:
            if fields.get("name") != Path(SKILL_DIR).name:
                errors.append("SKILL.md name must match its directory name")
            description = fields.get("description", "")
            if not description or len(description) > DESCRIPTION_LIMIT:
                errors.append(f"SKILL.md description must be 1-{DESCRIPTION_LIMIT} characters")

    agent_dir = root / CLAUDE_AGENT_DIR
    agents = sorted(agent_dir.glob("*.md")) if agent_dir.is_dir() else []
    for agent in agents:
        relative = agent.relative_to(root)
        fields = frontmatter(agent.read_text(encoding="utf-8"))
        if fields is None:
            errors.append(f"agent frontmatter is missing or malformed: {relative}")
            continue
        if fields.get("name") != agent.stem:
            errors.append(f"agent name must match its file name: {relative}")
        if not fields.get("description"):
            errors.append(f"agent description is empty: {relative}")
        if fields.get("model") != CLAUDE_SUBAGENT_MODEL:
            errors.append(f"agent model must be {CLAUDE_SUBAGENT_MODEL!r}: {relative}")
        tools = {item.strip() for item in fields.get("tools", "").split(",") if item.strip()}
        if not tools:
            errors.append(f"agent must list its tools explicitly: {relative}")
        if tools & FORBIDDEN_AGENT_TOOLS:
            errors.append(f"agent must not delegate to further subagents: {relative}")
        if agent.stem in READ_ONLY_AGENTS and tools & WRITE_TOOLS:
            errors.append(f"read-only agent lists write tools: {relative}")

    plugin = root / CLAUDE_PLUGIN_DIR
    manifest = plugin / ".claude-plugin" / "plugin.json"
    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"claude-code plugin.json is invalid JSON: {exc}")
        else:
            if data.get("name") != Path(SKILL_DIR).name:
                errors.append("claude-code plugin.json name must be the skill name")
        links = {
            plugin / "skills" / Path(SKILL_DIR).name: root / SKILL_DIR,
            plugin / "agents": agent_dir,
        }
        for link, target in links.items():
            if not link.exists() or link.resolve() != target.resolve():
                errors.append(f"{link.relative_to(root)} must resolve to {target.relative_to(root)}")
    return errors


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

    errors.extend(check_claude_code(root))

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

    print(
        f"repository validation passed ({len(REQUIRED)} required files, local links and "
        "Claude Code definitions checked)"
    )
    print("note: this proves repository consistency, not workflow behavior or delivery authorization")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
