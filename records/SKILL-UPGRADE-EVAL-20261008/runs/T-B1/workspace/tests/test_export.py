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
        self.dir = Path(self.directory.name)
        os.environ["TODO_FILE"] = str(self.dir / "todo.json")

    def tearDown(self):
        os.environ.pop("TODO_FILE", None)
        self.directory.cleanup()

    def export(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(["export", *args])
        return code, out.getvalue(), err.getvalue()

    def read_rows(self, path):
        # newline="" so embedded newlines in quoted fields are preserved
        with open(path, encoding="utf-8", newline="") as f:
            return list(csv.reader(f))

    def test_export_writes_header_and_rows(self):
        save([{"title": "buy milk", "done": False}, {"title": "call mom", "done": True}])
        target = self.dir / "out.csv"
        code, _, _ = self.export(str(target))
        self.assertEqual(code, 0)
        self.assertEqual(
            self.read_rows(target),
            [["title", "done"], ["buy milk", "false"], ["call mom", "true"]],
        )

    def test_titles_with_commas_quotes_newlines_and_unicode_round_trip(self):
        titles = [
            'a,b',
            'say "hi"',
            '"leading quote',
            'unclosed " quote, and comma',
            'two\nlines',
            '买牛奶,面包',
            ' padded ',
            ',',
            '',
        ]
        save([{"title": t, "done": i % 2 == 0} for i, t in enumerate(titles)])
        target = self.dir / "out.csv"
        self.assertEqual(self.export(str(target))[0], 0)
        rows = self.read_rows(target)
        self.assertEqual(rows[0], ["title", "done"])
        self.assertEqual([r[0] for r in rows[1:]], titles)
        self.assertEqual([r[1] for r in rows[1:]], ["true" if i % 2 == 0 else "false" for i in range(len(titles))])

    def test_empty_list_writes_header_only(self):
        target = self.dir / "out.csv"
        self.assertEqual(self.export(str(target))[0], 0)
        self.assertEqual(self.read_rows(target), [["title", "done"]])

    def test_existing_file_is_overwritten(self):
        target = self.dir / "out.csv"
        target.write_text("old,stuff\n" * 10, encoding="utf-8")
        save([{"title": "x", "done": False}])
        self.assertEqual(self.export(str(target))[0], 0)
        self.assertEqual(self.read_rows(target), [["title", "done"], ["x", "false"]])

    def test_does_not_modify_todo_data(self):
        save([{"title": "x", "done": False}])
        before = (self.dir / "todo.json").read_bytes()
        self.export(str(self.dir / "out.csv"))
        self.assertEqual((self.dir / "todo.json").read_bytes(), before)

    def test_missing_path_is_usage_error(self):
        code, _, err = self.export()
        self.assertEqual(code, 2)
        self.assertIn("export", err)

    def test_extra_arguments_are_usage_error(self):
        code, _, _ = self.export(str(self.dir / "a.csv"), str(self.dir / "b.csv"))
        self.assertEqual(code, 2)
        self.assertFalse((self.dir / "a.csv").exists())

    def test_unwritable_path_reports_error_without_traceback(self):
        save([{"title": "x", "done": False}])
        code, _, err = self.export(str(self.dir / "no_such_dir" / "out.csv"))
        self.assertEqual(code, 1)
        self.assertIn("export:", err)

    def test_directory_as_path_reports_error(self):
        code, _, err = self.export(str(self.dir))
        self.assertEqual(code, 1)
        self.assertIn("export:", err)


if __name__ == "__main__":
    unittest.main()
