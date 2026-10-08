import csv
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from todo.cli import main
from todo.store import save


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        os.environ["TODO_FILE"] = str(self.root / "todo.json")

    def tearDown(self):
        os.environ.pop("TODO_FILE", None)
        self.directory.cleanup()

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def read_rows(self, path):
        with open(path, encoding="utf-8", newline="") as handle:
            return list(csv.reader(handle))

    def test_export_writes_header_and_rows(self):
        save([{"title": "buy milk", "done": False}, {"title": "写报告", "done": True}])
        target = self.root / "out.csv"
        code, _, _ = self.run_cli("export", str(target))
        self.assertEqual(code, 0)
        self.assertEqual(
            self.read_rows(target),
            [["title", "done"], ["buy milk", "false"], ["写报告", "true"]],
        )

    def test_commas_quotes_and_newlines_round_trip(self):
        titles = ['a, b', 'say "hi"', '"quoted", and, more', 'unclosed " quote', "two\nlines", ""]
        save([{"title": t, "done": False} for t in titles])
        target = self.root / "out.csv"
        self.assertEqual(self.run_cli("export", str(target))[0], 0)
        rows = self.read_rows(target)
        self.assertEqual([r[0] for r in rows[1:]], titles)
        self.assertTrue(all(len(r) == 2 for r in rows))

    def test_empty_list_writes_header_only(self):
        target = self.root / "out.csv"
        self.assertEqual(self.run_cli("export", str(target))[0], 0)
        self.assertEqual(self.read_rows(target), [["title", "done"]])

    def test_overwrites_existing_file(self):
        target = self.root / "out.csv"
        target.write_text("stale,data\nfoo,bar\n", encoding="utf-8")
        save([{"title": "x", "done": True}])
        self.assertEqual(self.run_cli("export", str(target))[0], 0)
        self.assertEqual(self.read_rows(target), [["title", "done"], ["x", "true"]])

    def test_missing_path_is_usage_error_and_writes_nothing(self):
        code, _, err = self.run_cli("export")
        self.assertEqual(code, 2)
        self.assertIn("export", err)

    def test_too_many_args_is_usage_error(self):
        self.assertEqual(self.run_cli("export", "a.csv", "b.csv")[0], 2)

    def test_unwritable_path_reports_error_not_traceback(self):
        target = self.root / "no-such-dir" / "out.csv"
        code, out, err = self.run_cli("export", str(target))
        self.assertEqual(code, 1)
        self.assertNotIn("exported", out)
        self.assertTrue(err)


if __name__ == "__main__":
    unittest.main()
