#!/usr/bin/env python3
"""Create one immutable, path-scoped run seal without replacing prior output."""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path

EXCLUDE = {".git", "node_modules", "target", "build", "cache", ".cache"}

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""): h.update(b)
    return h.hexdigest()

def files(root: Path) -> dict[str, Path]:
    return {p.relative_to(root).as_posix(): p for p in root.rglob("*") if p.is_file() and not any(x in EXCLUDE for x in p.relative_to(root).parts)}

def git(root: Path, args: list[str]) -> str | None:
    r = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    return r.stdout if r.returncode == 0 else None

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True); p.add_argument("--work", type=Path, required=True)
    p.add_argument("--run", type=Path, required=True); p.add_argument("--output", type=Path, required=True)
    p.add_argument("--source-manifest", type=Path); p.add_argument("--session"); p.add_argument("--usage", type=Path)
    a = p.parse_args(); source, work, run, out = (x.resolve() for x in (a.source, a.work, a.run, a.output))
    created = False
    try:
        if out.exists(): raise RuntimeError("refusing to overwrite existing seal")
        if out in (source, work, run) or source == out: raise RuntimeError("source and target must differ")
        if not source.is_dir() or not work.is_dir() or not run.is_dir(): raise RuntimeError("source/work/run must be directories")
        out.mkdir(parents=True)
        created = True
        src = {k: digest(v) for k, v in files(source).items()}; prod = {k: digest(v) for k, v in files(work).items()}
        common = {}
        if a.source_manifest:
            common = json.loads(a.source_manifest.read_text(encoding="utf-8"))
        manifest = {"source": src, "common_manifest": common, "added": sorted(set(prod)-set(src)), "deleted": sorted(set(src)-set(prod)), "modified": sorted(k for k in set(src)&set(prod) if src[k] != prod[k])}
        (out / "source-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (out / "git.json").write_text(json.dumps({"head": git(work, ["rev-parse", "HEAD"]), "diff": git(work, ["diff", "--binary"]), "status": git(work, ["status", "--short"])}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        shutil.copytree(run, out / "run", ignore=shutil.ignore_patterns(*EXCLUDE))
        (out / "run-meta.json").write_text(json.dumps({"argv": ["seal.py", *(__import__('sys').argv[1:])], "sealed_at": datetime.now(timezone.utc).isoformat().replace('+00:00','Z'), "session": a.session, "usage": json.loads(a.usage.read_text()) if a.usage else {"five_hour": None, "weekly": None}, "token_count": {"total": None, "last": None, "cache": None, "reasoning": None}, "elapsed_seconds": None}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "output": str(out), "added": manifest["added"], "deleted": manifest["deleted"], "modified": manifest["modified"]}, ensure_ascii=False)); return 0
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as e:
        if created and out.exists(): shutil.rmtree(out)
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)); return 1

if __name__ == "__main__": raise SystemExit(main())
