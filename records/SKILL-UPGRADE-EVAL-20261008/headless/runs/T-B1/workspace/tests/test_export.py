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


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.dir = Path(self.directory.name)
        os.environ["TODO_FILE"] = str(self.dir / "todo.json")
        self.out = self.dir / "out.csv"

    def tearDown(self):
        os.environ.pop("TODO_FILE", None)
        self.directory.cleanup()

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def read_rows(self):
        with open(self.out, encoding="utf-8", newline="") as handle:
            return list(csv.reader(handle))

    def test_export_registered_and_writes_header_and_rows(self):
        save([{"title": "buy milk", "done": False}, {"title": "写报告", "done": True}])
        code, _, _ = self.run_cli("export", str(self.out))
        self.assertEqual(code, 0)
        self.assertEqual(
            self.read_rows(),
            [["title", "done"], ["buy milk", "false"], ["写报告", "true"]],
        )

    def test_commas_quotes_and_newlines_round_trip(self):
        titles = ['a, b', 'say "hi"', '"', 'x,"y",z', 'line1\nline2', ' padded ', '']
        save([{"title": t, "done": False} for t in titles])
        self.assertEqual(self.run_cli("export", str(self.out))[0], 0)
        self.assertEqual([r[0] for r in self.read_rows()[1:]], titles)

    def test_raw_bytes_are_rfc4180_quoted(self):
        save([{"title": 'a,"b"', "done": True}])
        self.run_cli("export", str(self.out))
        self.assertEqual(self.out.read_bytes(), b'title,done\r\n"a,""b""",true\r\n')

    def test_empty_store_writes_header_only(self):
        self.assertEqual(self.run_cli("export", str(self.out))[0], 0)
        self.assertEqual(self.read_rows(), [["title", "done"]])

    def test_overwrites_existing_file(self):
        self.out.write_text("stale,stale\nstale,stale\n")
        save([{"title": "new", "done": False}])
        self.run_cli("export", str(self.out))
        self.assertEqual(self.read_rows(), [["title", "done"], ["new", "false"]])

    def test_missing_path_is_usage_error(self):
        code, _, err = self.run_cli("export")
        self.assertEqual(code, 2)
        self.assertIn("export", err)

    def test_extra_args_is_usage_error(self):
        code, _, _ = self.run_cli("export", str(self.out), "extra")
        self.assertEqual(code, 2)
        self.assertFalse(self.out.exists())

    def test_unwritable_path_reports_error_without_traceback(self):
        save([{"title": "x", "done": False}])
        code, _, err = self.run_cli("export", str(self.dir / "no_such_dir" / "out.csv"))
        self.assertEqual(code, 1)
        self.assertIn("export", err)

    def test_does_not_modify_store(self):
        save([{"title": "keep", "done": False}])
        before = (self.dir / "todo.json").read_bytes()
        self.run_cli("export", str(self.out))
        self.assertEqual((self.dir / "todo.json").read_bytes(), before)

    def test_python_dash_m_end_to_end(self):
        save([{"title": 'a,"b"', "done": True}])
        env = dict(os.environ)
        result = subprocess.run(
            [sys.executable, "-m", "todo", "export", str(self.out)],
            cwd=ROOT, env=env, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.read_rows(), [["title", "done"], ['a,"b"', "true"]])


if __name__ == "__main__":
    unittest.main()
