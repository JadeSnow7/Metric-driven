#!/usr/bin/env python3
"""Run one command and write an evidence record of what actually happened."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import base64
import os
import signal
import re
from datetime import datetime, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


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
    p.add_argument("command", nargs=argparse.REMAINDER)
    args = p.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        p.error("a command is required after --")
    if args.output.exists():
        p.error(f"output already exists; refusing overwrite: {args.output}")
    cwd = args.cwd.resolve()
    if not cwd.is_dir():
        p.error(f"cwd is not a directory: {cwd}")
    files: dict[str, dict[str, str]] = {}
    for kind, paths in (("source", args.source), ("test", args.test), ("fixture", args.fixture)):
        for raw in paths:
            path = raw if raw.is_absolute() else cwd / raw
            path = path.resolve()
            if not path.is_file():
                p.error(f"{kind} file does not exist: {path}")
            files[str(path)] = {"kind": kind, "sha256": digest(path)}
    if args.expect_argv and args.expect_argv != command:
        p.error(f"argv does not match expected command: {command!r}")
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
    except FileNotFoundError as exc:
        wrapper_exit = 127
        if isinstance(exc, FileNotFoundError):
            code = None
            stdout_raw = b""
            stderr_raw = str(exc).encode()
    stdout = stdout_raw.decode("utf-8", errors="replace")
    stderr = stderr_raw.decode("utf-8", errors="replace")
    ended = now()
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
        "result": "missing_output" if args.require_stdout and not stdout else ("timeout" if timed_out else ("passed" if code == 0 else "failed")),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=args.output.parent, delete=False) as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(args.output)
    if record["result"] == "missing_output":
        return 1
    return wrapper_exit if wrapper_exit is not None else (code if code is not None else 1)


if __name__ == "__main__":
    raise SystemExit(main())
