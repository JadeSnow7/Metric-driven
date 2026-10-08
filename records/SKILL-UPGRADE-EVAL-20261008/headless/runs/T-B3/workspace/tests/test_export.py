import csv
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from todo.cli import main
from todo.store import save

ROOT = Path(__file__).resolve().parent.parent


def read_rows(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.dir = Path(self.directory.name)
        self.todo_file = self.dir / "todo.json"
        os.environ["TODO_FILE"] = str(self.todo_file)
        self.out = self.dir / "out.csv"

    def tearDown(self):
        os.environ.pop("TODO_FILE", None)
        self.directory.cleanup()

    def run_cli(self, *argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(list(argv))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_exports_title_and_done_columns(self):
        save([{"title": "buy milk", "done": False}, {"title": "pay rent", "done": True}])
        code, _, _ = self.run_cli("export", str(self.out))
        self.assertEqual(code, 0)
        self.assertEqual(
            read_rows(self.out),
            [["title", "done"], ["buy milk", "false"], ["pay rent", "true"]],
        )

    def test_commas_quotes_newlines_and_unicode_round_trip(self):
        titles = [
            "eggs, milk, bread",
            'say "hi"',
            '"quoted, start',
            'unclosed " quote',
            "line1\nline2",
            "  padded  ",
            "买牛奶，加糖",
            "",
        ]
        save([{"title": t, "done": False} for t in titles])
        self.assertEqual(self.run_cli("export", str(self.out))[0], 0)
        rows = read_rows(self.out)
        self.assertEqual(rows[0], ["title", "done"])
        self.assertEqual([r[0] for r in rows[1:]], titles)
        self.assertTrue(all(len(r) == 2 for r in rows))

    def test_empty_store_writes_header_only(self):
        self.assertEqual(self.run_cli("export", str(self.out))[0], 0)
        self.assertEqual(read_rows(self.out), [["title", "done"]])

    def test_overwrites_existing_file(self):
        self.out.write_text("stale,content\nfoo,bar\n", encoding="utf-8")
        save([{"title": "a", "done": False}])
        self.assertEqual(self.run_cli("export", str(self.out))[0], 0)
        self.assertEqual(read_rows(self.out), [["title", "done"], ["a", "false"]])

    def test_missing_path_is_usage_error(self):
        code, _, _ = self.run_cli("export")
        self.assertEqual(code, 2)

    def test_extra_arguments_are_usage_error(self):
        code, _, _ = self.run_cli("export", str(self.out), "extra")
        self.assertEqual(code, 2)
        self.assertFalse(self.out.exists())

    def test_unwritable_path_reports_error_without_traceback(self):
        bad = self.dir / "no_such_dir" / "out.csv"
        code, _, stderr = self.run_cli("export", str(bad))
        self.assertEqual(code, 1)
        self.assertIn("export:", stderr)

    def test_does_not_modify_store(self):
        save([{"title": "a", "done": True}])
        before = self.todo_file.read_text(encoding="utf-8")
        self.run_cli("export", str(self.out))
        self.assertEqual(self.todo_file.read_text(encoding="utf-8"), before)

    def test_end_to_end_via_python_m_todo(self):
        env = dict(os.environ, TODO_FILE=str(self.todo_file))
        run = lambda *args: subprocess.run(
            [sys.executable, "-m", "todo", *args],
            cwd=ROOT, env=env, capture_output=True, text=True,
        )
        self.assertEqual(run("add", 'a, "b"').returncode, 0)
        result = run("export", str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(read_rows(self.out), [["title", "done"], ['a, "b"', "false"]])


if __name__ == "__main__":
    unittest.main()
