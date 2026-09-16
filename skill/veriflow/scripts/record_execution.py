#!/usr/bin/env python3
"""Run one command and write an evidence record of what actually happened."""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_validator() -> ModuleType:
    """Load the sibling validate_task.py so both tools share one revision algorithm."""

    path = Path(__file__).resolve().with_name("validate_task.py")
    spec = importlib.util.spec_from_file_location("veriflow_validate_task", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    return module


def load_spec_contract() -> ModuleType:
    path = Path(__file__).resolve().with_name("spec_contract.py")
    spec = importlib.util.spec_from_file_location("veriflow_spec_contract", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def relative_to(path: Path, root: Path | None) -> str | None:
    if root is None:
        return None
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return None


def input_declaration(validator: ModuleType, repo: Path, state: dict, path: Path, kind: str) -> tuple[str, dict[str, str]]:
    """Return the portable input key and the declaration shared with validation."""
    resolved = path.resolve()
    rel = relative_to(resolved, repo)
    if kind in {"source", "test"} and rel is None:
        raise ValueError(f"{kind} input must be inside repository: {path}")
    if rel is None:
        allowed = validator.external_input_paths(state).get(str(resolved))
        if allowed is None:
            raise ValueError(f"external fixture is not declared in baseline.external_inputs: {resolved}")
        for field in ("sha256", "identity", "reproduction"):
            if not isinstance(allowed.get(field), str) or not allowed[field].strip():
                raise ValueError(f"external fixture declaration needs non-empty {field}: {resolved}")
        actual = digest(resolved)
        if allowed.get("sha256") != actual:
            raise ValueError(f"external fixture declaration hash does not match file: {resolved}")
        key = str(resolved)
        identity = allowed["identity"]
        reproduction = allowed["reproduction"]
    else:
        key = rel
        identity = f"repository:{rel}"
        reproduction = f"read repository input {rel} and verify sha256"
    return key, {"kind": kind, "sha256": digest(resolved), "identity": identity, "reproduction": reproduction}
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--cwd", type=Path, default=Path.cwd())
    p.add_argument("--timeout", type=float, default=None)
    p.add_argument("--source", action="append", type=Path, default=[])
    p.add_argument("--test", action="append", type=Path, default=[])
    p.add_argument("--fixture", action="append", type=Path, default=[])
    p.add_argument("--expect-argv", action="append", default=[])
    p.add_argument("--require-stdout", action="store_true")
    p.add_argument("--repo", type=Path, help="Git root; with --state, bind the record to the task revision")
    p.add_argument("--state", type=Path, help="task-state.json whose baseline defines the revision token")
    p.add_argument("command", nargs=argparse.REMAINDER)
    args = p.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        p.error("a command is required after --")
    if args.output.exists():
        p.error(f"output already exists; refusing overwrite: {args.output}")
    if (args.repo is None) != (args.state is None):
        p.error("--repo and --state must be given together")
    cwd = args.cwd.resolve()
    if not cwd.is_dir():
        p.error(f"cwd is not a directory: {cwd}")
    repo = args.repo.resolve() if args.repo is not None else None
    state_for_inputs: dict = {}
    validator = None
    contract = None
    if repo is not None:
        try:
            validator = load_validator()
            repo = validator.ensure_repository(repo)
            manifest_for_inputs = args.state.resolve()
            state_for_inputs = json.loads(manifest_for_inputs.read_text(encoding="utf-8"))
            if not isinstance(state_for_inputs, dict):
                raise ValueError("task-state root must be a JSON object")
            if state_for_inputs.get("schema_version") == "1.3":
                contract = load_spec_contract()
                spec_issues = contract.validate_spec(state_for_inputs, repo)
                blocking_spec_issues = [issue for issue in spec_issues if issue.get("code") != "SPEC_OPEN_ITEMS_PENDING"]
                if blocking_spec_issues:
                    print(json.dumps({"ok": False, "error": "invalid Spec binding", "issues": blocking_spec_issues}, ensure_ascii=False), file=sys.stderr)
                    return 2
        except Exception as exc:
            print(json.dumps({"ok": False, "error": f"cannot validate inputs: {exc}"}), file=sys.stderr)
            return 2
    files: dict[str, dict[str, str]] = {}
    for kind, paths in (("source", args.source), ("test", args.test), ("fixture", args.fixture)):
        for raw in paths:
            lexical = raw if raw.is_absolute() else cwd / raw
            if repo is not None and validator.input_uses_repo_symlink(repo, str(lexical)):
                p.error(f"{kind} input uses a repository symlink alias: {lexical}")
            if repo is not None and lexical.is_absolute():
                try:
                    lexical.resolve().relative_to(repo)
                    inside_repo = True
                except ValueError:
                    inside_repo = False
                if not inside_repo:
                    resolved_lexical = lexical.resolve()
                    allowed_external = validator.external_input_paths(state_for_inputs)
                    if str(resolved_lexical) in allowed_external and str(lexical) != str(resolved_lexical):
                        p.error(f"{kind} input must use the exact declared external fixture path: {lexical}")
            path = lexical
            path = path.resolve()
            if not path.is_file() or path.is_symlink():
                p.error(f"{kind} file does not exist or is a symlink: {path}")
            try:
                if repo is None:
                    key = str(path)
                    declaration = {"kind": kind, "sha256": digest(path), "identity": f"path:{key}", "reproduction": f"read input {key} and verify sha256"}
                else:
                    key, declaration = input_declaration(validator, repo, state_for_inputs, path, kind)
            except ValueError as exc:
                p.error(str(exc))
            files[key] = declaration
    if args.expect_argv and args.expect_argv != command:
        p.error(f"argv does not match expected command: {command!r}")

    revision_of = None
    if repo is not None:
        try:
            validator = load_validator()
            repo = validator.ensure_repository(repo)
            manifest = args.state.resolve()
            state = json.loads(manifest.read_text(encoding="utf-8"))
            if not isinstance(state, dict):
                raise ValueError("task-state root must be a JSON object")

            def revision_of() -> str:
                latest = json.loads(manifest.read_text(encoding="utf-8"))
                return validator.revision_for_state(repo, manifest, latest)

            def entries_of() -> dict[str, bytes]:
                latest = json.loads(manifest.read_text(encoding="utf-8"))
                return validator.revision_entries_for_state(repo, manifest, latest)

            revision_before = revision_of()
            entries_before = entries_of()
        except Exception as exc:  # the command must not run without its binding
            print(json.dumps({"ok": False, "error": f"cannot compute revision: {exc}"}), file=sys.stderr)
            return 2
    else:
        revision_before = None
        entries_before = {}
    spec_version = None
    spec_sha256 = None
    spec_version_before = None
    spec_sha256_before = None
    if repo is not None and state.get("schema_version") == "1.3":
        try:
            contract = contract or load_spec_contract()
            spec_version = state.get("spec", {}).get("version")
            spec_sha256 = contract.spec_digest(state, repo)
            spec_version_before = spec_version
            spec_sha256_before = spec_sha256
        except (TypeError, ValueError, OSError):
            spec_version = state.get("spec", {}).get("version") if isinstance(state.get("spec"), dict) else None
    input_hashes_before = {key: value["sha256"] for key, value in files.items()}
    started = now()
    timed_out = False
    wrapper_exit = None
    try:
        process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        try:
            stdout_raw, stderr_raw = process.communicate(timeout=args.timeout)
            code = process.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            wrapper_exit = 124
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                process.kill()
            stdout_raw, stderr_raw = process.communicate()
            code = process.returncode
    except OSError as exc:
        wrapper_exit = 127 if isinstance(exc, FileNotFoundError) else 126
        code = None
        stdout_raw = b""
        stderr_raw = str(exc).encode()
    stdout = stdout_raw.decode("utf-8", errors="replace")
    stderr = stderr_raw.decode("utf-8", errors="replace")
    ended = now()
    spec_version_after = None
    spec_sha256_after = None
    if repo is not None and state.get("schema_version") == "1.3":
        try:
            after_state = json.loads(args.state.resolve().read_text(encoding="utf-8"))
            contract = contract or load_spec_contract()
            spec_version_after = after_state.get("spec", {}).get("version") if isinstance(after_state.get("spec"), dict) else None
            spec_sha256_after = contract.spec_digest(after_state, repo)
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            spec_version_after = None
            spec_sha256_after = None
    revision_after = None
    changed_paths: list[str] = []
    if revision_of is not None:
        try:
            revision_after = revision_of()
            entries_after = entries_of()
            changed_paths = sorted(
                path
                for path in set(entries_before) | set(entries_after)
                if entries_before.get(path) != entries_after.get(path)
            )
        except Exception as exc:
            revision_after = f"unavailable: {exc}"
    revision_changed = revision_of is not None and revision_after != revision_before
    input_changed = []
    for key, expected in input_hashes_before.items():
        try:
            current = digest(Path(key) if Path(key).is_absolute() else repo / key) if (repo is not None or Path(key).is_absolute()) else expected
        except (OSError, ValueError):
            current = None
        if current != expected:
            input_changed.append(key)
    if input_changed:
        revision_changed = True
        changed_paths = sorted(set(changed_paths) | set(input_changed))
    if timed_out:
        result = "timeout"
    elif revision_changed:
        result = "revision_changed"
    elif args.require_stdout and not stdout:
        result = "missing_output"
    else:
        result = "passed" if code == 0 else "failed"
    record = {
        "argv": command,
        "cwd": str(cwd),
        "started_at": started,
        "ended_at": ended,
        "exit_code": code,
        "timed_out": timed_out,
        "wrapper_exit_code": wrapper_exit,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_base64": base64.b64encode(stdout_raw).decode("ascii"),
        "stderr_base64": base64.b64encode(stderr_raw).decode("ascii"),
        "stdout_present": bool(stdout),
        "stderr_present": bool(stderr),
        "stdout_required": args.require_stdout,
        "inputs": files,
        "repo": str(repo) if repo is not None else None,
        "cwd_relative": relative_to(cwd, repo),
        "revision_before": revision_before,
        "revision_after": revision_after,
        "revision": revision_before if revision_of is not None and not revision_changed else None,
        "spec_version": spec_version,
        "spec_sha256": spec_sha256,
        "spec_before": {"version": spec_version_before, "sha256": spec_sha256_before} if repo is not None and state.get("schema_version") == "1.3" else None,
        "spec_after": {"version": spec_version_after, "sha256": spec_sha256_after} if repo is not None and state.get("schema_version") == "1.3" else None,
        "spec_version_before": spec_version_before,
        "spec_sha256_before": spec_sha256_before,
        "spec_version_after": spec_version_after,
        "spec_sha256_after": spec_sha256_after,
        "revision_changed_paths": changed_paths[:50],
        "input_changed_paths": input_changed,
        "result": result,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=args.output.parent, delete=False) as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    try:
        # A hard-link is an exclusive publication: unlike replace(), it cannot
        # overwrite a destination created by the command or another recorder.
        os.link(temporary, args.output)
    except FileExistsError:
        print(f"output appeared while command was running; refusing overwrite: {args.output}", file=sys.stderr)
        return 2
    finally:
        temporary.unlink(missing_ok=True)
    if result == "revision_changed":
        listed = ", ".join(changed_paths[:5]) or "unknown paths"
        print(
            f"repository content changed while the command ran ({listed}); ignore generated files "
            "or write them under the evidence directory, then rerun",
            file=sys.stderr,
        )
    if result == "timeout":
        return 124
    if result in {"revision_changed", "missing_output"}:
        return 1
    return wrapper_exit if wrapper_exit is not None else (code if code is not None else 1)


if __name__ == "__main__":
    raise SystemExit(main())
