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

    def test_export_roundtrips_tricky_titles(self):
        items = [
            {"title": "plain", "done": False},
            {"title": "a, b", "done": True},
            {"title": 'say "hi"', "done": False},
            {"title": 'both, "x", y', "done": True},
            {"title": "line1\nline2", "done": False},
            {"title": '"', "done": False},
            {"title": "买牛奶，加糖", "done": True},
        ]
        save(items)
        target = self.root / "out.csv"
        code, _, _ = self.run_cli("export", str(target))
        self.assertEqual(code, 0)
        rows = self.read_rows(target)
        self.assertEqual(rows[0], ["title", "done"])
        self.assertEqual(
            rows[1:],
            [[i["title"], "true" if i["done"] else "false"] for i in items],
        )

    def test_empty_store_writes_header_only(self):
        target = self.root / "out.csv"
        self.assertEqual(self.run_cli("export", str(target))[0], 0)
        self.assertEqual(self.read_rows(target), [["title", "done"]])

    def test_missing_path_is_usage_error(self):
        code, _, err = self.run_cli("export")
        self.assertEqual(code, 2)
        self.assertIn("export", err)

    def test_extra_arguments_are_usage_error(self):
        code, _, _ = self.run_cli("export", "a.csv", "b.csv")
        self.assertEqual(code, 2)

    def test_unwritable_path_reports_error_without_traceback(self):
        save([{"title": "x", "done": False}])
        code, _, err = self.run_cli("export", str(self.root / "no_such_dir" / "out.csv"))
        self.assertEqual(code, 1)
        self.assertIn("export", err)

    def test_existing_file_is_overwritten(self):
        target = self.root / "out.csv"
        target.write_text("old,stuff\n" * 10, encoding="utf-8")
        save([{"title": "new", "done": False}])
        self.assertEqual(self.run_cli("export", str(target))[0], 0)
        self.assertEqual(self.read_rows(target), [["title", "done"], ["new", "false"]])

    def test_source_data_is_not_modified(self):
        save([{"title": "keep", "done": True}])
        before = Path(os.environ["TODO_FILE"]).read_bytes()
        self.run_cli("export", str(self.root / "out.csv"))
        self.assertEqual(Path(os.environ["TODO_FILE"]).read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
