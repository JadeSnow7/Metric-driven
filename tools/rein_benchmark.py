#!/usr/bin/env python3
"""Bounded preparation, execution and packaging helper for later Rein arms.

This module deliberately does not decide whether a product is correct.  It
only makes the inputs, process invocation and resulting trees auditable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

EXCLUDED_DIRS = {".git", "deps", "target", ".cargo-target", "build", "dist", "node_modules"}
EXCLUDED_BUILD = {".next", ".vitepress/cache", ".vitepress/dist"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def excluded(rel: Path) -> bool:
    parts = rel.parts
    if any(p in EXCLUDED_DIRS for p in parts):
        return True
    for build_path in EXCLUDED_BUILD:
        build_parts = Path(build_path).parts
        if any(parts[i:i + len(build_parts)] == build_parts for i in range(len(parts) - len(build_parts) + 1)):
            return True
    name = rel.name
    return name == ".env" or (name.startswith(".env.") and name != ".env.example")


def manifest(root: Path, *, skip: set[str] | None = None) -> list[dict]:
    skip = skip or set()
    out = []
    for current, dirs, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        dirs[:] = sorted(d for d in dirs if not excluded(current_path.joinpath(d).relative_to(root)))
        for name in sorted(dirs + files):
            p = current_path / name
            rel_path = p.relative_to(root)
            rel = rel_path.as_posix()
            if rel in skip or excluded(rel_path):
                continue
            if p.is_symlink():
                out.append({"path": rel, "symlink": os.readlink(p), "mode": p.lstat().st_mode & 0o777})
            elif p.is_file():
                out.append({"path": rel, "sha256": digest(p), "mode": p.stat().st_mode & 0o777})
    return out


def copy_tree(src: Path, dst: Path, *, skip: set[str] | None = None) -> list[str]:
    if dst.exists():
        raise RuntimeError(f"refusing to overwrite existing directory: {dst}")
    skip = skip or set()
    copied = []
    src_resolved = src.resolve()
    for current, dirs, files in os.walk(src, followlinks=False):
        current_path = Path(current)
        dirs[:] = sorted(d for d in dirs if not excluded(current_path.joinpath(d).relative_to(src)))
        for name in sorted(dirs + files):
            p = current_path / name
            rel = p.relative_to(src)
            if rel.as_posix() in skip or excluded(rel):
                continue
            target = dst / rel
            if p.is_symlink():
                resolved = p.resolve()
                if not resolved.is_relative_to(src_resolved):
                    raise RuntimeError(f"refusing symlink outside source: {rel}")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(os.readlink(p))
                copied.append(rel.as_posix())
            elif p.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            elif p.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, target)
                copied.append(rel.as_posix())
    dst.mkdir(parents=True, exist_ok=True)
    return copied


def input_records(inputs: list[Path], destination: Path) -> list[dict]:
    records = []
    for source in inputs:
        if not source.is_file():
            raise RuntimeError(f"input is not a file: {source}")
        target = destination / source.name
        if target.exists():
            raise RuntimeError(f"duplicate task input: {target.name}")
        shutil.copy2(source, target)
        records.append({"name": source.name, "sha256": digest(target), "source": str(source.resolve())})
    return records


def prepare(source: Path, output: Path, inputs: list[Path], *, skill15: list[Path] = (), copy_git: Path | None = None) -> dict:
    source = source.resolve(); output = output.resolve()
    if output.exists():
        raise RuntimeError(f"refusing to overwrite existing preparation: {output}")
    output.mkdir(parents=True)
    arms = {}
    for arm in ("control", "skill"):
        root = output / f"{arm}-arm"
        copy_tree(source, root)
        task = root / "task-inputs"
        if task.exists():
            shutil.rmtree(task)
        task.mkdir()
        rec = input_records(inputs, task)
        if copy_git:
            # Explicitly requested local history is copied as ordinary data.
            requested = copy_git.resolve()
            gitdir = requested if requested.name == ".git" else requested / ".git"
            if not gitdir.is_dir():
                raise RuntimeError(f"local Git source has no .git directory: {requested}")
            history = root / ".git"
            copy_tree(gitdir, history)
            # A copied config could contain a remote URL or credentials.  The
            # object/ref database remains useful without it and is safer.
            config = history / "config"
            if config.exists():
                config.unlink()
        arms[arm] = {"root": str(root), "files": manifest(root)}
    if arms["control"]["files"] != arms["skill"]["files"]:
        raise RuntimeError("prepared arm manifests differ")
    extra = [{"path": str(p), "sha256": digest(p)} for p in skill15 if p.is_file()]
    result = {"kind": "rein-benchmark-preparation", "created_at": now(), "source": str(source),
              "arms": arms, "task_inputs": rec, "skill15_external_hashes": extra,
              "excluded": sorted(EXCLUDED_DIRS | EXCLUDED_BUILD), "copy_git": bool(copy_git)}
    (output / "prepare.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def role_config(path: Path) -> dict:
    return tomllib.loads(path.read_text())


def build_argv(coder: Path, workspace: Path, prompt_file: Path, skill: Path | None, target: Path, log: Path, executable: str = "codex") -> list[str]:
    cfg = role_config(coder)
    argv = [executable, "exec", "--ephemeral", "--json", "--approve-for-me", "--skip-git-repo-check", "--sandbox", "workspace-write",
            "--disable", "memories", "--disable", "multi_agent",
            "-C", str(workspace), "--add-dir", str(target), "--add-dir", str(log), "-m", cfg.get("model", "gpt-5.6-luna"),
            "-c", f"model_reasoning_effort={cfg.get('model_reasoning_effort', 'medium')}",
            "-c", "developer_instructions=" + json.dumps(cfg.get("developer_instructions", "")),
            "-o", str(log.parent / "final.md"), "-"]
    return argv


def _stop_process(proc: subprocess.Popen[bytes] | None) -> str | None:
    """Stop only this run's process, escalating when it ignores SIGTERM."""
    if proc is None or proc.poll() is not None:
        return None
    try:
        proc.terminate()
    except OSError as exc:
        return f"terminate: {exc!r}"
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
            proc.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return f"kill/wait: {exc!r}"
    return None


def _capture_text(path: Path) -> str:
    return path.read_text(errors="replace") if path.exists() else ""


def _drain_process_pipes(proc: subprocess.Popen[bytes] | None, stdout_path: Path, stderr_path: Path, deadline: float = 0.5) -> bool:
    if proc is None:
        return True
    import selectors
    selector = selectors.DefaultSelector()
    streams = ((proc.stdout, stdout_path), (proc.stderr, stderr_path))
    try:
        for stream, _ in streams:
            if stream is not None:
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ)
        end = time.monotonic() + deadline
        try:
            while selector.get_map() and time.monotonic() < end:
                for key, _ in selector.select(max(0, end - time.monotonic())):
                    try:
                        remainder = os.read(key.fileobj.fileno(), 65536)
                    except BlockingIOError:
                        continue
                    if remainder:
                        path = next(path for stream, path in streams if stream is key.fileobj)
                        with path.open("ab") as handle:
                            handle.write(remainder)
                    else:
                        selector.unregister(key.fileobj)
        except (KeyboardInterrupt, OSError):
            return False
        return not selector.get_map()
    finally:
        selector.close()
        for stream, _ in streams:
            if stream is not None:
                stream.close()


def run_one(coder: Path, workspace: Path, prompt: Path, out: Path, skill: Path | None = None, executable: str = "codex") -> int:
    if out.exists(): raise RuntimeError(f"refusing to overwrite run directory: {out}")
    out.mkdir(parents=True); started = time.monotonic(); started_at = now()
    target = out / "cargo-target"; log = out / "logs"; target.mkdir(); log.mkdir()
    common_prompt = prompt.read_text()
    actual_prompt = common_prompt
    if skill:
        actual_prompt += f"\n\nRead and apply the frozen skill at: {skill.resolve()}\n"
    actual_prompt_file = out / "actual-prompt.md"; actual_prompt_file.write_text(actual_prompt)
    argv = build_argv(coder, workspace, actual_prompt_file, skill, target, log, executable)
    events_path = out / "events.jsonl"; stderr_path = out / "stderr.txt"
    events_path.touch(); stderr_path.touch()
    meta = {"started_at": started_at, "argv": argv, "role_sha256": digest(coder), "role_bytes_sha256": digest(coder),
            "prompt_sha256": digest(prompt), "prompt": common_prompt, "actual_prompt_sha256": digest(actual_prompt_file), "actual_prompt": actual_prompt, "workspace": str(workspace),
            "source_initial_hash": {x["path"]: x.get("sha256", x.get("symlink")) for x in manifest(workspace)},
            "skill": str(skill) if skill else None, "cli_version": None}
    (out / "run.json").write_text(json.dumps(meta, indent=2) + "\n")
    proc = None; prompt_handle = None
    try:
        if Path(executable).name == "codex":
            version = subprocess.run([executable, "--version"], text=True, capture_output=True)
            meta["cli_version"] = (version.stdout or version.stderr).strip()
        env = os.environ.copy(); env["CARGO_TARGET_DIR"] = str(target)
        prompt_handle = actual_prompt_file.open("rb")
        proc = subprocess.Popen(argv, stdin=prompt_handle, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, cwd=workspace)
        with events_path.open("ab") as event_file, stderr_path.open("ab") as error_file:
            import selectors
            selector = selectors.DefaultSelector(); selector.register(proc.stdout, selectors.EVENT_READ, event_file); selector.register(proc.stderr, selectors.EVENT_READ, error_file)
            try:
                while selector.get_map():
                    for key, _ in selector.select():
                        chunk = os.read(key.fileobj.fileno(), 65536)
                        if chunk:
                            key.data.write(chunk); key.data.flush()
                        else:
                            selector.unregister(key.fileobj)
            finally:
                selector.close()
        proc.wait(); prompt_handle.close(); proc.stdout.close(); proc.stderr.close()
        stdout = _capture_text(events_path); stderr = _capture_text(stderr_path)
        code = proc.returncode
        classification = "completed" if code == 0 else "process_exit"
    except KeyboardInterrupt:
        stop_error = _stop_process(proc)
        drain_complete = _drain_process_pipes(proc, events_path, stderr_path)
        if prompt_handle: prompt_handle.close()
        stdout = _capture_text(events_path); stderr = _capture_text(stderr_path); code = 130; classification = "interrupted"
        meta.update({"stop_error": stop_error, "drain_complete": drain_complete})
    except Exception as exc:
        stop_error = _stop_process(proc)
        drain_complete = _drain_process_pipes(proc, events_path, stderr_path)
        if prompt_handle: prompt_handle.close()
        stdout = _capture_text(events_path); stderr = _capture_text(stderr_path)
        code = getattr(proc, "returncode", None) or 127
        classification = "spawn_or_capture_error"
        meta.update({"error": repr(exc), "stop_error": stop_error, "drain_complete": drain_complete})
    lines = (stdout or "").splitlines()
    final_path = out / "final.md"
    usage = None
    for line in reversed(lines):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and event.get("usage") is not None:
            usage = event["usage"]; break
    terminal = None
    for line in reversed(lines):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and event.get("type") in {"turn.completed", "turn.failed", "turn.blocked"}:
            terminal = event["type"]; break
    meta.update({"ended_at": now(), "elapsed_seconds": time.monotonic() - started, "exit_code": code,
                 "terminal_status": terminal, "usage": usage, "classification": classification,
                 "stdout_file": str(events_path), "stderr_file": str(stderr_path),
                 "final_file": str(out / "final.md") if (out / "final.md").exists() else None})
    (out / "run.json").write_text(json.dumps(meta, indent=2) + "\n")
    return code


def tree_hashes(root: Path) -> dict[str, str]:
    return {x["path"]: (x["sha256"] if "sha256" in x else "symlink:" + x["symlink"]) + f"|git_exec:{int(bool(x['mode'] & 0o111))}" for x in manifest(root)}


def seal(tree: Path, output: Path, baseline: Path | None = None, execution: Path | None = None) -> Path:
    if output.exists(): raise RuntimeError(f"refusing to overwrite seal: {output}")
    if execution is None: raise RuntimeError("formal seal requires external --execution evidence")
    execution = execution.resolve()
    if not execution.is_file(): raise RuntimeError("execution evidence is missing")
    run = json.loads(execution.read_text())
    if "ended_at" not in run or "exit_code" not in run or not run.get("terminal_status"):
        raise RuntimeError("cannot seal an unfinished execution")
    if Path(run.get("workspace", "")).resolve() != tree.resolve(): raise RuntimeError("execution workspace does not match tree")
    output.mkdir(parents=True)
    copy_tree(tree, output / "tree")
    shutil.copy2(execution, output / "execution.json")
    # Preserve the raw external execution bundle beside its summary metadata.
    # These files are optional for hand-built test evidence, but mandatory
    # artifacts produced by run_one are carried through when present.
    for name in ("events.jsonl", "stderr.txt", "final.md"):
        sibling = execution.parent / name
        if sibling.is_file(): shutil.copy2(sibling, output / name)
    hashes = tree_hashes(output / "tree")
    payload = {"kind": "rein-benchmark-seal", "created_at": now(), "tree": hashes}
    if baseline:
        base = tree_hashes(baseline); changed = sorted(p for p in set(base)|set(hashes) if base.get(p) != hashes.get(p))
        payload["baseline"] = str(baseline); payload["changed"] = changed
        with tempfile.TemporaryDirectory() as td:
            base_name = "baseline"; result_name = "result"
            filtered_base = Path(td) / "base-source"; copy_tree(baseline, filtered_base)
            filtered_result = Path(td) / "result-source"; copy_tree(output / "tree", filtered_result)
            recovery = Path(td) / base_name
            # Keep a real Git index so binary payloads, empty additions, modes,
            # and symlink targets are represented by one portable patch.
            repo = Path(td) / "patch-repo"
            shutil.copytree(filtered_base, repo, symlinks=True)
            subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
            base_tree = subprocess.check_output(["git", "-C", str(repo), "write-tree"], text=True).strip()
            for child in repo.iterdir():
                if child.name == ".git": continue
                if child.is_dir() and not child.is_symlink(): shutil.rmtree(child)
                else: child.unlink()
            for child in filtered_result.iterdir():
                target = repo / child.name
                if child.is_dir() and not child.is_symlink(): shutil.copytree(child, target, symlinks=True)
                elif child.is_symlink(): target.symlink_to(os.readlink(child))
                else: shutil.copy2(child, target)
            subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
            result_tree = subprocess.check_output(["git", "-C", str(repo), "write-tree"], text=True).strip()
            binary_patch = subprocess.check_output(["git", "-C", str(repo), "diff", "--binary", base_tree, result_tree], text=True)
            (output / "baseline.patch").write_text(binary_patch)
            copy_tree(filtered_base, recovery)
            apply_repo = Path(td) / "apply-repo"
            shutil.copytree(recovery, apply_repo, symlinks=True)
            subprocess.run(["git", "-C", str(apply_repo), "init", "-q"], check=True, capture_output=True)
            (Path(td) / "change.patch").write_text(binary_patch)
            applied = subprocess.run(["git", "-C", str(apply_repo), "apply", "--binary", str(Path(td) / "change.patch")], text=True, capture_output=True) if binary_patch else None
            if (applied is not None and applied.returncode != 0) or manifest(apply_repo) != manifest(output / "tree"):
                raise RuntimeError("baseline patch did not recover result hashes")
    payload["execution"] = str(execution)
    (output / "seal.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return output


def review_pack(source: Path | dict[str, Path], output: Path, mapping: dict, exclusions: set[str] = set()) -> Path:
    if output.exists(): raise RuntimeError(f"refusing to overwrite review pack: {output}")
    output.mkdir(parents=True)
    sources = source if isinstance(source, dict) else {"control": source, "skill": source}
    for reviewer, packages in mapping.items():
        for arm, package in packages.items():
            if arm not in sources: raise RuntimeError(f"mapping references unknown source: {arm}")
            dst = output / reviewer / package
            copy_tree(Path(sources[arm]), dst, skip=exclusions)
            (output / reviewer / f"{package}.cargo-target").mkdir(parents=True)
    (output / "review-manifest.json").write_text(json.dumps({"source": {k: str(v) for k, v in sources.items()}, "mapping": mapping,
        "exclusions": sorted(exclusions), "created_at": now()}, indent=2) + "\n")
    return output


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__); s = p.add_subparsers(dest="cmd", required=True)
    x = s.add_parser("prepare"); x.add_argument("--source", type=Path, required=True); x.add_argument("--output", type=Path, required=True); x.add_argument("--input", type=Path, action="append", default=[]); x.add_argument("--skill15", type=Path, action="append", default=[]); x.add_argument("--copy-git", type=Path)
    x = s.add_parser("run"); x.add_argument("--coder", type=Path, required=True); x.add_argument("--workspace", type=Path, required=True); x.add_argument("--prompt", type=Path, required=True); x.add_argument("--output", type=Path, required=True); x.add_argument("--skill", type=Path); x.add_argument("--executable", default="codex")
    x = s.add_parser("seal"); x.add_argument("--tree", type=Path, required=True); x.add_argument("--output", type=Path, required=True); x.add_argument("--baseline", type=Path); x.add_argument("--execution", type=Path, required=True)
    x = s.add_parser("review-pack"); x.add_argument("--source", type=Path); x.add_argument("--source-control", type=Path); x.add_argument("--source-skill", type=Path); x.add_argument("--output", type=Path, required=True); x.add_argument("--mapping", type=Path, required=True); x.add_argument("--exclude", action="append", default=[])
    a = p.parse_args(argv)
    try:
        if a.cmd == "prepare": prepare(a.source, a.output, a.input, skill15=a.skill15, copy_git=a.copy_git)
        elif a.cmd == "run": return run_one(a.coder, a.workspace, a.prompt, a.output, a.skill, a.executable)
        elif a.cmd == "seal": seal(a.tree, a.output, a.baseline, a.execution)
        else:
            sources = {"control": a.source_control or a.source, "skill": a.source_skill or a.source}
            if not all(sources.values()): raise RuntimeError("review-pack needs --source or both arm sources")
            review_pack(sources, a.output, json.loads(a.mapping.read_text()), set(a.exclude))
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError, json.JSONDecodeError) as e:
        print(f"rein_benchmark: error: {e}", file=sys.stderr); return 2


if __name__ == "__main__": raise SystemExit(main())
