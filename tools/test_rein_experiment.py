#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TOOL = Path(__file__).with_name("rein_experiment.py")


def invoke(*args):
    return subprocess.run([sys.executable, str(TOOL), *map(str, args)], text=True, capture_output=True)


class SnapshotToolTests(unittest.TestCase):
    def test_snapshot_inventory_filters_and_preserves_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
            (root / "tracked.txt").write_text("before\n")
            (root / "deleted.txt").write_text("remove\n")
            (root / ".env").write_text("TOKEN=secret\n")
            subprocess.run(["git", "-C", str(root), "add", "tracked.txt", "deleted.txt", ".env"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "baseline"], check=True)
            (root / "tracked.txt").write_text("dirty\n")
            (root / "deleted.txt").unlink()
            (root / "new.txt").write_text("untracked\n")
            (root / ".env.example").write_text("TOKEN=example\n")
            (root / "script.sh").write_text("#!/bin/sh\n")
            os.chmod(root / "script.sh", 0o755)
            (root / "node_modules").mkdir()
            (root / "node_modules" / "ignored.js").write_text("ignored\n")
            output = Path(tmp) / "snapshot"
            result = invoke("snapshot", "--source", root, "--output", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / "manifest.json").read_text())
            paths = {item["path"]: item for item in manifest["files"]}
            self.assertEqual(set(paths), {".env.example", "new.txt", "script.sh", "tracked.txt"})
            self.assertEqual(manifest["deleted_tracked"], ["deleted.txt"])
            self.assertEqual(paths["script.sh"]["mode"] & 0o111, 0o111)
            self.assertNotIn(".env", manifest["git_inventory"])

    def test_clone_seal_and_manifest_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "tree"
            tree.mkdir()
            (tree / "a.txt").write_text("a\n")
            clone = Path(tmp) / "clone"
            # seal works on arbitrary trees and records executable/hash metadata.
            first = Path(tmp) / "first.json"
            second = Path(tmp) / "second.json"
            self.assertEqual(invoke("seal", "--tree", tree, "--output", first).returncode, 0)
            (tree / "a.txt").write_text("changed\n")
            self.assertEqual(invoke("seal", "--tree", tree, "--output", second).returncode, 0)
            positive = invoke("compare-manifests", first, first)
            negative = invoke("compare-manifests", first, second)
            self.assertEqual(positive.returncode, 0, positive.stdout)
            self.assertEqual(negative.returncode, 1, negative.stdout)

    def test_nul_paths_and_external_symlink_are_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
            unusual = root / "中文 name.txt"
            unusual.write_text("safe\n")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "baseline"], check=True)
            outside = Path(tmp) / "outside.txt"
            outside.write_text("secret outside\n")
            (root / "external-link").symlink_to(outside)
            output = Path(tmp) / "snapshot"
            result = invoke("snapshot", "--source", root, "--output", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertIn("中文 name.txt", manifest["git_inventory"])
            self.assertEqual(manifest["skipped_symlinks"], ["external-link"])
            self.assertFalse((output / "files" / "external-link").exists())

    def test_seal_excludes_generated_trees_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "tree"
            (root / "target").mkdir(parents=True)
            (root / "node_modules").mkdir()
            (root / "dist").mkdir()
            (root / "source.txt").write_text("source\n")
            (root / "target" / "junk").write_text("generated\n")
            (root / "node_modules" / "junk").write_text("dependency\n")
            (root / "dist" / "junk").write_text("output\n")
            result = Path(tmp) / "seal.json"
            self.assertEqual(invoke("seal", "--tree", root, "--output", result).returncode, 0)
            paths = {entry["path"] for entry in json.loads(result.read_text())["files"]}
            self.assertEqual(paths, {"source.txt"})


if __name__ == "__main__":
    unittest.main()
