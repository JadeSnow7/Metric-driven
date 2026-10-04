#!/usr/bin/env python3
"""Capture and audit the authorization in force before a side effect."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = 1
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _scope_covers(scope: Any, target: Any) -> bool:
    if scope is None:
        return True
    return isinstance(scope, list) and all(isinstance(item, str) and item.strip() for item in scope) and (not scope or target in scope)


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not _UTC.fullmatch(value):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _digest(snapshot: dict[str, Any]) -> str:
    body = {key: value for key, value in snapshot.items() if key != "content_sha256"}
    return hashlib.sha256(_canonical(body)).hexdigest()


def capture_snapshot(state: dict[str, Any], authorization_action: str, target: str, revision: str) -> dict[str, Any]:
    """Return an immutable-in-practice copy of authorization before execution.

    This function only reads the supplied objects.  It never performs or
    records the side effect represented by ``authorization_action``.
    """
    if not isinstance(state, dict) or not isinstance(authorization_action, str) or not authorization_action:
        raise ValueError("state and authorization_action are required")
    if not isinstance(target, str) or not target.strip() or not isinstance(revision, str) or not revision.strip():
        raise ValueError("target and revision are required")
    authorization = state.get("authorization", {}).get(authorization_action) if isinstance(state.get("authorization"), dict) else None
    if not isinstance(authorization, dict) or authorization.get("status") != "authorized":
        raise ValueError(f"authorization.{authorization_action} is not authorized")
    source_id = authorization.get("source_id")
    sources = state.get("sources")
    source = next((item for item in sources if isinstance(item, dict) and item.get("id") == source_id), None) if isinstance(sources, list) else None
    if not isinstance(source_id, str) or not source_id.strip() or not isinstance(source, dict):
        raise ValueError("authorization source_id does not identify a source")
    if not isinstance(source.get("kind"), str) or source.get("kind") not in {"user_requirement", "user_feedback"} or source.get("adoption") != "accepted":
        raise ValueError("authorization source must be an accepted user requirement or feedback")
    if not isinstance(source.get("reference"), str) or not source["reference"].strip() or not isinstance(source.get("summary"), str) or not source["summary"].strip():
        raise ValueError("authorization source reference and summary are required")
    scope = authorization.get("scope")
    if not _scope_covers(scope, target):
        raise ValueError(f"target {target!r} is outside authorization scope")
    snapshot: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "captured_at": _now(),
        "action": authorization_action,
        "target": target,
        "revision": revision,
        "authorization": copy.deepcopy(authorization),
        "source": copy.deepcopy(source),
        # Stable integration fields make the record easy to inspect without
        # discarding the complete copies above.
        "source_id": source_id,
        "scope": copy.deepcopy(scope),
        "source_content": json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    }
    snapshot["content_sha256"] = _digest(snapshot)
    return snapshot


def _issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def audit_snapshot(snapshot: dict[str, Any] | None, action_record: dict[str, Any]) -> list[dict[str, str]]:
    """Audit a historical snapshot without consulting current authorization."""
    if snapshot is None:
        return [_issue("AUTH_SNAPSHOT_UNKNOWN", "authorization snapshot is absent; historical authorization is unknown")]
    errors: list[dict[str, str]] = []
    if not isinstance(snapshot, dict):
        return [_issue("AUTH_SNAPSHOT_INVALID", "authorization snapshot must be an object")]
    if not isinstance(action_record, dict):
        return [_issue("ACTION_RECORD_INVALID", "action record must be an object")]
    if isinstance(snapshot.get("schema_version"), bool) or snapshot.get("schema_version") != SCHEMA_VERSION:
        errors.append(_issue("AUTH_SNAPSHOT_SCHEMA", "unsupported authorization snapshot schema_version"))
    captured = snapshot.get("captured_at")
    if not _valid_timestamp(captured):
        errors.append(_issue("AUTH_SNAPSHOT_TIME", "captured_at must be a UTC RFC3339 timestamp"))
    action = snapshot.get("action")
    if not isinstance(action, str) or not action.strip() or not isinstance(action_record.get("authorization_action"), str) or not action_record.get("authorization_action").strip() or action != action_record.get("authorization_action"):
        errors.append(_issue("AUTH_SNAPSHOT_ACTION", "snapshot action does not match action record"))
    for field in ("target", "revision"):
        if not isinstance(snapshot.get(field), str) or not snapshot.get(field).strip() or not isinstance(action_record.get(field), str) or not action_record.get(field).strip() or snapshot.get(field) != action_record.get(field):
            errors.append(_issue(f"AUTH_SNAPSHOT_{field.upper()}", f"snapshot {field} does not match action record"))
    authorization = snapshot.get("authorization")
    source = snapshot.get("source")
    if not isinstance(authorization, dict) or authorization.get("status") != "authorized":
        errors.append(_issue("AUTH_SNAPSHOT_STATUS", "captured authorization status is not authorized"))
    if not isinstance(source, dict) or not isinstance(source.get("kind"), str) or source.get("kind") not in {"user_requirement", "user_feedback"} or source.get("adoption") != "accepted":
        errors.append(_issue("AUTH_SNAPSHOT_SOURCE", "captured source is not an accepted user requirement or feedback"))
    if not isinstance(source, dict) or not isinstance(source.get("reference"), str) or not source.get("reference", "").strip() or not isinstance(source.get("summary"), str) or not source.get("summary", "").strip():
        errors.append(_issue("AUTH_SNAPSHOT_SOURCE_FIELDS", "captured source needs non-empty reference and summary"))
    expected_source_content = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":")) if isinstance(source, dict) else None
    if snapshot.get("source_content") != expected_source_content:
        errors.append(_issue("AUTH_SNAPSHOT_SOURCE_CONTENT", "captured source content does not match the complete source copy"))
    source_dict = source if isinstance(source, dict) else {}
    authorization_dict = authorization if isinstance(authorization, dict) else {}
    if not isinstance(snapshot.get("source_id"), str) or not snapshot.get("source_id").strip() or snapshot.get("source_id") != source_dict.get("id") or snapshot.get("source_id") != authorization_dict.get("source_id"):
        errors.append(_issue("AUTH_SNAPSHOT_SOURCE_ID", "captured source id is inconsistent"))
    scope = authorization.get("scope") if isinstance(authorization, dict) else None
    if "scope" in snapshot and snapshot.get("scope") != scope:
        errors.append(_issue("AUTH_SNAPSHOT_SCOPE_COPY", "top-level scope disagrees with captured authorization scope"))
    if isinstance(snapshot.get("source"), dict) and snapshot.get("source_id") != snapshot["source"].get("id"):
        errors.append(_issue("AUTH_SNAPSHOT_SOURCE_COPY", "top-level source id disagrees with captured source"))
    if not _scope_covers(scope, snapshot.get("target")):
        errors.append(_issue("AUTH_SNAPSHOT_SCOPE", "action target is outside captured authorization scope"))
    expected = snapshot.get("content_sha256")
    try:
        digest_matches = isinstance(expected, str) and bool(re.fullmatch(r"[0-9a-f]{64}", expected)) and expected == _digest(snapshot)
    except (TypeError, ValueError, OverflowError):
        digest_matches = False
    if not digest_matches:
        errors.append(_issue("AUTH_SNAPSHOT_HASH", "authorization snapshot integrity digest does not match"))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True, type=argparse.FileType("r", encoding="utf-8"))
    parser.add_argument("--action", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args(argv)
    try:
        state = json.load(args.state)
        snapshot = capture_snapshot(state, args.action, args.target, args.revision)
        print(json.dumps(snapshot, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"authorization snapshot failed: {exc}", file=__import__("sys").stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
