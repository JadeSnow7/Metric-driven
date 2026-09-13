#!/usr/bin/env python3
"""Read-only consistency and delivery-gate checks for task-state.json.

This tool intentionally cannot prove product success or authorization truth. It
checks only the record, referenced local evidence, and observable Git state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


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

DISCOVERY_STATES = {"needs_clarification", "exploring", "ready"}
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
METRIC_KINDS = {"mandatory_gate", "improvement_target", "non_regression"}
SOURCE_KINDS = {
    "user_requirement",
    "user_feedback",
    "reproduced_defect",
    "external_material",
    "agent_inference",
    "implementation_adjustment",
}
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


class ValidationError(RuntimeError):
    """Operational failure while reading the repository."""


def run_git(repo: Path, args: list[str]) -> bytes:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=env,
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


def revision_metadata_paths(repo: Path, manifest: Path) -> list[str]:
    """Return fixed task-record paths excluded from behavioral fingerprints."""

    manifest_rel = relative_manifest(repo, manifest)
    parent = Path(manifest_rel).parent
    if parent == Path("."):
        return [manifest_rel]
    candidates = (
        Path(manifest_rel),
        parent / "index.md",
        parent / "task-summary.md",
        parent / "work-log.md",
        parent / "handoffs",
    )
    return [candidate.as_posix() for candidate in candidates]


def is_revision_metadata(path: str, excluded: list[str]) -> bool:
    return any(path == item or path.startswith(f"{item}/") for item in excluded)


def current_revision(repo: Path, manifest: Path, base_ref: str) -> str:
    """Hash the base-to-worktree patch while excluding the manifest itself."""

    if not isinstance(base_ref, str) or not base_ref.strip():
        raise ValidationError("baseline.git_ref is required to compute a revision")
    base = run_git(repo, ["rev-parse", "--verify", f"{base_ref}^{{commit}}"]).decode().strip()
    excluded = revision_metadata_paths(repo, manifest)
    pathspecs = [".", *(f":(top,exclude){item}" for item in excluded)]
    diff = run_git(
        repo,
        ["diff", "--binary", "--no-ext-diff", "--no-textconv", base, "--", *pathspecs],
    )
    untracked_raw = run_git(repo, ["ls-files", "--others", "--exclude-standard", "-z"])
    untracked = sorted(
        item.decode("utf-8", errors="surrogateescape")
        for item in untracked_raw.split(b"\0")
        if item
    )
    untracked = [item for item in untracked if not is_revision_metadata(item, excluded)]

    if not diff and not untracked:
        return f"commit:{base}"

    digest = hashlib.sha256()
    digest.update(b"evidence-driven-development/revision-v1\0")
    digest.update(base.encode("ascii"))
    digest.update(b"\0tracked-diff\0")
    digest.update(diff)
    for rel in untracked:
        path = repo / rel
        digest.update(b"\0untracked\0")
        digest.update(rel.encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        if path.is_symlink():
            digest.update(b"symlink\0")
            digest.update(os.readlink(path).encode("utf-8", errors="surrogateescape"))
        elif path.is_file():
            digest.update(b"file\0")
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
        else:
            digest.update(b"other\0")
    return f"patch:{base}:{digest.hexdigest()}"


def git_worktree_clean(repo: Path) -> bool:
    return not run_git(repo, ["status", "--porcelain=v1", "--untracked-files=all"])


def changed_paths(repo: Path, manifest: Path, base_ref: str) -> list[str]:
    """Return task-worktree changes since base, excluding the state manifest."""

    base = run_git(repo, ["rev-parse", "--verify", f"{base_ref}^{{commit}}"]).decode().strip()
    manifest_rel = relative_manifest(repo, manifest)
    exclude = f":(top,exclude){manifest_rel}"
    tracked_raw = run_git(
        repo,
        ["diff", "--name-only", "-z", "--no-ext-diff", base, "--", ".", exclude],
    )
    untracked_raw = run_git(repo, ["ls-files", "--others", "--exclude-standard", "-z"])
    values = {
        item.decode("utf-8", errors="surrogateescape")
        for raw in (tracked_raw, untracked_raw)
        for item in raw.split(b"\0")
        if item
    }
    values.discard(manifest_rel)
    return sorted(values)


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
        add_issue(errors, "TYPE_LIST", f"{owner} references must be a list")
        return
    for ref in refs:
        if ref not in target:
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


def validate_record(
    state: dict[str, Any], repo: Path, manifest: Path
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, dict[str, Any]]]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    require_fields(
        state,
        (
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
        ),
        "root",
        errors,
    )
    if state.get("schema_version") != "1.0":
        add_issue(errors, "SCHEMA_VERSION", "schema_version must be '1.0'")

    indexes = {key: index_items(state, key, errors) for key in ID_PREFIXES}
    sources = indexes["sources"]
    main_tasks = indexes["main_tasks"]
    metrics = indexes["metrics"]
    implementation_tasks = indexes["implementation_tasks"]
    evidence = indexes["evidence"]
    changes = indexes["changes"]
    decisions = indexes["decisions"]

    task = state.get("task", {})
    require_fields(task, ("id", "title", "mode", "status", "source_ids"), "task", errors)
    require_refs("task.source_ids", task.get("source_ids", []), sources, errors, "CROSSREF_SOURCE")

    discovery = state.get("discovery", {})
    require_fields(discovery, ("status",), "discovery", errors)
    discovery_status = discovery.get("status")
    if discovery_status not in DISCOVERY_STATES:
        add_issue(errors, "DISCOVERY_STATUS", f"invalid discovery.status {discovery_status!r}")
    if discovery_status == "ready":
        for field in ("user", "scenario", "problem", "expected_outcome", "scope", "acceptable_result"):
            if not nonempty(discovery.get(field)):
                add_issue(errors, "DISCOVERY_FIELD_EMPTY", f"discovery.{field} is required when ready")

    for source_id, source in sources.items():
        require_fields(source, ("kind", "reference", "summary", "adoption"), source_id, errors)
        if source.get("kind") not in SOURCE_KINDS:
            add_issue(errors, "SOURCE_KIND", f"{source_id} has invalid kind")
        if source.get("adoption") not in ADOPTION_STATES:
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
        for metric_id in main.get("metric_ids", []):
            if metric_id in metrics and metrics[metric_id].get("main_task_id") != main_id:
                add_issue(errors, "CROSSREF_MAIN_TASK", f"{main_id} includes metric owned by another main task: {metric_id}")
        for implementation_id in main.get("implementation_task_ids", []):
            if (
                implementation_id in implementation_tasks
                and implementation_tasks[implementation_id].get("main_task_id") != main_id
            ):
                add_issue(
                    errors,
                    "CROSSREF_MAIN_TASK",
                    f"{main_id} includes implementation task owned by another main task: {implementation_id}",
                )
        if main.get("status") not in TASK_STATES:
            add_issue(errors, "TASK_STATUS", f"{main_id} has invalid status")
        if not main.get("source_ids"):
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
        if metric.get("main_task_id") not in main_tasks:
            add_issue(errors, "CROSSREF_MAIN_TASK", f"{metric_id} references missing main task")
        elif metric_id not in main_tasks[metric["main_task_id"]].get("metric_ids", []):
            add_issue(errors, "CROSSREF_MAIN_TASK", f"{metric_id} is absent from its main task metric_ids")
        if metric.get("kind") not in METRIC_KINDS:
            add_issue(errors, "METRIC_KIND", f"{metric_id} has invalid kind")
        if metric.get("status") not in VERIFY_STATES:
            add_issue(errors, "VERIFY_STATUS", f"{metric_id} has invalid status")
        require_refs(f"{metric_id}.evidence_ids", metric.get("evidence_ids", []), evidence, errors, "CROSSREF_EVIDENCE")
        for field in ("name", "baseline", "target", "method", "environment_data"):
            if not nonempty(metric.get(field)):
                add_issue(errors, "METRIC_FIELD_EMPTY", f"{metric_id}.{field} must not be empty")
        if metric.get("kind") == "improvement_target" and metric.get("status") == "failed":
            decision_id = metric.get("decision_id")
            if decision_id not in decisions:
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
        if item.get("main_task_id") not in main_tasks:
            add_issue(errors, "CROSSREF_MAIN_TASK", f"{implementation_id} references missing main task")
        elif implementation_id not in main_tasks[item["main_task_id"]].get("implementation_task_ids", []):
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
        for metric_id in item.get("acceptance", []):
            if metric_id in metrics and metrics[metric_id].get("main_task_id") != item.get("main_task_id"):
                add_issue(
                    errors,
                    "IMPLEMENTATION_METRIC_SCOPE",
                    f"{implementation_id} acceptance references another main task's metric: {metric_id}",
                )
        if item.get("status") not in TASK_STATES:
            add_issue(errors, "TASK_STATUS", f"{implementation_id} has invalid status")
        for field in ("scope", "file_scope", "owner"):
            if not nonempty(item.get(field)):
                add_issue(errors, "IMPLEMENTATION_FIELD_EMPTY", f"{implementation_id}.{field} must not be empty")

    revision: str | None = None
    if evidence or changes:
        try:
            revision = current_revision(repo, manifest, state.get("baseline", {}).get("git_ref", ""))
        except ValidationError as exc:
            add_issue(errors, "REVISION_UNAVAILABLE", str(exc))

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
        if item.get("status") not in EVIDENCE_STATES:
            add_issue(errors, "EVIDENCE_STATUS", f"{evidence_id} has invalid status")
        if item.get("result") not in VERIFY_STATES:
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
        if not nonempty(item.get("paths")):
            add_issue(errors, "CHANGE_PATHS_EMPTY", f"{change_id}.paths must not be empty")
        elif isinstance(item.get("paths"), list):
            for path in item["paths"]:
                if normalized_declared_path(path) is None:
                    add_issue(errors, "CHANGE_PATH", f"{change_id} has unsafe or empty path {path!r}")
        if item.get("status") not in {"proposed", "implemented", "reviewed", "reverted"}:
            add_issue(errors, "CHANGE_STATUS", f"{change_id} has invalid status")
        if revision is not None and item.get("status") == "reviewed" and item.get("revision") != revision:
            add_issue(errors, "CHANGE_STALE", f"{change_id} revision does not match current repository state")

    overall = state.get("overall_acceptance", {})
    require_fields(overall, ("metric_ids", "evidence_ids", "status"), "overall_acceptance", errors)
    require_refs("overall_acceptance.metric_ids", overall.get("metric_ids", []), metrics, errors, "CROSSREF_METRIC")
    require_refs("overall_acceptance.evidence_ids", overall.get("evidence_ids", []), evidence, errors, "CROSSREF_EVIDENCE")
    if overall.get("status") not in VERIFY_STATES:
        add_issue(errors, "VERIFY_STATUS", "overall_acceptance.status is invalid")

    baseline = state.get("baseline", {})
    require_fields(baseline, ("git_ref", "worktree_status", "ownership", "prepared_at"), "baseline", errors)
    if baseline.get("worktree_status") not in {"clean", "dirty_dependency_confirmed", "unknown"}:
        add_issue(errors, "BASELINE_STATUS", "baseline.worktree_status is invalid")
    if not nonempty(baseline.get("ownership")):
        add_issue(errors, "BASELINE_OWNERSHIP", "baseline.ownership must not be empty")

    authorization = state.get("authorization", {})
    require_fields(authorization, AUTH_ACTIONS, "authorization", errors)
    for action in AUTH_ACTIONS:
        entry = authorization.get(action, {})
        require_fields(entry, ("status", "source_id"), f"authorization.{action}", errors)
        if entry.get("status") not in AUTH_STATES:
            add_issue(errors, "AUTH_STATUS", f"authorization.{action}.status is invalid")
        if entry.get("status") == "authorized":
            source_id = entry.get("source_id")
            source = sources.get(source_id)
            if source is None:
                add_issue(errors, "AUTH_SOURCE", f"authorized {action} needs an existing source_id")
            elif source.get("kind") not in {"user_requirement", "user_feedback"}:
                add_issue(errors, "AUTH_SOURCE", f"authorized {action} must cite a user instruction")

    delivery = state.get("delivery", {})
    require_fields(delivery, DELIVERY_KEYS, "delivery", errors)
    for key in DELIVERY_KEYS:
        if delivery.get(key) not in DELIVERY_STATES:
            add_issue(errors, "DELIVERY_STATUS", f"delivery.{key} has invalid status")

    action_keys: set[str] = set()
    for action_id, item in indexes["actions"].items():
        require_fields(item, ("kind", "status", "authorization_action", "idempotency_key", "receipt"), action_id, errors)
        if item.get("status") not in ACTION_STATES:
            add_issue(errors, "ACTION_STATUS", f"{action_id} has invalid status")
        auth_action = item.get("authorization_action")
        if auth_action not in AUTH_ACTIONS:
            add_issue(errors, "ACTION_AUTH", f"{action_id}.authorization_action is invalid")
        key = item.get("idempotency_key")
        if not nonempty(key):
            add_issue(errors, "ACTION_KEY", f"{action_id}.idempotency_key must not be empty")
        elif key in action_keys:
            add_issue(errors, "ACTION_KEY_DUPLICATE", f"duplicate idempotency_key {key!r}")
        else:
            action_keys.add(key)
        if item.get("status") == "completed" and not nonempty(item.get("receipt")):
            add_issue(errors, "ACTION_RECEIPT", f"completed {action_id} needs a receipt")

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

    discovery = state.get("discovery", {})
    main_tasks = indexes["main_tasks"]
    metrics = indexes["metrics"]
    evidence = indexes["evidence"]
    changes = indexes["changes"]
    implementation_tasks = indexes["implementation_tasks"]
    baseline = state.get("baseline", {})
    authorization = state.get("authorization", {})
    delivery = state.get("delivery", {})
    overall = state.get("overall_acceptance", {})

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
    if baseline.get("worktree_status") != "clean":
        add_issue(errors, "BASELINE_NOT_CLEAN", "implementation needs a recorded clean task worktree")
    try:
        run_git(repo, ["rev-parse", "--verify", f"{baseline.get('git_ref', '')}^{{commit}}"])
    except ValidationError as exc:
        add_issue(errors, "BASELINE_UNRESOLVED", str(exc))

    if gate == "implementation":
        return None

    try:
        revision = current_revision(repo, manifest, baseline.get("git_ref", ""))
    except ValidationError as exc:
        add_issue(errors, "REVISION_UNAVAILABLE", str(exc))
        revision = None

    for metric_id, metric in metrics.items():
        kind = metric.get("kind")
        status = metric.get("status")
        if kind in {"mandatory_gate", "non_regression"} and status != "passed":
            add_issue(errors, "MANDATORY_GATE", f"{metric_id} ({kind}) is {status!r}, not passed")
        if kind == "improvement_target" and status == "undetermined":
            add_issue(errors, "IMPROVEMENT_UNDETERMINED", f"{metric_id} improvement target is undetermined")
        if kind == "improvement_target" and status == "failed" and metric.get("decision_id") not in indexes["decisions"]:
            add_issue(errors, "IMPROVEMENT_UNACCEPTED", f"{metric_id} failed without a recorded decision")
        if status in {"passed", "failed"} and not metric.get("evidence_ids"):
            add_issue(errors, "METRIC_EVIDENCE_MISSING", f"{metric_id} is assessed without evidence")
        for evidence_id in metric.get("evidence_ids", []):
            item = evidence.get(evidence_id, {})
            if item.get("status") != "current" or item.get("revision") != revision:
                add_issue(errors, "METRIC_EVIDENCE_NOT_CURRENT", f"{metric_id} evidence {evidence_id} is not current")
            if status == "passed" and item.get("result") != "passed":
                add_issue(errors, "METRIC_EVIDENCE_RESULT", f"{metric_id} is passed but {evidence_id} is not")

    for implementation_id, item in implementation_tasks.items():
        if item.get("status") != "verified":
            add_issue(errors, "IMPLEMENTATION_NOT_VERIFIED", f"{implementation_id} is not verified")
        if item.get("status") == "verified" and not item.get("evidence_ids"):
            add_issue(errors, "IMPLEMENTATION_EVIDENCE_MISSING", f"{implementation_id} is verified without evidence")
        for evidence_id in item.get("evidence_ids", []):
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
            actual_paths = changed_paths(repo, manifest, baseline.get("git_ref", ""))
        except ValidationError as exc:
            add_issue(errors, "CHANGED_PATHS_UNAVAILABLE", str(exc))
        else:
            declared_paths = {
                normalized
                for item in changes.values()
                if item.get("status") == "reviewed"
                for value in item.get("paths", [])
                if (normalized := normalized_declared_path(value)) is not None
            }
            for path in actual_paths:
                if not any(path_is_covered(path, declared) for declared in declared_paths):
                    add_issue(errors, "CHANGED_PATH_UNREVIEWED", f"changed path is not covered by a reviewed CHG-*: {path}")
    if overall.get("status") != "passed":
        add_issue(errors, "OVERALL_NOT_PASSED", "overall end-to-end acceptance is not passed")
    if not overall.get("evidence_ids"):
        add_issue(errors, "OVERALL_EVIDENCE_MISSING", "overall acceptance needs evidence")
    for evidence_id in overall.get("evidence_ids", []):
        item = evidence.get(evidence_id, {})
        if item.get("status") != "current" or item.get("revision") != revision or item.get("result") != "passed":
            add_issue(errors, "OVERALL_EVIDENCE_NOT_CURRENT", f"overall evidence {evidence_id} is not current and passed")
    if authorization.get("commit", {}).get("status") != "authorized":
        add_issue(errors, "AUTH_COMMIT", "commit is not authorized")

    if gate == "local-commit":
        if delivery.get("local_commit") == "completed":
            add_issue(errors, "DELIVERY_ALREADY_COMPLETED", "local commit is already recorded as completed; verify before repeating")
        return revision

    if delivery.get("local_commit") != "completed":
        add_issue(errors, "LOCAL_COMMIT_INCOMPLETE", "push gate requires a completed local commit")
    if authorization.get("push", {}).get("status") != "authorized":
        add_issue(errors, "AUTH_PUSH", "push is not authorized")
    try:
        if not git_worktree_clean(repo):
            add_issue(errors, "WORKTREE_DIRTY", "push gate requires a clean worktree")
    except ValidationError as exc:
        add_issue(errors, "WORKTREE_UNAVAILABLE", str(exc))

    if gate == "push":
        if delivery.get("push") == "completed" or any(
            item.get("kind") == "push" and item.get("status") == "completed"
            for item in indexes["actions"].values()
        ):
            add_issue(errors, "DELIVERY_ALREADY_COMPLETED", "push is already recorded as completed; verify the receipt instead of repeating")
        return revision

    if delivery.get("push") != "completed":
        add_issue(errors, "PUSH_INCOMPLETE", "merge gate requires a completed push")
    if delivery.get("remote_ci") != "passed":
        add_issue(errors, "REMOTE_CI", "merge gate requires remote CI to have actually passed")
    if authorization.get("merge", {}).get("status") != "authorized":
        add_issue(errors, "AUTH_MERGE", "merge is not authorized")

    if gate == "merge":
        if delivery.get("merge") == "completed" or any(
            item.get("kind") == "merge" and item.get("status") == "completed"
            for item in indexes["actions"].values()
        ):
            add_issue(errors, "DELIVERY_ALREADY_COMPLETED", "merge is already recorded as completed; verify the receipt instead of repeating")
        return revision

    if delivery.get("merge") != "completed":
        add_issue(errors, "MERGE_INCOMPLETE", "deploy gate requires a completed merge")
    if authorization.get("deploy", {}).get("status") != "authorized":
        add_issue(errors, "AUTH_DEPLOY", "deploy is not authorized")
    recovery = state.get("recovery_strategy", {})
    if not isinstance(recovery, dict) or not all(
        nonempty(recovery.get(field)) for field in ("trigger", "steps", "owner")
    ):
        add_issue(errors, "RECOVERY_STRATEGY", "deploy gate requires trigger, steps, and owner")
    if delivery.get("deploy") == "completed" or any(
        item.get("kind") == "deploy" and item.get("status") == "completed"
        for item in indexes["actions"].values()
    ):
        add_issue(errors, "DELIVERY_ALREADY_COMPLETED", "deploy is already recorded as completed; verify the receipt instead of repeating")
    return revision


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="path to task-state.json")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Git repository root")
    parser.add_argument(
        "--gate",
        choices=("record", "implementation", "local-commit", "push", "merge", "deploy"),
        default="record",
    )
    parser.add_argument(
        "--print-revision",
        action="store_true",
        help="print the current base-to-worktree revision token and exit",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        repo = ensure_repository(args.repo)
        manifest = args.manifest.resolve()
        if not manifest.is_file():
            raise ValidationError(f"manifest does not exist: {manifest}")
        relative_manifest(repo, manifest)
        with manifest.open("r", encoding="utf-8") as handle:
            state = json.load(handle)
        if not isinstance(state, dict):
            raise ValidationError("manifest root must be a JSON object")

        if args.print_revision:
            print(current_revision(repo, manifest, state.get("baseline", {}).get("git_ref", "")))
            return 0

        errors, warnings, indexes = validate_record(state, repo, manifest)
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
        result = {
            "ok": False,
            "gate": args.gate,
            "errors": [{"code": "OPERATIONAL_ERROR", "message": str(exc)}],
            "warnings": [],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
