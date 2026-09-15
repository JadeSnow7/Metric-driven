#!/usr/bin/env python3
"""Read-only consistency and delivery-gate checks for task-state.json.

This tool intentionally cannot prove product success or authorization truth. It
checks only the record, referenced local evidence, and observable Git state.

Exit codes: 0 = no errors, 1 = record or gate errors, 2 = operational error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "1.1"
# Keep the established domain so renaming the skill does not invalidate
# revision tokens already stored in existing task records.
REVISION_DOMAIN = b"evidence-driven-development/revision-v2\0"

ID_PREFIXES = {
    "sources": "SRC-",
    "main_tasks": "MT-",
    "metrics": "MET-",
    "implementation_tasks": "IT-",
    "evidence": "EVD-",
    "changes": "CHG-",
    "decisions": "DEC-",
    "hypotheses": "HYP-",
    "actions": "ACT-",
}

ROOT_FIELDS = (
    "schema_version",
    "task",
    "discovery",
    "sources",
    "main_tasks",
    "metrics",
    "implementation_tasks",
    "evidence",
    "changes",
    "overall_acceptance",
    "baseline",
    "authorization",
    "delivery",
    "actions",
    "decisions",
    "hypotheses",
    "recovery_strategy",
)

DISCOVERY_STATES = {"needs_clarification", "exploring", "ready"}
TASK_RECORD_STATES = {
    "needs_clarification",
    "exploring",
    "ready",
    "in_progress",
    "blocked",
    "implemented",
    "verified",
    "failed",
    "paused",
    "completed",
    "cancelled",
}
TASK_MODES = {"new", "resume"}
TASK_STATES = {
    "proposed",
    "defined",
    "planned",
    "in_progress",
    "blocked",
    "implemented",
    "verified",
    "failed",
    "cancelled",
}
VERIFY_STATES = {"passed", "failed", "undetermined"}
EVIDENCE_STATES = {"current", "stale"}
CHANGE_STATES = {"proposed", "implemented", "reviewed", "reverted"}
BASELINE_STATES = {"clean", "dirty_dependency_confirmed", "unknown"}
IMPLEMENTABLE_BASELINE_STATES = {"clean", "dirty_dependency_confirmed"}
AUTH_STATES = {"authorized", "not_authorized", "unknown"}
DELIVERY_STATES = {
    "not_started",
    "passed",
    "failed",
    "unavailable",
    "completed",
    "rolled_back",
}
ACTION_STATES = {"planned", "in_progress", "completed", "failed", "unknown"}
EXECUTED_ACTION_STATES = {"in_progress", "completed", "failed"}
METRIC_KINDS = {"mandatory_gate", "improvement_target", "non_regression"}
SOURCE_KINDS = {
    "user_requirement",
    "user_feedback",
    "reproduced_defect",
    "external_material",
    "agent_inference",
    "implementation_adjustment",
}
USER_INSTRUCTION_KINDS = {"user_requirement", "user_feedback"}
ADOPTION_STATES = {"proposed", "accepted", "rejected", "superseded"}
AUTH_ACTIONS = ("commit", "push", "merge", "deploy")
DELIVERY_KEYS = (
    "local_validation",
    "local_commit",
    "push",
    "remote_ci",
    "merge",
    "deploy",
)
GATES = ("record", "implementation", "acceptance", "local-commit", "push", "merge", "deploy")

# Record files that live beside a task-state.json in records/<TASK-ID>/. They are
# excluded from behavioral fingerprints so saving status or evidence does not
# invalidate evidence that was already bound to the implementation.
RECORD_FILES = ("index.md", "task-summary.md", "work-log.md")
RECORD_DIRECTORIES = ("handoffs", "evidence")
EVIDENCE_DIRECTORY = "evidence"

SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
PLACEHOLDER_PATTERN = re.compile(r"replace[-_/]with|0000-00-00", re.IGNORECASE)


class ValidationError(RuntimeError):
    """Operational failure while reading the repository."""


def run_git(repo: Path, args: list[str], input_bytes: bytes | None = None) -> bytes:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=env,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValidationError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def ensure_repository(repo: Path) -> Path:
    repo = repo.resolve()
    top = run_git(repo, ["rev-parse", "--show-toplevel"]).decode().strip()
    top_path = Path(top).resolve()
    if top_path != repo:
        raise ValidationError(f"--repo must be the Git root: expected {top_path}")
    return repo


def relative_manifest(repo: Path, manifest: Path) -> str:
    try:
        return manifest.resolve().relative_to(repo).as_posix()
    except ValueError as exc:
        raise ValidationError("task-state.json must be inside --repo") from exc


def record_directory(repo: Path, manifest: Path) -> str | None:
    parent = Path(relative_manifest(repo, manifest)).parent
    return None if parent == Path(".") else parent.as_posix()


def resolve_base(repo: Path, base_ref: Any) -> str:
    if not isinstance(base_ref, str) or not base_ref.strip():
        raise ValidationError("baseline.git_ref is required to compute a revision")
    if base_ref.startswith("-"):
        raise ValidationError(f"baseline.git_ref is not a commit reference: {base_ref!r}")
    return run_git(repo, ["rev-parse", "--verify", f"{base_ref}^{{commit}}"]).decode().strip()


def revision_metadata_paths(repo: Path, manifest: Path) -> list[str]:
    """Return fixed task-record paths excluded from behavioral fingerprints."""

    manifest_rel = relative_manifest(repo, manifest)
    directory = record_directory(repo, manifest)
    if directory is None:
        return [manifest_rel]
    names = (*RECORD_FILES, *RECORD_DIRECTORIES)
    return [manifest_rel, *(f"{directory}/{name}" for name in names)]


def is_revision_metadata(path: str, excluded: list[str]) -> bool:
    return any(path == item or path.startswith(f"{item}/") for item in excluded)


def split_null_terminated(raw: bytes) -> list[str]:
    return [item.decode("utf-8", errors="surrogateescape") for item in raw.split(b"\0") if item]


def worktree_changes(repo: Path, base: str) -> list[str]:
    """Paths whose working-tree state differs from base, including untracked files.

    Renames are listed as a deletion plus an addition so the original path is
    never hidden from review.
    """

    tracked = run_git(repo, ["diff", "--name-only", "-z", "--no-renames", "--no-ext-diff", base, "--"])
    untracked = run_git(repo, ["ls-files", "--others", "--exclude-standard", "-z"])
    return sorted(set(split_null_terminated(tracked)) | set(split_null_terminated(untracked)))


def hash_worktree_blobs(repo: Path, paths: list[str]) -> dict[str, bytes]:
    """Hash files as Git would store them, applying clean filters and EOL rules.

    `git hash-object` without `-w` does not write objects. Using Git's view of
    the content keeps the fingerprint stable across checkouts that differ only
    in line-ending conversion.
    """

    hashes: dict[str, bytes] = {}
    line_safe = [path for path in paths if "\n" not in path]
    if line_safe:
        payload = "".join(f"{path}\n" for path in line_safe).encode("utf-8", errors="surrogateescape")
        output = run_git(repo, ["hash-object", "--stdin-paths"], input_bytes=payload).split()
        if len(output) != len(line_safe):
            raise ValidationError("git hash-object returned an unexpected number of hashes")
        hashes.update(zip(line_safe, output))
    for path in paths:
        if path not in hashes:
            hashes[path] = run_git(repo, ["hash-object", "--", path]).strip()
    return hashes


def fingerprint_entries(repo: Path, paths: list[str]) -> dict[str, bytes]:
    entries: dict[str, bytes] = {}
    regular: list[str] = []
    for rel in paths:
        path = repo / rel
        if path.is_symlink():
            entries[rel] = b"120000\0" + os.readlink(path).encode("utf-8", errors="surrogateescape")
        elif path.is_file():
            regular.append(rel)
        elif path.is_dir():
            head = b""
            if (path / ".git").exists():
                try:
                    head = run_git(path, ["rev-parse", "HEAD"]).strip()
                except ValidationError:
                    head = b"no-head"  # nested repository without commits
            entries[rel] = b"160000\0" + head
        elif not os.path.lexists(path):
            entries[rel] = b"deleted\0"
        else:
            entries[rel] = b"other\0"
    for rel, blob in hash_worktree_blobs(repo, regular).items():
        mode = b"100755" if os.stat(repo / rel).st_mode & stat.S_IXUSR else b"100644"
        entries[rel] = mode + b"\0" + blob
    return entries


def current_revision(repo: Path, manifest: Path, base_ref: Any) -> str:
    """Fingerprint base-to-worktree content, excluding task-record metadata.

    The token depends only on which paths differ from base and what they
    contain. It does not change when files are staged or committed, and it does
    not depend on local diff settings such as prefixes, context, or algorithms.
    """

    base = resolve_base(repo, base_ref)
    excluded = revision_metadata_paths(repo, manifest)
    paths = [path for path in worktree_changes(repo, base) if not is_revision_metadata(path, excluded)]
    if not paths:
        return f"commit:{base}"

    entries = fingerprint_entries(repo, paths)
    digest = hashlib.sha256(REVISION_DOMAIN)
    digest.update(base.encode("ascii"))
    for rel in paths:
        digest.update(b"\0path\0")
        digest.update(rel.encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        digest.update(entries[rel])
    return f"patch:{base}:{digest.hexdigest()}"


def uncommitted_paths(repo: Path) -> list[str]:
    raw = run_git(repo, ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames"])
    return sorted({entry[3:] for entry in split_null_terminated(raw) if len(entry) > 3})


def changed_paths(repo: Path, manifest: Path, base_ref: Any) -> list[str]:
    """Return task-worktree changes since base, excluding the state manifest."""

    base = resolve_base(repo, base_ref)
    manifest_rel = relative_manifest(repo, manifest)
    return [path for path in worktree_changes(repo, base) if path != manifest_rel]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized_declared_path(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    normalized = path.as_posix().rstrip("/")
    return normalized or None


def path_is_covered(changed: str, declared: str) -> bool:
    return changed == declared or changed.startswith(f"{declared}/")


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def id_list(value: Any) -> list[str]:
    return [item for item in as_list(value) if isinstance(item, str)]


def is_one_of(value: Any, allowed: Iterable[str]) -> bool:
    """Membership test that tolerates unhashable values from malformed records."""

    return isinstance(value, str) and value in allowed


def gate_reaches(gate: str, threshold: str) -> bool:
    return GATES.index(gate) >= GATES.index(threshold)


def nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, dict):
        return bool(value)
    return value is not None


def add_issue(bucket: list[dict[str, str]], code: str, message: str) -> None:
    bucket.append({"code": code, "message": message})


def require_fields(
    obj: Any,
    fields: Iterable[str],
    label: str,
    errors: list[dict[str, str]],
) -> None:
    if not isinstance(obj, dict):
        add_issue(errors, "TYPE_OBJECT", f"{label} must be an object")
        return
    for field in fields:
        if field not in obj:
            add_issue(errors, "FIELD_MISSING", f"{label}.{field} is required")


def index_items(
    state: dict[str, Any],
    key: str,
    errors: list[dict[str, str]],
) -> dict[str, dict[str, Any]]:
    value = state.get(key, [])
    if not isinstance(value, list):
        add_issue(errors, "TYPE_LIST", f"{key} must be a list")
        return {}
    prefix = ID_PREFIXES[key]
    result: dict[str, dict[str, Any]] = {}
    for position, item in enumerate(value):
        label = f"{key}[{position}]"
        if not isinstance(item, dict):
            add_issue(errors, "TYPE_OBJECT", f"{label} must be an object")
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.startswith(prefix):
            add_issue(errors, "ID_FORMAT", f"{label}.id must start with {prefix}")
            continue
        if item_id in result:
            add_issue(errors, "ID_DUPLICATE", f"duplicate id {item_id}")
            continue
        result[item_id] = item
    return result


def require_refs(
    owner: str,
    refs: Any,
    target: dict[str, Any],
    errors: list[dict[str, str]],
    code: str,
) -> None:
    if not isinstance(refs, list):
        add_issue(errors, "TYPE_LIST", f"{owner} must be a list")
        return
    for ref in refs:
        if not isinstance(ref, str):
            add_issue(errors, "TYPE_ID", f"{owner} must contain id strings, not {ref!r}")
        elif ref not in target:
            add_issue(errors, code, f"{owner} references missing id {ref!r}")


def safe_repo_file(repo: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = Path(value)
    if raw.is_absolute():
        return None
    resolved = (repo / raw).resolve()
    try:
        resolved.relative_to(repo)
    except ValueError:
        return None
    return resolved


def find_placeholders(value: Any, label: str = "") -> list[str]:
    if isinstance(value, str):
        return [label or "root"] if PLACEHOLDER_PATTERN.search(value) else []
    if isinstance(value, dict):
        return [
            hit
            for key, item in value.items()
            for hit in find_placeholders(item, f"{label}.{key}" if label else str(key))
        ]
    if isinstance(value, list):
        return [hit for position, item in enumerate(value) for hit in find_placeholders(item, f"{label}[{position}]")]
    return []


def authorization_status(state: dict[str, Any], action: str) -> Any:
    return as_dict(as_dict(state.get("authorization")).get(action)).get("status")


def completed_action(indexes: dict[str, dict[str, Any]], action: str) -> bool:
    return any(
        item.get("authorization_action") == action and item.get("status") == "completed"
        for item in indexes["actions"].values()
    )


def validate_record(
    state: dict[str, Any], repo: Path, manifest: Path, gate: str = "record"
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, dict[str, Any]]]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    require_fields(state, ROOT_FIELDS, "root", errors)
    if state.get("schema_version") != SCHEMA_VERSION:
        add_issue(
            errors,
            "SCHEMA_VERSION",
            f"schema_version must be {SCHEMA_VERSION!r}; when migrating from 1.0, add evidence[].sha256 "
            "and recompute every revision token with --print-revision before re-assessing evidence",
        )

    indexes = {key: index_items(state, key, errors) for key in ID_PREFIXES}
    sources = indexes["sources"]
    main_tasks = indexes["main_tasks"]
    metrics = indexes["metrics"]
    implementation_tasks = indexes["implementation_tasks"]
    evidence = indexes["evidence"]
    changes = indexes["changes"]
    decisions = indexes["decisions"]

    require_fields(state.get("task", {}), ("id", "title", "mode", "status", "source_ids"), "task", errors)
    task = as_dict(state.get("task"))
    require_refs("task.source_ids", task.get("source_ids", []), sources, errors, "CROSSREF_SOURCE")
    if "status" in task and not is_one_of(task.get("status"), TASK_RECORD_STATES):
        add_issue(errors, "TASK_RECORD_STATUS", f"invalid task.status {task.get('status')!r}")
    if "mode" in task and not is_one_of(task.get("mode"), TASK_MODES):
        add_issue(errors, "TASK_MODE", f"task.mode must be 'new' or 'resume', not {task.get('mode')!r}")

    require_fields(state.get("discovery", {}), ("status",), "discovery", errors)
    discovery = as_dict(state.get("discovery"))
    discovery_status = discovery.get("status")
    if not is_one_of(discovery_status, DISCOVERY_STATES):
        add_issue(errors, "DISCOVERY_STATUS", f"invalid discovery.status {discovery_status!r}")
    if discovery_status == "ready":
        for field in ("user", "scenario", "problem", "expected_outcome", "scope", "acceptable_result"):
            if not nonempty(discovery.get(field)):
                add_issue(errors, "DISCOVERY_FIELD_EMPTY", f"discovery.{field} is required when ready")

    for source_id, source in sources.items():
        require_fields(source, ("kind", "reference", "summary", "adoption"), source_id, errors)
        if not is_one_of(source.get("kind"), SOURCE_KINDS):
            add_issue(errors, "SOURCE_KIND", f"{source_id} has invalid kind")
        if not is_one_of(source.get("adoption"), ADOPTION_STATES):
            add_issue(errors, "SOURCE_ADOPTION", f"{source_id} has invalid adoption")

    for main_id, main in main_tasks.items():
        require_fields(
            main,
            (
                "source_ids",
                "goal",
                "scope",
                "non_goals",
                "dependencies",
                "assumptions",
                "status",
                "metric_ids",
                "implementation_task_ids",
            ),
            main_id,
            errors,
        )
        require_refs(f"{main_id}.source_ids", main.get("source_ids", []), sources, errors, "CROSSREF_SOURCE")
        require_refs(f"{main_id}.metric_ids", main.get("metric_ids", []), metrics, errors, "CROSSREF_METRIC")
        require_refs(
            f"{main_id}.implementation_task_ids",
            main.get("implementation_task_ids", []),
            implementation_tasks,
            errors,
            "CROSSREF_IMPLEMENTATION",
        )
        require_refs(f"{main_id}.dependencies", main.get("dependencies", []), main_tasks, errors, "CROSSREF_MAIN_TASK")
        for metric_id in id_list(main.get("metric_ids")):
            if metric_id in metrics and metrics[metric_id].get("main_task_id") != main_id:
                add_issue(errors, "CROSSREF_MAIN_TASK", f"{main_id} includes metric owned by another main task: {metric_id}")
        for implementation_id in id_list(main.get("implementation_task_ids")):
            if (
                implementation_id in implementation_tasks
                and implementation_tasks[implementation_id].get("main_task_id") != main_id
            ):
                add_issue(
                    errors,
                    "CROSSREF_MAIN_TASK",
                    f"{main_id} includes implementation task owned by another main task: {implementation_id}",
                )
        if not is_one_of(main.get("status"), TASK_STATES):
            add_issue(errors, "TASK_STATUS", f"{main_id} has invalid status")
        if not id_list(main.get("source_ids")):
            add_issue(errors, "MAIN_TASK_SOURCE_MISSING", f"{main_id} must cite at least one source")
        for field in ("goal", "scope", "non_goals"):
            if not nonempty(main.get(field)):
                add_issue(errors, "MAIN_TASK_FIELD_EMPTY", f"{main_id}.{field} must not be empty")

    for metric_id, metric in metrics.items():
        require_fields(
            metric,
            ("main_task_id", "kind", "name", "baseline", "target", "method", "environment_data", "evidence_ids", "status"),
            metric_id,
            errors,
        )
        owner = metric.get("main_task_id")
        if not is_one_of(owner, main_tasks):
            add_issue(errors, "CROSSREF_MAIN_TASK", f"{metric_id} references missing main task")
        elif metric_id not in id_list(main_tasks[owner].get("metric_ids")):
            add_issue(errors, "CROSSREF_MAIN_TASK", f"{metric_id} is absent from its main task metric_ids")
        if not is_one_of(metric.get("kind"), METRIC_KINDS):
            add_issue(errors, "METRIC_KIND", f"{metric_id} has invalid kind")
        if not is_one_of(metric.get("status"), VERIFY_STATES):
            add_issue(errors, "VERIFY_STATUS", f"{metric_id} has invalid status")
        require_refs(f"{metric_id}.evidence_ids", metric.get("evidence_ids", []), evidence, errors, "CROSSREF_EVIDENCE")
        for field in ("name", "baseline", "target", "method", "environment_data"):
            if not nonempty(metric.get(field)):
                add_issue(errors, "METRIC_FIELD_EMPTY", f"{metric_id}.{field} must not be empty")
        if metric.get("kind") == "improvement_target" and metric.get("status") == "failed":
            if not is_one_of(metric.get("decision_id"), decisions):
                add_issue(
                    warnings,
                    "IMPROVEMENT_DECISION_MISSING",
                    f"{metric_id} failed without a linked DEC-* decision",
                )

    for implementation_id, item in implementation_tasks.items():
        require_fields(
            item,
            (
                "main_task_id",
                "source_ids",
                "scope",
                "file_scope",
                "interface_constraints",
                "dependencies",
                "acceptance",
                "support_reason",
                "evidence_ids",
                "owner",
                "status",
            ),
            implementation_id,
            errors,
        )
        owner = item.get("main_task_id")
        if not is_one_of(owner, main_tasks):
            add_issue(errors, "CROSSREF_MAIN_TASK", f"{implementation_id} references missing main task")
        elif implementation_id not in id_list(main_tasks[owner].get("implementation_task_ids")):
            add_issue(
                errors,
                "CROSSREF_MAIN_TASK",
                f"{implementation_id} is absent from its main task implementation_task_ids",
            )
        require_refs(f"{implementation_id}.source_ids", item.get("source_ids", []), sources, errors, "CROSSREF_SOURCE")
        require_refs(f"{implementation_id}.dependencies", item.get("dependencies", []), implementation_tasks, errors, "CROSSREF_IMPLEMENTATION")
        require_refs(f"{implementation_id}.acceptance", item.get("acceptance", []), metrics, errors, "CROSSREF_METRIC")
        require_refs(f"{implementation_id}.evidence_ids", item.get("evidence_ids", []), evidence, errors, "CROSSREF_EVIDENCE")
        if not item.get("acceptance") and not nonempty(item.get("support_reason")):
            add_issue(errors, "IMPLEMENTATION_UNJUSTIFIED", f"{implementation_id} needs acceptance metrics or support_reason")
        for metric_id in id_list(item.get("acceptance")):
            if metric_id in metrics and metrics[metric_id].get("main_task_id") != owner:
                add_issue(
                    errors,
                    "IMPLEMENTATION_METRIC_SCOPE",
                    f"{implementation_id} acceptance references another main task's metric: {metric_id}",
                )
        if not is_one_of(item.get("status"), TASK_STATES):
            add_issue(errors, "TASK_STATUS", f"{implementation_id} has invalid status")
        for field in ("scope", "file_scope", "owner"):
            if not nonempty(item.get(field)):
                add_issue(errors, "IMPLEMENTATION_FIELD_EMPTY", f"{implementation_id}.{field} must not be empty")

    baseline = as_dict(state.get("baseline"))
    revision: str | None = None
    if evidence or changes:
        try:
            revision = current_revision(repo, manifest, baseline.get("git_ref"))
        except ValidationError as exc:
            add_issue(errors, "REVISION_UNAVAILABLE", str(exc))

    evidence_directory = record_directory(repo, manifest)
    hash_bucket = errors if gate in {"acceptance", "local-commit", "push", "merge", "deploy"} else warnings
    for evidence_id, item in evidence.items():
        require_fields(item, ("path", "kind", "supports", "revision", "status", "result", "observed_at"), evidence_id, errors)
        require_refs(f"{evidence_id}.supports", item.get("supports", []), metrics, errors, "CROSSREF_METRIC")
        if not item.get("supports"):
            add_issue(errors, "EVIDENCE_SUPPORT_MISSING", f"{evidence_id} must support at least one metric")
        path = safe_repo_file(repo, item.get("path"))
        if path is None:
            add_issue(errors, "EVIDENCE_PATH", f"{evidence_id}.path must stay inside the repository")
        elif not path.is_file():
            add_issue(errors, "EVIDENCE_MISSING", f"{evidence_id} file does not exist: {item.get('path')}")
        else:
            digest = item.get("sha256")
            if digest is None:
                add_issue(
                    hash_bucket,
                    "EVIDENCE_HASH_MISSING",
                    f"{evidence_id}.sha256 is required from the local-commit gate onward (use --print-sha256)",
                )
            elif not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
                add_issue(errors, "EVIDENCE_HASH_FORMAT", f"{evidence_id}.sha256 must be 64 lowercase hex characters")
            elif sha256_file(path) != digest:
                add_issue(errors, "EVIDENCE_HASH_MISMATCH", f"{evidence_id} file content no longer matches its sha256")
            if evidence_directory is not None:
                relative = path.relative_to(repo).as_posix()
                if not path_is_covered(relative, f"{evidence_directory}/{EVIDENCE_DIRECTORY}"):
                    add_issue(
                        warnings,
                        "EVIDENCE_OUTSIDE_RECORD_DIR",
                        f"{evidence_id} is outside {evidence_directory}/{EVIDENCE_DIRECTORY}/, so it is part of the "
                        "revision fingerprint and adding or editing it invalidates other evidence",
                    )
            if item.get("kind") == "execution" and path is not None and path.is_file():
                try:
                    execution = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    add_issue(errors, "EXECUTION_RECORD_INVALID", f"{evidence_id} execution record is unreadable: {exc}")
                else:
                    required = ("argv", "cwd", "started_at", "ended_at", "exit_code", "timed_out", "stdout", "stderr")
                    for field in required:
                        if field not in execution:
                            add_issue(errors, "EXECUTION_RECORD_FIELD", f"{evidence_id} missing execution field {field}")
                    if execution.get("timed_out") and execution.get("result") != "timeout":
                        add_issue(errors, "EXECUTION_RESULT_MISMATCH", f"{evidence_id} timeout does not have result=timeout")
                    if execution.get("exit_code") == 0 and execution.get("result") != "passed":
                        add_issue(errors, "EXECUTION_RESULT_MISMATCH", f"{evidence_id} exit_code 0 does not have result=passed")
                    if isinstance(execution.get("exit_code"), int) and execution.get("exit_code") != 0 and not execution.get("timed_out") and execution.get("result") == "passed":
                        add_issue(errors, "EXECUTION_RESULT_MISMATCH", f"{evidence_id} failed command is marked passed")
                    if item.get("result") == "passed" and (execution.get("exit_code") != 0 or execution.get("timed_out") or execution.get("result") != "passed"):
                        add_issue(errors, "EXECUTION_RESULT_MISMATCH", f"{evidence_id} outer passed result disagrees with actual execution")
                    if execution.get("stdout_required") and not execution.get("stdout_present"):
                        add_issue(errors, "EXECUTION_OUTPUT_MISSING", f"{evidence_id} requires stdout but captured none")
                    for input_path, input_meta in as_dict(execution.get("inputs")).items():
                        candidate = Path(input_path)
                        if not candidate.is_absolute():
                            candidate = Path(execution.get("cwd", "")) / candidate
                        try:
                            checked = candidate.resolve().relative_to(repo).as_posix()
                        except (OSError, ValueError):
                            checked = None
                        checked_path = repo / checked if checked is not None else None
                        expected = as_dict(input_meta).get("sha256")
                        if checked_path is None or not checked_path.is_file() or not isinstance(expected, str) or sha256_file(checked_path) != expected:
                            add_issue(errors, "EXECUTION_INPUT_STALE", f"{evidence_id} input hash is stale or outside repository: {input_path}")
        if not is_one_of(item.get("status"), EVIDENCE_STATES):
            add_issue(errors, "EVIDENCE_STATUS", f"{evidence_id} has invalid status")
        if not is_one_of(item.get("result"), VERIFY_STATES):
            add_issue(errors, "VERIFY_STATUS", f"{evidence_id} has invalid result")
        if revision is not None and item.get("status") == "current" and item.get("revision") != revision:
            add_issue(errors, "EVIDENCE_STALE", f"{evidence_id} revision does not match current repository state")

    for change_id, item in changes.items():
        require_fields(item, ("implementation_task_ids", "paths", "evidence_ids", "revision", "status"), change_id, errors)
        require_refs(
            f"{change_id}.implementation_task_ids",
            item.get("implementation_task_ids", []),
            implementation_tasks,
            errors,
            "CROSSREF_IMPLEMENTATION",
        )
        require_refs(f"{change_id}.evidence_ids", item.get("evidence_ids", []), evidence, errors, "CROSSREF_EVIDENCE")
        if not item.get("implementation_task_ids"):
            add_issue(errors, "CHANGE_IMPLEMENTATION_MISSING", f"{change_id} needs an implementation task")
        if item.get("status") == "reviewed" and not item.get("evidence_ids"):
            add_issue(errors, "CHANGE_EVIDENCE_MISSING", f"reviewed {change_id} needs evidence")
        paths = item.get("paths")
        if "paths" in item and not isinstance(paths, list):
            add_issue(errors, "TYPE_LIST", f"{change_id}.paths must be a list")
        elif not paths:
            add_issue(errors, "CHANGE_PATHS_EMPTY", f"{change_id}.paths must not be empty")
        else:
            for value in paths:
                if normalized_declared_path(value) is None:
                    add_issue(errors, "CHANGE_PATH", f"{change_id} has unsafe or empty path {value!r}")
        if not is_one_of(item.get("status"), CHANGE_STATES):
            add_issue(errors, "CHANGE_STATUS", f"{change_id} has invalid status")
        if revision is not None and item.get("status") == "reviewed" and item.get("revision") != revision:
            add_issue(errors, "CHANGE_STALE", f"{change_id} revision does not match current repository state")

    require_fields(state.get("overall_acceptance", {}), ("metric_ids", "evidence_ids", "status"), "overall_acceptance", errors)
    overall = as_dict(state.get("overall_acceptance"))
    require_refs("overall_acceptance.metric_ids", overall.get("metric_ids", []), metrics, errors, "CROSSREF_METRIC")
    require_refs("overall_acceptance.evidence_ids", overall.get("evidence_ids", []), evidence, errors, "CROSSREF_EVIDENCE")
    if not is_one_of(overall.get("status"), VERIFY_STATES):
        add_issue(errors, "VERIFY_STATUS", "overall_acceptance.status is invalid")

    require_fields(state.get("baseline", {}), ("git_ref", "worktree_status", "ownership", "prepared_at"), "baseline", errors)
    if not is_one_of(baseline.get("worktree_status"), BASELINE_STATES):
        add_issue(errors, "BASELINE_STATUS", "baseline.worktree_status is invalid")
    if not nonempty(baseline.get("ownership")):
        add_issue(errors, "BASELINE_OWNERSHIP", "baseline.ownership must not be empty")

    require_fields(state.get("authorization", {}), AUTH_ACTIONS, "authorization", errors)
    authorization = as_dict(state.get("authorization"))
    for action in AUTH_ACTIONS:
        require_fields(authorization.get(action, {}), ("status", "source_id"), f"authorization.{action}", errors)
        entry = as_dict(authorization.get(action))
        if not is_one_of(entry.get("status"), AUTH_STATES):
            add_issue(errors, "AUTH_STATUS", f"authorization.{action}.status is invalid")
        if entry.get("status") == "authorized":
            source_id = entry.get("source_id")
            source = sources.get(source_id) if isinstance(source_id, str) else None
            if source is None:
                add_issue(errors, "AUTH_SOURCE", f"authorized {action} needs an existing source_id")
            elif not is_one_of(source.get("kind"), USER_INSTRUCTION_KINDS):
                add_issue(errors, "AUTH_SOURCE", f"authorized {action} must cite a user instruction")
            elif source.get("adoption") != "accepted":
                add_issue(
                    errors,
                    "AUTH_SOURCE_NOT_ACCEPTED",
                    f"authorized {action} cites {source_id} whose adoption is {source.get('adoption')!r}, not 'accepted'",
                )

    require_fields(state.get("delivery", {}), DELIVERY_KEYS, "delivery", errors)
    delivery = as_dict(state.get("delivery"))
    for key in DELIVERY_KEYS:
        if not is_one_of(delivery.get(key), DELIVERY_STATES):
            add_issue(errors, "DELIVERY_STATUS", f"delivery.{key} has invalid status")

    unauthorized_bucket = errors if gate_reaches(gate, "push") else warnings
    action_keys: set[str] = set()
    for action_id, item in indexes["actions"].items():
        require_fields(item, ("kind", "status", "authorization_action", "idempotency_key", "receipt"), action_id, errors)
        status = item.get("status")
        if not is_one_of(status, ACTION_STATES):
            add_issue(errors, "ACTION_STATUS", f"{action_id} has invalid status")
        auth_action = item.get("authorization_action")
        if not is_one_of(auth_action, AUTH_ACTIONS):
            add_issue(errors, "ACTION_AUTH", f"{action_id}.authorization_action is invalid")
        elif is_one_of(status, EXECUTED_ACTION_STATES) and authorization_status(state, auth_action) != "authorized":
            add_issue(
                unauthorized_bucket,
                "ACTION_UNAUTHORIZED",
                f"{action_id} ({auth_action}) is {status} but authorization.{auth_action} is not authorized; "
                "keep the record, verify the real external state, and confirm with the user before continuing",
            )
        key = item.get("idempotency_key")
        if not isinstance(key, str) or not key.strip():
            add_issue(errors, "ACTION_KEY", f"{action_id}.idempotency_key must be a non-empty string")
        elif key in action_keys:
            add_issue(errors, "ACTION_KEY_DUPLICATE", f"duplicate idempotency_key {key!r}")
        else:
            action_keys.add(key)
        if status == "completed" and not nonempty(item.get("receipt")):
            add_issue(errors, "ACTION_RECEIPT", f"completed {action_id} needs a receipt")

    placeholder_bucket = warnings if gate == "record" else errors
    for label in find_placeholders(state):
        add_issue(placeholder_bucket, "PLACEHOLDER_VALUE", f"{label} still contains a template placeholder")

    return errors, warnings, indexes


def add_gate_errors(
    gate: str,
    state: dict[str, Any],
    repo: Path,
    manifest: Path,
    indexes: dict[str, dict[str, Any]],
    errors: list[dict[str, str]],
) -> str | None:
    if gate == "record":
        return None

    discovery = as_dict(state.get("discovery"))
    main_tasks = indexes["main_tasks"]
    metrics = indexes["metrics"]
    evidence = indexes["evidence"]
    changes = indexes["changes"]
    implementation_tasks = indexes["implementation_tasks"]
    baseline = as_dict(state.get("baseline"))
    delivery = as_dict(state.get("delivery"))
    overall = as_dict(state.get("overall_acceptance"))

    if discovery.get("status") != "ready":
        add_issue(errors, "DISCOVERY_NOT_READY", "implementation is blocked until discovery.status is ready")
    if not main_tasks:
        add_issue(errors, "MAIN_TASKS_MISSING", "at least one result-oriented main task is required")
    for main_id, main in main_tasks.items():
        linked = [item for item in metrics.values() if item.get("main_task_id") == main_id]
        if not linked:
            add_issue(errors, "MAIN_TASK_METRICS_MISSING", f"{main_id} has no metric")
        if main.get("status") == "proposed":
            add_issue(errors, "MAIN_TASK_UNDEFINED", f"{main_id} boundary has not been defined")
    if not is_one_of(baseline.get("worktree_status"), IMPLEMENTABLE_BASELINE_STATES):
        add_issue(
            errors,
            "BASELINE_NOT_CLEAN",
            "implementation needs a clean task worktree or a confirmed dirty dependency in baseline.worktree_status",
        )
    try:
        resolve_base(repo, baseline.get("git_ref"))
    except ValidationError as exc:
        add_issue(errors, "BASELINE_UNRESOLVED", str(exc))

    if gate == "implementation":
        return None

    try:
        revision = current_revision(repo, manifest, baseline.get("git_ref"))
    except ValidationError as exc:
        add_issue(errors, "REVISION_UNAVAILABLE", str(exc))
        revision = None

    for metric_id, metric in metrics.items():
        kind = metric.get("kind")
        status = metric.get("status")
        if is_one_of(kind, {"mandatory_gate", "non_regression"}) and status != "passed":
            add_issue(errors, "MANDATORY_GATE", f"{metric_id} ({kind}) is {status!r}, not passed")
        if kind == "improvement_target" and status == "undetermined":
            add_issue(errors, "IMPROVEMENT_UNDETERMINED", f"{metric_id} improvement target is undetermined")
        if kind == "improvement_target" and status == "failed" and not is_one_of(metric.get("decision_id"), indexes["decisions"]):
            add_issue(errors, "IMPROVEMENT_UNACCEPTED", f"{metric_id} failed without a recorded decision")
        if is_one_of(status, {"passed", "failed"}) and not id_list(metric.get("evidence_ids")):
            add_issue(errors, "METRIC_EVIDENCE_MISSING", f"{metric_id} is assessed without evidence")
        for evidence_id in id_list(metric.get("evidence_ids")):
            item = evidence.get(evidence_id, {})
            if item.get("status") != "current" or item.get("revision") != revision:
                add_issue(errors, "METRIC_EVIDENCE_NOT_CURRENT", f"{metric_id} evidence {evidence_id} is not current")
            if status == "passed" and item.get("result") != "passed":
                add_issue(errors, "METRIC_EVIDENCE_RESULT", f"{metric_id} is passed but {evidence_id} is not")

    for implementation_id, item in implementation_tasks.items():
        if item.get("status") != "verified":
            add_issue(errors, "IMPLEMENTATION_NOT_VERIFIED", f"{implementation_id} is not verified")
        if item.get("status") == "verified" and not id_list(item.get("evidence_ids")):
            add_issue(errors, "IMPLEMENTATION_EVIDENCE_MISSING", f"{implementation_id} is verified without evidence")
        for evidence_id in id_list(item.get("evidence_ids")):
            evidence_item = evidence.get(evidence_id, {})
            if evidence_item.get("status") != "current" or evidence_item.get("revision") != revision:
                add_issue(errors, "IMPLEMENTATION_EVIDENCE_NOT_CURRENT", f"{implementation_id} evidence {evidence_id} is not current")
    for main_id, main in main_tasks.items():
        if main.get("status") != "verified":
            add_issue(errors, "MAIN_TASK_NOT_VERIFIED", f"{main_id} is not verified")
    for change_id, item in changes.items():
        if item.get("status") != "reviewed":
            add_issue(errors, "CHANGE_NOT_REVIEWED", f"{change_id} is not reviewed")
        if revision is not None and item.get("revision") != revision:
            add_issue(errors, "CHANGE_STALE", f"{change_id} is not bound to current state")
    if not changes:
        add_issue(errors, "CHANGES_MISSING", "local commit gate needs at least one reviewed CHG-* record")
    else:
        try:
            actual_paths = changed_paths(repo, manifest, baseline.get("git_ref"))
        except ValidationError as exc:
            add_issue(errors, "CHANGED_PATHS_UNAVAILABLE", str(exc))
        else:
            declared_paths = {
                normalized
                for item in changes.values()
                if item.get("status") == "reviewed"
                for value in as_list(item.get("paths"))
                if (normalized := normalized_declared_path(value)) is not None
            }
            for path in actual_paths:
                if not any(path_is_covered(path, declared) for declared in declared_paths):
                    add_issue(errors, "CHANGED_PATH_UNREVIEWED", f"changed path is not covered by a reviewed CHG-*: {path}")
    if overall.get("status") != "passed":
        add_issue(errors, "OVERALL_NOT_PASSED", "overall end-to-end acceptance is not passed")
    if not id_list(overall.get("evidence_ids")):
        add_issue(errors, "OVERALL_EVIDENCE_MISSING", "overall acceptance needs evidence")
    for evidence_id in id_list(overall.get("evidence_ids")):
        item = evidence.get(evidence_id, {})
        if item.get("status") != "current" or item.get("revision") != revision or item.get("result") != "passed":
            add_issue(errors, "OVERALL_EVIDENCE_NOT_CURRENT", f"overall evidence {evidence_id} is not current and passed")
    # Acceptance is deliberately independent of commit authorization.  The
    # local-commit gate reuses these product/review checks and adds the side
    # effect authorization below.
    if gate == "acceptance":
        return revision

    if authorization_status(state, "commit") != "authorized":
        add_issue(errors, "AUTH_COMMIT", "commit is not authorized")

    if gate == "local-commit":
        if delivery.get("local_commit") == "completed" or completed_action(indexes, "commit"):
            add_issue(errors, "DELIVERY_ALREADY_COMPLETED", "local commit is already recorded as completed; verify before repeating")
        return revision

    if delivery.get("local_commit") != "completed":
        add_issue(errors, "LOCAL_COMMIT_INCOMPLETE", "push gate requires a completed local commit")
    if authorization_status(state, "push") != "authorized":
        add_issue(errors, "AUTH_PUSH", "push is not authorized")
    try:
        excluded = revision_metadata_paths(repo, manifest)
        dirty = [path for path in uncommitted_paths(repo) if not is_revision_metadata(path, excluded)]
    except ValidationError as exc:
        add_issue(errors, "WORKTREE_UNAVAILABLE", str(exc))
    else:
        if dirty:
            listed = ", ".join(dirty[:10]) + (" ..." if len(dirty) > 10 else "")
            add_issue(errors, "WORKTREE_DIRTY", f"push gate requires task changes to be committed; uncommitted: {listed}")

    if gate == "push":
        if delivery.get("push") == "completed" or completed_action(indexes, "push"):
            add_issue(errors, "DELIVERY_ALREADY_COMPLETED", "push is already recorded as completed; verify the receipt instead of repeating")
        return revision

    if delivery.get("push") != "completed":
        add_issue(errors, "PUSH_INCOMPLETE", "merge gate requires a completed push")
    if delivery.get("remote_ci") != "passed":
        add_issue(errors, "REMOTE_CI", "merge gate requires remote CI to have actually passed")
    if authorization_status(state, "merge") != "authorized":
        add_issue(errors, "AUTH_MERGE", "merge is not authorized")

    if gate == "merge":
        if delivery.get("merge") == "completed" or completed_action(indexes, "merge"):
            add_issue(errors, "DELIVERY_ALREADY_COMPLETED", "merge is already recorded as completed; verify the receipt instead of repeating")
        return revision

    if delivery.get("merge") != "completed":
        add_issue(errors, "MERGE_INCOMPLETE", "deploy gate requires a completed merge")
    if authorization_status(state, "deploy") != "authorized":
        add_issue(errors, "AUTH_DEPLOY", "deploy is not authorized")
    recovery = state.get("recovery_strategy", {})
    if not isinstance(recovery, dict) or not all(
        nonempty(recovery.get(field)) for field in ("trigger", "steps", "owner")
    ):
        add_issue(errors, "RECOVERY_STRATEGY", "deploy gate requires trigger, steps, and owner")
    if delivery.get("deploy") == "completed" or completed_action(indexes, "deploy"):
        add_issue(errors, "DELIVERY_ALREADY_COMPLETED", "deploy is already recorded as completed; verify the receipt instead of repeating")
    return revision


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("manifest", type=Path, help="path to task-state.json")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Git repository root")
    parser.add_argument("--gate", choices=GATES, default="record")
    printing = parser.add_mutually_exclusive_group()
    printing.add_argument(
        "--print-revision",
        action="store_true",
        help="print the current base-to-worktree revision token and exit",
    )
    printing.add_argument(
        "--print-sha256",
        metavar="PATH",
        help="print the sha256 of a repository-relative evidence file and exit",
    )
    return parser.parse_args(argv)


def operational_failure(gate: str, code: str, message: str) -> int:
    result = {
        "ok": False,
        "gate": gate,
        "errors": [{"code": code, "message": message}],
        "warnings": [],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        repo = ensure_repository(args.repo)
        if args.print_sha256 is not None:
            path = safe_repo_file(repo, args.print_sha256)
            if path is None or not path.is_file():
                raise ValidationError(f"evidence file must exist inside --repo: {args.print_sha256}")
            print(sha256_file(path))
            return 0

        manifest = args.manifest.resolve()
        if not manifest.is_file():
            raise ValidationError(f"manifest does not exist: {manifest}")
        relative_manifest(repo, manifest)
        with manifest.open("r", encoding="utf-8") as handle:
            state = json.load(handle)
        if not isinstance(state, dict):
            raise ValidationError("manifest root must be a JSON object")

        if args.print_revision:
            print(current_revision(repo, manifest, as_dict(state.get("baseline")).get("git_ref")))
            return 0

        errors, warnings, indexes = validate_record(state, repo, manifest, args.gate)
        revision = add_gate_errors(args.gate, state, repo, manifest, indexes, errors)
        result = {
            "ok": not errors,
            "gate": args.gate,
            "current_revision": revision,
            "errors": errors,
            "warnings": warnings,
            "limits": "Structural consistency is not proof of product success or authorization authenticity.",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if not errors else 1
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        return operational_failure(args.gate, "OPERATIONAL_ERROR", str(exc))
    except Exception as exc:  # keep output machine-readable even for record shapes not anticipated above
        return operational_failure(args.gate, "INTERNAL_ERROR", f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
