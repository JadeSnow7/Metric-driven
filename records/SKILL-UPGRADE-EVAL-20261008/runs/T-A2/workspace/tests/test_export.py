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

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def read_rows(self, path):
        with open(path, encoding="utf-8", newline="") as handle:
            return list(csv.reader(handle))

    def test_export_via_cli_with_awkward_titles(self):
        titles = [
            "plain",
            "a, b",
            'say "hi"',
            'both, "x"',
            'unclosed " quote',
            "line1\nline2",
            "中文，标题",
            "",
            "x" * 5000,
        ]
        save([{"title": t, "done": i % 2 == 1} for i, t in enumerate(titles)])
        path = self.root / "out.csv"
        code, _, _ = self.cli("export", str(path))
        self.assertEqual(code, 0)
        rows = self.read_rows(path)
        self.assertEqual(rows[0], ["title", "done"])
        self.assertEqual([r[0] for r in rows[1:]], titles)
        self.assertEqual([r[1] for r in rows[1:]], ["true" if i % 2 else "false" for i in range(len(titles))])

    def test_empty_store_writes_header_only(self):
        path = self.root / "out.csv"
        self.assertEqual(self.cli("export", str(path))[0], 0)
        self.assertEqual(self.read_rows(path), [["title", "done"]])

    def test_overwrites_existing_file(self):
        path = self.root / "out.csv"
        path.write_text("old,stuff\n" * 10, encoding="utf-8")
        save([{"title": "new", "done": False}])
        self.assertEqual(self.cli("export", str(path))[0], 0)
        self.assertEqual(self.read_rows(path), [["title", "done"], ["new", "false"]])

    def test_missing_or_extra_path_is_usage_error(self):
        self.assertEqual(self.cli("export")[0], 2)
        self.assertEqual(self.cli("export", "a.csv", "b.csv")[0], 2)

    def test_unwritable_path_reports_error_without_traceback(self):
        code, _, err = self.cli("export", str(self.root / "missing-dir" / "out.csv"))
        self.assertEqual(code, 1)
        self.assertIn("export:", err)


if __name__ == "__main__":
    unittest.main()
