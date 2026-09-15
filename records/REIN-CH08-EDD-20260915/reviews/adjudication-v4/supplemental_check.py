#!/usr/bin/env python3
"""Read-only supplemental adapter for the frozen ch08 evaluator."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

EVALUATOR_PATH = Path("/private/tmp/rein-ch08-evaluator-frozen/evaluator.py")
EVALUATOR_SHA256 = "6ed1a9d09fd40871b8e4e0bfed7cb2d2f64a4a3eb9f5ff762bb0566cda6fe86b"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_tree(root: Path) -> str:
    """Hash the current data files deterministically without modifying them."""
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _estimated_json(value: Any) -> int:
    if value is None:
        return 4
    if isinstance(value, bool):
        return 4 if value else 5
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return 8
    if isinstance(value, str):
        return 2 + len(value.encode("utf-8"))
    if isinstance(value, list):
        return 2 + sum(_estimated_json(item) for item in value) + max(0, len(value) - 1)
    if isinstance(value, dict):
        return 2 + sum(2 + len(str(key).encode("utf-8")) + 1 + _estimated_json(item)
                       for key, item in value.items()) + max(0, len(value) - 1)
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def estimated_message(message: dict[str, Any]) -> int:
    total = 8 + len(message["role"].encode("utf-8")) + len(message["content"].encode("utf-8"))
    if "toolCallId" in message and "tool_call_id" in message:
        raise ValueError("CHECK_DUPLICATE_TOOL_CALL_ID_KEYS")
    if "toolCalls" in message and "tool_calls" in message:
        raise ValueError("CHECK_DUPLICATE_TOOL_CALLS_KEYS")
    call_id = message.get("toolCallId", message.get("tool_call_id"))
    calls = message.get("toolCalls", message.get("tool_calls", []))
    total += len(call_id.encode("utf-8")) if call_id is not None else 0
    total += sum(8 + len(call["id"].encode("utf-8")) + len(call["name"].encode("utf-8"))
                 + _estimated_json(call["arguments"])
                 for call in calls)
    return total


def estimated_units(messages: list[dict[str, Any]]) -> int:
    return sum(estimated_message(message) for message in messages)


def load_frozen():
    actual = sha256_file(EVALUATOR_PATH)
    if actual != EVALUATOR_SHA256:
        raise RuntimeError(f"CHECK_EVALUATOR_HASH: expected {EVALUATOR_SHA256}, got {actual}")
    spec = importlib.util.spec_from_file_location("rein_ch08_frozen_evaluator", EVALUATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("CHECK_EVALUATOR_IMPORT")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.estimate = lambda messages: estimated_units(messages)
    return module


def adapted_row(row: dict[str, Any]) -> dict[str, Any]:
    candidate = copy.deepcopy(row)
    for message in candidate.get("messages", []):
        for wire, internal in (("toolCallId", "tool_call_id"), ("toolCalls", "tool_calls")):
            if wire in message and internal in message:
                raise AssertionError("CHECK_DUPLICATE_TOOL_KEYS")
            if wire in message:
                message[internal] = message.pop(wire)
        if (message.get("role") == "tool"
                and message.get("content", "").startswith("[来源:")):
            message["role"] = "user"
    return candidate


def check_run(run_path: Path, data_root: Path, budget: int) -> dict[str, Any]:
    frozen = load_frozen()
    before_hash = sha256_file(run_path)
    run = json.loads(run_path.read_text(encoding="utf-8"))
    if run.get("exit_code") != 0:
        raise AssertionError("CHECK_RUN_EXIT_CODE")
    if run.get("timed_out") is True:
        raise AssertionError("CHECK_RUN_TIMED_OUT")
    try:
        output = json.loads(run["stdout"])
    except (KeyError, json.JSONDecodeError) as exc:
        raise AssertionError(f"CHECK_JSON_OUTPUT: {exc}") from exc
    if output.get("unit") != "estimated-bytes-v1":
        raise AssertionError("CHECK_ROOT_UNIT")
    if output.get("serviceTokens") is not None:
        raise AssertionError("CHECK_ROOT_SERVICE_TOKENS")
    tasks = json.loads((data_root / "tasks.json").read_text(encoding="utf-8"))["tasks"]
    index = json.loads((data_root / "index.json").read_text(encoding="utf-8"))
    rows = output.get("results")
    expected = {(task["id"], strategy) for task in tasks for strategy in frozen.STRATEGIES}
    actual = [(row.get("taskId"), row.get("strategy")) for row in rows] if isinstance(rows, list) else []
    if not isinstance(rows, list) or len(rows) != len(expected) or set(actual) != expected or len(set(actual)) != len(actual):
        raise AssertionError("CHECK_EXACT_4X4")
    for row in rows:
        frozen.check_row(adapted_row(row), tasks, index, {"budget": budget}, data_root)
    after_hash = sha256_file(run_path)
    if before_hash != after_hash:
        raise AssertionError("CHECK_RUN_HASH_CHANGED")
    return {
        "status": "passed",
        "checked_rows": len(rows),
        "run_hash": before_hash,
        "data_hash": sha256_tree(data_root),
        "evaluator_hash": EVALUATOR_SHA256,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--budget", type=int, choices=(0, 2400), required=True)
    args = parser.parse_args(argv)
    run_hash = sha256_file(args.run)
    try:
        result = check_run(args.run, args.data, args.budget)
    except AssertionError as exc:
        result = {
            "status": "failed",
            "run_hash": run_hash,
            "data_hash": sha256_tree(args.data),
            "evaluator_hash": EVALUATOR_SHA256,
            "failed_checks": [{"check_id": str(exc)}],
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1
    except (OSError, RuntimeError, TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        result = {
            "status": "failed",
            "run_hash": run_hash,
            "data_hash": sha256_tree(args.data),
            "evaluator_hash": EVALUATOR_SHA256,
            "failed_checks": [{"check_id": f"CHECK_WRAPPER_{type(exc).__name__}: {exc}"}],
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
