from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORDER = ROOT / "scripts/record_execution.py"
INTEGRATOR = ROOT / "scripts/integrate_boundary.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ToolBehaviorTests(unittest.TestCase):
    def test_execution_records_failure_timeout_and_empty_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.py"
            source.write_text("x\n", encoding="utf-8")
            failed = root / "failed.json"
            result = subprocess.run([sys.executable, str(RECORDER), "--output", str(failed), "--source", str(source), "--", sys.executable, "-c", "import sys; sys.exit(3)"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 3)
            record = json.loads(failed.read_text())
            self.assertEqual(record["exit_code"], 3)
            self.assertEqual(record["result"], "failed")
            self.assertFalse(record["stdout_present"])
            timed = root / "timeout.json"
            result = subprocess.run([sys.executable, str(RECORDER), "--output", str(timed), "--timeout", "0.2", "--", sys.executable, "-c", "import sys,time; sys.stdout.buffer.write(b'prefix\\xff'); sys.stdout.flush(); time.sleep(1)"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 124)
            timeout_record = json.loads(timed.read_text())
            self.assertTrue(timeout_record["timed_out"])
            self.assertEqual(timeout_record["stdout_base64"], "cHJlZml4/w==")
            missing = root / "missing.json"
            result = subprocess.run([sys.executable, str(RECORDER), "--output", str(missing), "--", "command-that-does-not-exist"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 127)
            self.assertEqual(json.loads(missing.read_text())["result"], "failed")
            mismatch = root / "mismatch.json"
            result = subprocess.run([sys.executable, str(RECORDER), "--output", str(mismatch), "--expect-argv", "wrong", "--", sys.executable, "-c", "print(1)"], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(mismatch.exists())
            mismatch.write_text("sentinel")
            result = subprocess.run([sys.executable, str(RECORDER), "--output", str(mismatch), "--", sys.executable, "-c", "print(1)"], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(mismatch.read_text(), "sentinel")
            required = root / "required.json"
            result = subprocess.run([sys.executable, str(RECORDER), "--output", str(required), "--require-stdout", "--", sys.executable, "-c", "pass"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(required.read_text())["result"], "missing_output")

    def test_integration_rejects_scope_drift_and_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, target = root / "source", root / "target"
            for repo in (source, target):
                repo.mkdir()
                subprocess.run(["git", "init", "-q", str(repo)], check=True)
                subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.invalid"], check=True)
                subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
            (source / "ok.txt").write_text("source\n")
            subprocess.run(["git", "-C", str(source), "add", "ok.txt"], check=True)
            subprocess.run(["git", "-C", str(source), "commit", "-qm", "base"], check=True)
            subprocess.run(["git", "-C", str(target), "commit", "--allow-empty", "-qm", "base"], check=True)
            src_head = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
            target_head = subprocess.check_output(["git", "-C", str(target), "rev-parse", "HEAD"], text=True).strip()
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"source_root": str(source), "target_root": str(target), "files": {"ok.txt": {"source": "ok.txt", "source_sha256": sha(source / "ok.txt"), "target_sha256": "absent"}}}))
            command = [sys.executable, str(INTEGRATOR), "--source-root", str(source), "--target-root", str(target), "--manifest", str(manifest), "--source-revision", src_head, "--target-base", target_head, "--allowed-path", "ok.txt"]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            (target / "ok.txt").write_text("different\n")
            manifest.write_text(json.dumps({"source_root": str(source), "target_root": str(target), "files": {"ok.txt": {"source": "ok.txt", "source_sha256": sha(source / "ok.txt"), "target_sha256": sha(source / "ok.txt")}}}))
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual((target / "ok.txt").read_text(), "different\n")

    def test_integration_preflights_all_files_and_rejects_parent_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, target = root / "source", root / "target"
            for repo in (source, target):
                repo.mkdir(); subprocess.run(["git", "init", "-q", str(repo)], check=True)
                subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.invalid"], check=True)
                subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
            (source / "a.txt").write_text("a\n"); (source / "b.txt").write_text("b\n")
            subprocess.run(["git", "-C", str(source), "add", "."], check=True); subprocess.run(["git", "-C", str(source), "commit", "-qm", "base"], check=True)
            subprocess.run(["git", "-C", str(target), "commit", "--allow-empty", "-qm", "base"], check=True)
            sh = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip(); th = subprocess.check_output(["git", "-C", str(target), "rev-parse", "HEAD"], text=True).strip()
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"source_root": str(source), "target_root": str(target), "files": {"a.txt": {"source": "a.txt", "source_sha256": sha(source / "a.txt"), "target_sha256": "absent"}, "b.txt": {"source": "b.txt", "source_sha256": sha(source / "b.txt"), "target_sha256": "absent"}}}))
            command = [sys.executable, str(INTEGRATOR), "--source-root", str(source), "--target-root", str(target), "--manifest", str(manifest), "--source-revision", sh, "--target-base", th, "--allowed-path", "."]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            before = (target / "a.txt").read_text()
            manifest.write_text(json.dumps({"source_root": str(source), "target_root": str(target), "files": {"a.txt": {"source": "a.txt", "source_sha256": sha(source / "a.txt"), "target_sha256": sha(target / "a.txt")}, "b.txt": {"source": "b.txt", "source_sha256": "wrong", "target_sha256": "absent"}}}))
            failed = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0); self.assertEqual((target / "a.txt").read_text(), before)
            outside = root / "outside"; outside.mkdir(); (target / "link").symlink_to(outside, target_is_directory=True)
            manifest.write_text(json.dumps({"source_root": str(source), "target_root": str(target), "files": {"link/a.txt": {"source": "a.txt", "source_sha256": sha(source / "a.txt"), "target_sha256": "absent"}}}))
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0); self.assertFalse((outside / "a.txt").exists())

    def test_integration_each_boundary_failure_reports_specific_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source, target = root / "source", root / "target"
            for repo in (source, target):
                repo.mkdir(); subprocess.run(["git", "init", "-q", str(repo)], check=True)
                subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.invalid"], check=True); subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
            (source / "item.txt").write_text("new\n"); subprocess.run(["git", "-C", str(source), "add", "."], check=True); subprocess.run(["git", "-C", str(source), "commit", "-qm", "base"], check=True)
            (target / "item.txt").write_text("old\n"); subprocess.run(["git", "-C", str(target), "add", "."], check=True); subprocess.run(["git", "-C", str(target), "commit", "-qm", "base"], check=True)
            sh = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip(); th = subprocess.check_output(["git", "-C", str(target), "rev-parse", "HEAD"], text=True).strip()
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"source_root": str(source), "target_root": str(target), "files": {"item.txt": {"source": "item.txt", "source_sha256": sha(source / "item.txt"), "target_sha256": sha(target / "item.txt")}}}))
            base = [sys.executable, str(INTEGRATOR), "--source-root", str(source), "--target-root", str(target), "--manifest", str(manifest), "--source-revision", sh, "--target-base", th, "--allowed-path", "item.txt"]
            good = subprocess.run(base, capture_output=True, text=True); self.assertEqual(good.returncode, 0, good.stderr); self.assertEqual((target / "item.txt").read_text(), "new\n")
            # Recreate the expected old target and perturb exactly one contract field per run.
            (target / "item.txt").write_text("old\n")
            for field, value, needle in (("source_root", str(root / "wrong-source"), "source root identity"), ("target_root", str(root / "wrong-target"), "target root identity")):
                data = json.loads(manifest.read_text()); data[field] = value; manifest.write_text(json.dumps(data)); failed = subprocess.run(base, capture_output=True, text=True); self.assertNotEqual(failed.returncode, 0); self.assertIn(needle, failed.stdout); self.assertEqual((target / "item.txt").read_text(), "old\n"); data[field] = str(source if field == "source_root" else target); manifest.write_text(json.dumps(data))
            bad = base.copy(); bad[bad.index("--source-revision") + 1] = "deadbeef"; failed = subprocess.run(bad, capture_output=True, text=True); self.assertIn("source revision drifted", failed.stdout); self.assertEqual((target / "item.txt").read_text(), "old\n")
            data = json.loads(manifest.read_text()); data["files"]["item.txt"]["source_sha256"] = "0" * 64; manifest.write_text(json.dumps(data)); failed = subprocess.run(base, capture_output=True, text=True); self.assertIn("source hash drifted", failed.stdout); self.assertEqual((target / "item.txt").read_text(), "old\n")
            data["files"]["item.txt"]["source_sha256"] = sha(source / "item.txt"); manifest.write_text(json.dumps(data)); failed = subprocess.run([*base[:-1], "other.txt"], capture_output=True, text=True); self.assertIn("outside allowed scope", failed.stdout); self.assertEqual((target / "item.txt").read_text(), "old\n")

    def test_result_precedence_and_launch_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            both = root / "timeout-and-empty.json"
            result = subprocess.run([sys.executable, str(RECORDER), "--output", str(both), "--timeout", "0.2", "--require-stdout", "--", sys.executable, "-c", "import time; time.sleep(2)"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 124)
            self.assertEqual(json.loads(both.read_text())["result"], "timeout")
            script = root / "not-executable.sh"
            script.write_text("#!/bin/sh\necho hi\n")
            script.chmod(0o644)
            denied = root / "denied.json"
            result = subprocess.run([sys.executable, str(RECORDER), "--output", str(denied), "--", str(script)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 126)
            record = json.loads(denied.read_text())
            self.assertEqual((record["result"], record["wrapper_exit_code"]), ("failed", 126))
            for flag in ("--repo", "--state"):
                with self.subTest(flag):
                    output = root / f"half-{flag.strip('-')}.json"
                    result = subprocess.run([sys.executable, str(RECORDER), "--output", str(output), flag, str(root), "--", sys.executable, "-c", "print(1)"], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2)
                    self.assertFalse(output.exists())

    def test_recorder_refuses_destination_created_by_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "record.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(RECORDER),
                    "--output",
                    str(output),
                    "--",
                    sys.executable,
                    "-c",
                    f"open({str(output)!r}, 'w').write('command artifact')",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(output.read_text(), "command artifact")
            self.assertIn("refusing overwrite", result.stderr)

            dangling = root / "dangling.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(RECORDER),
                    "--output",
                    str(dangling),
                    "--",
                    sys.executable,
                    "-c",
                    f"import os; os.symlink('missing-target', {str(dangling)!r})",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertTrue(dangling.is_symlink())

    def test_recorder_preserves_empty_command_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "record.json"
            result = subprocess.run(
                [sys.executable, str(RECORDER), "--output", str(output), "--", sys.executable, "-c", ""],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text())["argv"][-1], "")

    def test_revision_binding_matches_validator_and_detects_changes_during_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
            (repo / "app.txt").write_text("base\n")
            subprocess.run(["git", "-C", str(repo), "add", "app.txt"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
            head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
            (repo / "app.txt").write_text("implemented\n")
            state = json.loads((ROOT / "assets/templates/task-state.example.json").read_text(encoding="utf-8"))
            state["baseline"]["git_ref"] = head
            manifest = repo / "records/TASK-001/task-state.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps(state))
            token = subprocess.run([sys.executable, str(ROOT / "scripts/validate_task.py"), str(manifest), "--repo", str(repo), "--print-revision"], capture_output=True, text=True, check=True).stdout.strip()

            steady = manifest.parent / "evidence/steady.json"
            result = subprocess.run([sys.executable, str(RECORDER), "--output", str(steady), "--repo", str(repo), "--state", str(manifest), "--cwd", str(repo), "--source", "app.txt", "--", sys.executable, "-c", "print('ok')"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads(steady.read_text())
            self.assertEqual((record["revision_before"], record["revision_after"], record["revision"]), (token, token, token))
            self.assertEqual(list(record["inputs"]), ["app.txt"])
            self.assertEqual((record["cwd_relative"], record["result"]), (".", "passed"))

            drift = manifest.parent / "evidence/drift.json"
            result = subprocess.run([sys.executable, str(RECORDER), "--output", str(drift), "--repo", str(repo), "--state", str(manifest), "--cwd", str(repo), "--", sys.executable, "-c", "open('app.txt', 'w').write('changed by the check')"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            record = json.loads(drift.read_text())
            self.assertEqual(record["result"], "revision_changed")
            self.assertIsNone(record["revision"])
            self.assertEqual(record["revision_changed_paths"], ["app.txt"])
            self.assertIn("app.txt", result.stderr)

            generated = manifest.parent / "evidence/generated.json"
            result = subprocess.run([sys.executable, str(RECORDER), "--output", str(generated), "--repo", str(repo), "--state", str(manifest), "--cwd", str(repo), "--", sys.executable, "-c", "import os; os.makedirs('build', exist_ok=True); open('build/out.txt', 'w').write('x')"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(generated.read_text())["revision_changed_paths"], ["build/out.txt"])
            (repo / ".gitignore").write_text("build/\n")
            subprocess.run(["git", "-C", str(repo), "add", ".gitignore"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "ignore build output"], check=True)
            state["baseline"]["git_ref"] = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
            manifest.write_text(json.dumps(state))
            ignored = manifest.parent / "evidence/ignored.json"
            result = subprocess.run([sys.executable, str(RECORDER), "--output", str(ignored), "--repo", str(repo), "--state", str(manifest), "--cwd", str(repo), "--", sys.executable, "-c", "open('build/out.txt', 'w').write('y')"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(ignored.read_text())["revision_changed_paths"], [])
            self.assertNotEqual(record["revision_before"], record["revision_after"])

            missing_base = json.loads(json.dumps(state))
            missing_base["baseline"]["git_ref"] = "0" * 40
            broken = manifest.parent / "broken-state.json"
            broken.write_text(json.dumps(missing_base))
            never = manifest.parent / "evidence/never.json"
            marker = repo / "ran.txt"
            result = subprocess.run([sys.executable, str(RECORDER), "--output", str(never), "--repo", str(repo), "--state", str(broken), "--", sys.executable, "-c", f"open({str(marker)!r}, 'w').write('x')"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(never.exists())
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
