#!/usr/bin/env python3
"""Integrate an explicitly listed handoff without source/target drift or overwrite."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import hashlib
import re
from pathlib import Path


def git_head(root: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "cannot read git HEAD")
    return result.stdout.strip()


def safe(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not value.strip():
        raise ValueError(f"unsafe path: {value!r}")
    return path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-root", type=Path, required=True)
    p.add_argument("--target-root", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True, help="JSON: {source_root,target_root,files:{target:{source,source_sha256,target_sha256}}}")
    p.add_argument("--source-revision", required=True)
    p.add_argument("--target-base", required=True)
    p.add_argument("--allowed-path", action="append", required=True)
    args = p.parse_args(argv)
    try:
        source, target = args.source_root.resolve(), args.target_root.resolve()
        if git_head(source) != args.source_revision:
            raise RuntimeError("source revision drifted")
        if git_head(target) != args.target_base:
            raise RuntimeError("target base drifted")
        allowed = [safe(item).as_posix() for item in args.allowed_path]
        entries = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(entries, dict):
            raise ValueError("manifest must be a JSON object")
        plan: list[tuple[Path, Path]] = []
        if Path(entries.get("source_root", "")).resolve() != source:
            raise RuntimeError("source root identity drifted")
        if Path(entries.get("target_root", "")).resolve() != target:
            raise RuntimeError("target root identity drifted")
        files = entries.get("files")
        if not isinstance(files, dict) or not files:
            raise ValueError("manifest.files must be a non-empty object")
        preflight: list[tuple[Path, Path]] = []
        for target_name, spec in files.items():
            if not isinstance(spec, dict):
                raise ValueError(f"invalid manifest entry: {target_name}")
            source_name = spec.get("source")
            expected_source, expected_target = spec.get("source_sha256"), spec.get("target_sha256")
            if not isinstance(source_name, str):
                raise ValueError(f"manifest source must be a string: {target_name}")
            if not isinstance(expected_source, str) or not isinstance(expected_target, str):
                raise ValueError(f"manifest hashes are required: {target_name}")
            if expected_source != "absent" and not re.fullmatch(r"[0-9a-f]{64}", expected_source):
                raise ValueError(f"invalid source hash: {target_name}")
            if expected_target != "absent" and not re.fullmatch(r"[0-9a-f]{64}", expected_target):
                raise ValueError(f"invalid target hash: {target_name}")
            dst = safe(target_name).as_posix()
            src = safe(source_name)
            if not any(item == "." or dst == item or dst.startswith(item.rstrip("/") + "/") for item in allowed):
                raise RuntimeError(f"path outside allowed scope: {dst}")
            src_path, dst_path = source / src, target / dst
            if not src_path.parent.resolve().is_relative_to(source):
                raise RuntimeError(f"source path escaped source root: {src}")
            if src_path.is_symlink() or not src_path.is_file():
                raise RuntimeError(f"source file missing: {src}")
            if not dst_path.parent.resolve().is_relative_to(target):
                raise RuntimeError(f"target path escaped target root: {dst}")
            if expected_source and sha256(src_path) != expected_source:
                raise RuntimeError(f"source hash drifted: {src}")
            if dst_path.is_symlink() or (dst_path.exists() and not dst_path.is_file()):
                raise RuntimeError(f"target is not a regular file: {dst}")
            if expected_target == "absent" and dst_path.exists():
                    raise RuntimeError(f"target appeared since handoff: {dst}")
            if expected_target != "absent" and (not dst_path.exists() or sha256(dst_path) != expected_target):
                    raise RuntimeError(f"target baseline drifted: {dst}")
            preflight.append((src_path, dst_path))
        for src_path, dst_path in preflight:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
        print(json.dumps({"ok": True, "copied": [str(dst.relative_to(target)) for _, dst in preflight]}, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
