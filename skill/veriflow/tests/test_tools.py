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


if __name__ == "__main__":
    unittest.main()
