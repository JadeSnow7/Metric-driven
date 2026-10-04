"""Schema 1.3 Spec binding and structural checks."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

SPEC_VERSION = "1.3"
SPEC_FIELDS = ("version", "authority", "source_ids", "goal_ref", "scope_ref", "constraints", "exceptions", "conditions", "contracts", "open_items")
_RUNTIME_FIELDS = {"status", "evidence_ids", "implementation_task_ids"}


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"cannot canonicalize Spec data: {exc}") from exc


def _path(value: Any) -> str | None:
    if not isinstance(value, str) or not value or value != value.strip():
        return None
    p = Path(value)
    if p.is_absolute() or not p.parts or any(part in ("", ".", "..") for part in p.parts):
        return None
    normalized = p.as_posix()
    if normalized != value or normalized in ("", ".") or normalized.endswith("/"):
        return None
    return normalized


def _paths(values: Any) -> list[str] | None:
    if not isinstance(values, list):
        return None
    result = []
    for value in values:
        # Mapping keys are paths; embedded path objects are not accepted.
        normalized = _path(value)
        if normalized is None:
            return None
        result.append(normalized)
    return result


def _unique(values: list[str] | None) -> list[str]:
    return list(dict.fromkeys(values or []))


def deliverable_paths(spec: dict[str, Any]) -> list[str]:
    if not isinstance(spec, dict) or not isinstance(spec.get("conditions"), list):
        return []
    result: list[str] = []
    for condition in spec["conditions"]:
        if isinstance(condition, dict):
            paths = _paths(condition.get("deliverables"))
            if paths is not None:
                result.extend(paths)
    return _unique(result)


def contract_paths(spec: dict[str, Any]) -> list[str]:
    return _unique(_paths(spec.get("contracts"))) if isinstance(spec, dict) else []


def receipt_paths(state: dict[str, Any]) -> list[str]:
    """Return exact runtime receipt files from the complete state object."""
    binding = state.get("binding") if isinstance(state, dict) else None
    return _unique(_paths(binding.get("receipt_paths"))) if isinstance(binding, dict) else []


def _resolve_ref(state: dict[str, Any], ref: Any) -> Any:
    if not isinstance(ref, str) or ref.count(".") != 1:
        raise ValueError("Spec references must be a root.field reference")
    root, field = ref.split(".")
    value = state.get(root)
    if not isinstance(value, dict) or field not in value:
        raise ValueError(f"Spec reference does not resolve: {ref}")
    return value[field]


def _normative_object(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("normative object must be an object")
    return {key: copy.deepcopy(item) for key, item in value.items() if key not in _RUNTIME_FIELDS}


def _repo_file(repo: Path, rel: str) -> Path:
    root = repo.resolve()
    candidate = root / rel
    current = root
    for part in Path(rel).parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"path contains a symlink parent: {rel}")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes repository: {rel}") from exc
    return candidate


def spec_projection(state: dict[str, Any], repo: Path | None = None) -> dict[str, Any]:
    if not isinstance(state, dict) or state.get("schema_version") != SPEC_VERSION:
        raise ValueError("schema 1.3 state is required")
    spec = state.get("spec")
    if not isinstance(spec, dict):
        raise ValueError("schema 1.3 requires state.spec")
    if not isinstance(spec.get("conditions"), list):
        raise ValueError("spec.conditions must be a list")
    if _paths(spec.get("contracts")) is None:
        raise ValueError("spec.contracts must be a list of paths")
    if any(not isinstance(item, dict) for item in spec["conditions"]):
        raise ValueError("spec.conditions entries must be objects")
    if not isinstance(state.get("main_tasks"), list) or not isinstance(state.get("metrics"), list):
        raise ValueError("state.main_tasks and state.metrics must be lists")
    if not isinstance(state.get("binding"), dict):
        raise ValueError("schema 1.3 requires state.binding")
    receipts = _paths(state["binding"].get("receipt_paths"))
    if receipts is None:
        raise ValueError("binding.receipt_paths must be a list of paths")
    baseline = state.get("baseline")
    if not isinstance(baseline, dict):
        raise ValueError("state.baseline must be an object")
    projected: dict[str, Any] = {
        "spec": copy.deepcopy(spec),
        "main_tasks": [_normative_object(item) for item in state["main_tasks"]],
        "metrics": [_normative_object(item) for item in state["metrics"]],
        "goal_ref_value": _resolve_ref(state, spec.get("goal_ref")),
        "scope_ref_value": _resolve_ref(state, spec.get("scope_ref")),
        "binding": {"receipt_paths": _unique(receipts)},
        "baseline_declarations": {"foreign_paths": copy.deepcopy(baseline.get("foreign_paths", [])), "external_inputs": copy.deepcopy(baseline.get("external_inputs", []))},
    }
    if repo is not None:
        if not isinstance(repo, Path):
            raise ValueError("repo must be a pathlib.Path")
        files: dict[str, Any] = {}
        for rel in contract_paths(spec):
            path = _repo_file(repo, rel)
            if path.is_file() and not path.is_symlink():
                files[rel] = {"exists": True, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            else:
                files[rel] = {"exists": False, "sha256": None}
        projected["contract_files"] = files
    return projected


def spec_digest(state: dict[str, Any], repo: Path | None = None) -> str:
    return hashlib.sha256(_canonical(spec_projection(state, repo))).hexdigest()


def _issue(issues: list[dict[str, str]], code: str, message: str) -> None:
    issues.append({"code": code, "message": message})


def _declared_paths(value: Any, repo: Path, require_exists: bool) -> tuple[list[str], list[dict[str, str]]]:
    paths = _paths(value)
    issues: list[dict[str, str]] = []
    if paths is None:
        _issue(issues, "SPEC_PATHS", "paths must be a list of canonical repository-relative files")
        return [], issues
    for rel in paths:
        path = _repo_file(repo, rel)
        if path.is_symlink() or (path.exists() and not path.is_file()):
            _issue(issues, "SPEC_PATH_FILE", f"path must be an exact file: {rel}")
        elif require_exists and not path.is_file():
            _issue(issues, "SPEC_CONTRACT_MISSING", f"contract file does not exist: {rel}")
    return paths, issues


def validate_spec(state: dict[str, Any], repo: Path) -> list[dict[str, str]]:
    """Return structural issues, including malformed data, without traceback."""
    issues: list[dict[str, str]] = []
    try:
        if not isinstance(state, dict) or state.get("schema_version") != SPEC_VERSION:
            return [{"code": "SPEC_SCHEMA", "message": "schema 1.3 is required for Spec binding"}]
        spec = state.get("spec")
        if not isinstance(spec, dict):
            return [{"code": "SPEC_MISSING", "message": "schema 1.3 requires state.spec"}]
        for field in SPEC_FIELDS:
            if field not in spec:
                _issue(issues, "SPEC_FIELD_MISSING", f"spec.{field} is required")
        for field in ("constraints", "exceptions", "open_items"):
            if field in spec and not isinstance(spec[field], list):
                _issue(issues, "SPEC_FIELD_TYPE", f"spec.{field} must be a list")
        if isinstance(spec.get("open_items"), list) and spec["open_items"]:
            _issue(issues, "SPEC_OPEN_ITEMS_PENDING", "non-empty spec.open_items keeps implementation not ready")
        if not isinstance(spec.get("version"), str) or not spec.get("version", "").strip():
            _issue(issues, "SPEC_VERSION", "spec.version must be non-empty")
        sources = state.get("sources")
        accepted = {s.get("id") for s in sources if isinstance(s, dict) and s.get("adoption") == "accepted"} if isinstance(sources, list) else set()
        source_ids = spec.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids or any(s not in accepted for s in source_ids):
            _issue(issues, "SPEC_SOURCES", "spec.source_ids must reference accepted sources")
        authority = spec.get("authority")
        if authority != "state.spec":
            authority_paths, path_issues = _declared_paths([authority], repo, True)
            issues.extend(path_issues)
            if authority_paths and authority_paths[0] not in set(contract_paths(spec)):
                _issue(issues, "SPEC_AUTHORITY", "file authority must also be listed in spec.contracts")
        if spec.get("goal_ref") != "discovery.expected_outcome":
            _issue(issues, "SPEC_REFERENCE", "spec.goal_ref must reference discovery.expected_outcome")
        if spec.get("scope_ref") != "discovery.scope":
            _issue(issues, "SPEC_REFERENCE", "spec.scope_ref must reference discovery.scope")
        metrics_raw = state.get("metrics")
        metrics = {m.get("id"): m for m in metrics_raw if isinstance(m, dict)} if isinstance(metrics_raw, list) else {}
        conditions = spec.get("conditions")
        if not isinstance(conditions, list) or not conditions:
            _issue(issues, "SPEC_CONDITIONS", "spec.conditions must be a non-empty list")
            conditions = []
        seen: set[str] = set()
        for condition in conditions:
            if not isinstance(condition, dict):
                _issue(issues, "SPEC_CONDITION", "each condition must be an object")
                continue
            cid = condition.get("id")
            if not isinstance(cid, str) or not cid.strip() or cid in seen:
                _issue(issues, "SPEC_CONDITION_ID", "each condition needs a unique non-empty id")
            if isinstance(cid, str):
                seen.add(cid)
            mids = condition.get("metric_ids")
            if not isinstance(mids, list) or not mids or any(mid not in metrics for mid in mids):
                _issue(issues, "SPEC_METRIC_BINDING", f"{cid} must reference existing metric_ids")
            elif not any(metrics[mid].get("kind") in {"mandatory_gate", "non_regression"} for mid in mids):
                _issue(issues, "SPEC_METRIC_BINDING", f"{cid} must include mandatory_gate or non_regression")
            paths = _paths(condition.get("deliverables"))
            if paths is None or not paths:
                _issue(issues, "SPEC_DELIVERABLES", f"{cid} must list concrete deliverable files")
            else:
                _, path_issues = _declared_paths(paths, repo, False)
                issues.extend(path_issues)
        contracts, path_issues = _declared_paths(spec.get("contracts"), repo, True)
        issues.extend(path_issues)
        binding = state.get("binding")
        if not isinstance(binding, dict):
            _issue(issues, "SPEC_BINDING", "state.binding is required")
            receipts = []
        else:
            receipts, path_issues = _declared_paths(binding.get("receipt_paths"), repo, False)
            issues.extend(path_issues)
        deliverables = set(deliverable_paths(spec))
        if set(contracts) & set(receipts):
            _issue(issues, "SPEC_PATH_CONFLICT", "contract paths cannot be receipt paths")
        if deliverables & set(receipts):
            _issue(issues, "SPEC_PATH_CONFLICT", "deliverables cannot be receipt paths")
        baseline = state.get("baseline")
        foreign = baseline.get("foreign_paths", []) if isinstance(baseline, dict) else []
        if isinstance(foreign, list):
            foreign_paths = {p for p in (_path(v) for v in foreign) if p is not None}
            def overlaps_foreign(path: str) -> bool:
                return any(path == item or path.startswith(item + "/") or item.startswith(path + "/") for item in foreign_paths)
            if any(overlaps_foreign(path) for path in deliverables | set(contracts)):
                _issue(issues, "SPEC_PATH_CONFLICT", "foreign paths cannot be explicit deliverables or contracts")
    except (TypeError, ValueError, OSError) as exc:
        _issue(issues, "SPEC_MALFORMED", str(exc))
    return issues
