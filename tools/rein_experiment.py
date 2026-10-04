#!/usr/bin/env python3
"""Snapshot, clone, seal, and compare local Rein experiment trees.

The tool intentionally uses only the Python standard library.  A snapshot is a
directory containing a manifest and a ``files/`` tree copied from a Git working
tree.  Git's own path inventory is the source of truth; safety filters remove
secrets and generated/dependency trees before copying.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


EXCLUDED_DIRS = {".git", "node_modules", "target", "build", "dist", ".vitepress/cache", ".vitepress/dist"}
SECRET_NAMES = {".env", ".env.local", ".env.production", ".env.development"}


def run_git(source: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(source), *args], text=True, stderr=subprocess.STDOUT).strip()


def run_git_paths(source: Path, *args: str) -> list[str]:
    raw = subprocess.check_output(["git", "-C", str(source), *args], stderr=subprocess.STDOUT)
    return [item.decode("utf-8", "surrogateescape") for item in raw.split(b"\0") if item]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def excluded(rel: str) -> bool:
    parts = Path(rel).parts
    if any(part in {".git", "node_modules", "target", "build", "dist"} for part in parts):
        return True
    if rel == ".vitepress/cache" or rel.startswith(".vitepress/cache/"):
        return True
    if rel == ".vitepress/dist" or rel.startswith(".vitepress/dist/"):
        return True
    name = Path(rel).name
    return name in SECRET_NAMES or (name.startswith(".env.") and name != ".env.example")


def inventory(source: Path) -> tuple[list[str], list[str]]:
    """Return present Git inventory and tracked paths deleted in the worktree."""
    raw = run_git_paths(source, "ls-files", "-z", "-co", "--exclude-standard")
    present = sorted({p for p in raw if p and not excluded(p) and ((source / p).is_file() or (source / p).is_symlink())})
    tracked = set(run_git_paths(source, "ls-files", "-z"))
    deleted = sorted(p for p in tracked - set(present) if not excluded(p) and not (source / p).exists())
    return present, deleted


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_records(root: Path) -> list[dict]:
    records = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink()):
        rel = path.relative_to(root).as_posix()
        if excluded(rel) or rel in {".rein-snapshot.json", "seal.json"}:
            continue
        records.append({"path": rel, "sha256": sha256(path), "mode": path.stat().st_mode & 0o777})
    for path in sorted(p for p in root.rglob("*") if p.is_symlink()):
        rel = path.relative_to(root).as_posix()
        if excluded(rel) or rel in {".rein-snapshot.json", "seal.json"}:
            continue
        records.append({"path": rel, "mode": path.lstat().st_mode & 0o777, "symlink": os.readlink(path)})
    records.sort(key=lambda item: item["path"])
    return records


def snapshot(source: Path, output: Path) -> Path:
    source = source.resolve()
    output = output.resolve()
    if output.exists():
        raise RuntimeError(f"output already exists: {output}")
    present, deleted = inventory(source)
    files_root = output / "files"
    files_root.mkdir(parents=True)
    skipped_symlinks = []
    for rel in present:
        src = source / rel
        if src.is_symlink():
            try:
                src.resolve().relative_to(source)
            except ValueError:
                skipped_symlinks.append(rel)
                continue
        if not src.is_file() and not src.is_symlink():
            continue
        dest = files_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_symlink():
            os.symlink(os.readlink(src), dest)
        else:
            shutil.copy2(src, dest)  # copy2 retains executable bits and timestamps
    manifest = {
        "kind": "rein-working-tree-snapshot",
        "created_at": utc_now(),
        "source": str(source),
        "head": run_git(source, "rev-parse", "HEAD"),
        "branch": run_git(source, "branch", "--show-current"),
        "files": file_records(files_root),
        "git_inventory": present,
        "deleted_tracked": deleted,
        "skipped_symlinks": skipped_symlinks,
        "excluded_policy": {"directories": sorted(EXCLUDED_DIRS), "secret_names": sorted(SECRET_NAMES)},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return output


def clone(snapshot_dir: Path, output: Path) -> Path:
    snapshot_dir = snapshot_dir.resolve()
    output = output.resolve()
    if output.exists():
        raise RuntimeError(f"output already exists: {output}")
    manifest = json.loads((snapshot_dir / "manifest.json").read_text())
    shutil.copytree(snapshot_dir / "files", output, symlinks=True)
    (output / ".rein-snapshot.json").write_text(json.dumps({"source_manifest": manifest, "cloned_at": utc_now()}, ensure_ascii=False, indent=2) + "\n")
    return output


def seal(tree: Path, output: Path | None = None) -> Path:
    tree = tree.resolve()
    records = file_records(tree)
    source_meta = tree / ".rein-snapshot.json"
    payload = {"kind": "rein-seal", "created_at": utc_now(), "tree": str(tree), "files": records}
    if source_meta.exists():
        payload["source_snapshot"] = json.loads(source_meta.read_text())
    target = (output or (tree / "seal.json")).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return target


def compare(first: Path, second: Path) -> int:
    a = json.loads(first.read_text())
    b = json.loads(second.read_text())
    amap = {x["path"]: x for x in a.get("files", [])}
    bmap = {x["path"]: x for x in b.get("files", [])}
    paths = sorted(set(amap) | set(bmap))
    differences = []
    for path in paths:
        if amap.get(path) != bmap.get(path):
            differences.append(path)
    result = {"equal": not differences, "differences": differences, "first": str(first), "second": str(second)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not differences else 1


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Reproducible Rein working-tree snapshots and sealed manifests.")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("snapshot", help="copy tracked and nonignored untracked files into a manifest snapshot")
    s.add_argument("--source", type=Path, required=True, help="Git working-tree directory")
    s.add_argument("--output", type=Path, required=True, help="new snapshot directory")
    c = sub.add_parser("clone", help="clone snapshot files into a new independent directory")
    c.add_argument("--snapshot", type=Path, required=True)
    c.add_argument("--output", type=Path, required=True)
    z = sub.add_parser("seal", help="hash a final source/document tree")
    z.add_argument("--tree", type=Path, required=True)
    z.add_argument("--output", type=Path)
    d = sub.add_parser("compare-manifests", help="compare two seal or snapshot manifests")
    d.add_argument("first", type=Path)
    d.add_argument("second", type=Path)
    return p


def main(argv: Iterable[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "snapshot":
            print(snapshot(args.source, args.output))
        elif args.command == "clone":
            print(clone(args.snapshot, args.output))
        elif args.command == "seal":
            print(seal(args.tree, args.output))
        else:
            return compare(args.first.resolve(), args.second.resolve())
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"rein_experiment: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
