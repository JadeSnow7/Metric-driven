#!/usr/bin/env python3
"""Run and aggregate an explicit REIN chapter evaluation manifest.

The manifest is intentionally declarative: every command that is evidence for
an evaluation must be listed there.  This runner never turns prose, a zero-test
command, or an unverified artifact into a passing result.

Runner matching and reported test counts are provenance checks, not a proof
against a malicious command that impersonates a supported runner; argv and
source bindings must therefore be frozen and reviewed by the calling process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


SUPPORTED_TEST_RUNNERS = {
    "pytest": lambda argv: "pytest" in argv,
    "vitest": lambda argv: "vitest" in argv,
    "cargo-test": lambda argv: len(argv) >= 2 and argv[0] == "cargo" and argv[1] == "test",
    "unittest": lambda argv: "-m" in argv and "unittest" in argv,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_stats(stdout: str, stderr: str, runner: str | None = None) -> dict[str, int | None]:
    """Parse one runner's own summary grammar and add summaries across harnesses."""
    text = f"{stdout}\n{stderr}"
    stats: dict[str, int | None] = {"executed": None, "passed": None, "failed": None, "skipped": None}
    if runner == "cargo-test":
        rows = re.findall(
            r"test result:\s*(?:ok|FAILED)\.\s*(\d+)\s+passed;\s*(\d+)\s+failed;\s*(\d+)\s+ignored",
            text, re.I,
        )
        if rows:
            passed = sum(int(row[0]) for row in rows)
            failed = sum(int(row[1]) for row in rows)
            skipped = sum(int(row[2]) for row in rows)
            stats.update(executed=passed + failed, passed=passed, failed=failed, skipped=skipped)
    elif runner == "unittest":
        runs = [int(value) for value in re.findall(r"\bRan\s+(\d+)\s+tests?\b", text, re.I)]
        skipped = sum(int(value) for value in re.findall(r"\bskipped[= ](\d+)\b", text, re.I))
        failures = sum(int(value) for value in re.findall(r"\bfailures[= ](\d+)\b", text, re.I))
        errors = sum(int(value) for value in re.findall(r"\berrors[= ](\d+)\b", text, re.I))
        if runs:
            skipped = min(skipped, sum(runs))
            failed = failures + errors
            executed = sum(runs) - skipped
            stats.update(executed=executed, skipped=skipped, failed=failed,
                         passed=max(0, executed - failed))
    elif runner == "vitest":
        # Vitest has two summaries; only the line beginning with Tests counts
        # individual tests (the preceding Test Files line counts files).
        lines = [line for line in text.splitlines() if re.match(r"^\s*Tests\b", line, re.I)]
        if lines:
            counts = {name.lower(): int(value) for value, name in re.findall(
                r"(\d+)\s+(passed|failed|skipped)\b", lines[-1], re.I
            )}
            passed, failed, skipped = (counts.get(name, 0) for name in ("passed", "failed", "skipped"))
            stats.update(executed=passed + failed, passed=passed, failed=failed, skipped=skipped)
    elif runner == "pytest":
        # pytest's terminal summary is the line with its duration; do not
        # count names or intermediate progress output.
        lines = [line for line in text.splitlines() if re.search(r"\bin\s+[\d.]+s\b", line, re.I)]
        if lines:
            counts = {name.lower(): int(value) for value, name in re.findall(
                r"(\d+)\s+(passed|failed|skipped)\b", lines[-1], re.I
            )}
            passed, failed, skipped = (counts.get(name, 0) for name in ("passed", "failed", "skipped"))
            stats.update(executed=passed + failed, passed=passed, failed=failed, skipped=skipped)
    return stats


def test_count(stdout: str, stderr: str, runner: str | None = None) -> int | None:
    """Compatibility wrapper: count only after binding the output to a runner."""
    return test_stats(stdout, stderr, runner).get("executed")


def source_fingerprint(root: Path, paths: list[str]) -> tuple[str, list[dict[str, Any]]]:
    root = root.resolve()
    expanded: list[str] = []
    for relative in paths:
        candidate = (root / relative).resolve()
        if candidate.is_dir() and candidate.is_relative_to(root):
            expanded.extend(item.relative_to(root).as_posix() for item in sorted(candidate.rglob("*")) if item.is_file())
        else:
            expanded.append(relative)
    files: list[dict[str, Any]] = []
    for relative in sorted(set(expanded)):
        path = (root / relative).resolve()
        if not path.is_file() or not path.is_relative_to(root):
            files.append({"path": relative, "exists": False, "sha256": None})
            continue
        files.append({"path": relative, "exists": True, "sha256": sha256(path)})
    payload = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest(), files


def _artifact_path(command: dict[str, Any], item: Any, root: Path) -> tuple[Path, str | None]:
    if isinstance(item, str):
        path = (root / item).resolve()
        if not path.is_relative_to(root):
            raise ValueError("artifact path must stay inside manifest root")
        return path, None
    if not isinstance(item, dict) or not isinstance(item.get("path"), str):
        raise ValueError("expected_artifacts entries require a path")
    base = Path(command.get("cwd", "."))
    if not base.is_absolute():
        base = root / base
    path = (base / item["path"]).resolve()
    if not path.is_relative_to(root):
        raise ValueError("artifact path must stay inside manifest root")
    return path, item.get("sha256")


def run_command(command: dict[str, Any], root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": command.get("id"),
        "required": bool(command.get("required", True)),
        "status": "not_run",
        "exit": None,
        "duration_ms": None,
        "stdout": "",
        "stderr": "",
        "artifacts": [],
        "tests_run": None,
        "test_stats": {"executed": None, "passed": None, "failed": None, "skipped": None},
        "reasons": [],
    }
    if command.get("enabled", True) is False:
        result["reasons"].append("command disabled")
        return result
    argv = command.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(part, str) for part in argv):
        result["status"] = "invalid"
        result["reasons"].append("manifest command must provide a non-empty argv list")
        return result
    cwd_value = command.get("cwd", ".")
    cwd = (root / cwd_value).resolve() if not Path(cwd_value).is_absolute() else Path(cwd_value).resolve()
    if not cwd.is_dir():
        result["status"] = "invalid"
        result["reasons"].append(f"cwd does not exist: {cwd}")
        return result
    started = time.monotonic()
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            env={**os.environ, **{str(k): str(v) for k, v in command.get("env", {}).items()}},
            capture_output=True,
            text=True,
            timeout=float(command.get("timeout_seconds", 120)),
            check=False,
        )
        result["exit"] = completed.returncode
        result["stdout"] = completed.stdout
        result["stderr"] = completed.stderr
    except subprocess.TimeoutExpired as exc:
        result["exit"] = None
        result["stdout"] = (exc.stdout or b"").decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        result["stderr"] = (exc.stderr or b"").decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        result["reasons"].append("command timed out")
    except OSError as exc:
        result["reasons"].append(f"command could not run: {exc}")
    result["duration_ms"] = round((time.monotonic() - started) * 1000, 3)
    result["test_stats"] = test_stats(result["stdout"], result["stderr"], command.get("runner"))
    result["tests_run"] = result["test_stats"]["executed"]

    expected_exit = int(command.get("expected_exit", 0))
    if result["exit"] != expected_exit:
        result["reasons"].append(f"exit {result['exit']!r} != expected {expected_exit}")
    for field, label in (("stdout_contains", "stdout"), ("stderr_contains", "stderr")):
        for needle in command.get(field, []):
            if str(needle) not in result[label]:
                result["reasons"].append(f"{label} missing expected text: {needle!r}")
    for item in command.get("expected_artifacts", []):
        try:
            path, expected_hash = _artifact_path(command, item, root)
        except ValueError as exc:
            result["reasons"].append(str(exc))
            continue
        record: dict[str, Any] = {"path": str(path), "exists": path.is_file(), "sha256": None}
        if path.is_file():
            record["sha256"] = sha256(path)
            if expected_hash and record["sha256"] != expected_hash:
                result["reasons"].append(f"artifact hash mismatch: {path}")
        else:
            result["reasons"].append(f"missing expected artifact: {path}")
        result["artifacts"].append(record)
    if command.get("kind") == "test":
        runner = command.get("runner")
        matcher = SUPPORTED_TEST_RUNNERS.get(runner)
        if matcher is None or not matcher(argv):
            result["reasons"].append("test command lacks a recognized real runner binding")
        elif result["tests_run"] is None or result["tests_run"] < 1:
            result["reasons"].append("test command produced no observable tests")
        elif result["test_stats"]["passed"] in (None, 0) or (result["test_stats"]["failed"] or 0) > 0:
            result["reasons"].append("test command has no passing tests or has failures")
        elif result["test_stats"]["executed"] == 0:
            result["reasons"].append("all observed tests were skipped")
    if command.get("require_review", False):
        result["reasons"].append("manual review is unreviewed")
    result["status"] = "passed" if not result["reasons"] else (
        "undetermined" if result["reasons"] == ["manual review is unreviewed"] else "failed"
    )
    return result


def evaluate(manifest_path: Path, output_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest.get("commands"), list):
        raise ValueError("manifest.commands must be a list")
    root = Path(manifest.get("root", manifest_path.parent)).resolve()
    results = [run_command(command, root) for command in manifest["commands"]]
    required = [item for item in results if item["required"]]
    reasons: list[str] = []
    if not results:
        reasons.append("manifest has no commands")
    if not required:
        reasons.append("manifest has no required commands")
    if any(item["status"] not in {"passed", "undetermined"} for item in required):
        reasons.append("one or more required commands did not pass")
    if any(item["status"] == "undetermined" for item in required):
        reasons.append("one or more required commands require manual review")
    source_paths = manifest.get("source_paths")
    if not isinstance(source_paths, list) or not source_paths or not all(isinstance(item, str) for item in source_paths):
        reasons.append("manifest source_paths are required for stale-result detection")
        source_files: list[dict[str, Any]] = []
        actual_source_fingerprint = None
    else:
        actual_source_fingerprint, source_files = source_fingerprint(root, source_paths)
        if manifest.get("source_fingerprint") != actual_source_fingerprint:
            reasons.append("source fingerprint is missing or stale")
    review = manifest.get("review", {})
    technical_reasons = [reason for reason in reasons if "manual review" not in reason]
    if review.get("document_quality") != "reviewed":
        reasons.append("document quality remains unreviewed")
    status = "failed" if technical_reasons else ("undetermined" if reasons else "passed")
    report = {
        "schema_version": "rein-evaluation-v1",
        "manifest": str(manifest_path.resolve()),
        "root": str(root),
        "status": status,
        "reasons": reasons,
        "source_fingerprint": {"expected": manifest.get("source_fingerprint"), "actual": actual_source_fingerprint, "files": source_files},
        "commands": results,
        "review": {"document_quality": review.get("document_quality", "unreviewed")},
        "usage": manifest.get("usage", {"tokens": None, "duration_ms": None}),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = evaluate(args.manifest, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"evaluation error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "output": str(args.output)}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
