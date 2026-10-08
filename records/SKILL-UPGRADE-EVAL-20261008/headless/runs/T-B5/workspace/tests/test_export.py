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

    def test_export_via_cli_round_trips_awkward_titles(self):
        titles = [
            "buy milk",
            "eggs, bread, butter",
            'say "hello"',
            'both, "quoted", here',
            "line1\nline2",
            "买牛奶，加冰",
            '"',
            "",
        ]
        save([{"title": t, "done": i % 2 == 1} for i, t in enumerate(titles)])
        out = self.root / "out.csv"
        code, _, _ = self.run_cli("export", str(out))
        self.assertEqual(code, 0)
        rows = self.read_rows(out)
        self.assertEqual(rows[0], ["title", "done"])
        self.assertEqual(
            rows[1:],
            [[t, "true" if i % 2 == 1 else "false"] for i, t in enumerate(titles)],
        )

    def test_export_empty_list_writes_header_only(self):
        out = self.root / "out.csv"
        self.assertEqual(self.run_cli("export", str(out))[0], 0)
        self.assertEqual(self.read_rows(out), [["title", "done"]])

    def test_export_overwrites_existing_file(self):
        out = self.root / "out.csv"
        out.write_text("stale,content\n" * 5, encoding="utf-8")
        save([{"title": "a", "done": False}])
        self.assertEqual(self.run_cli("export", str(out))[0], 0)
        self.assertEqual(self.read_rows(out), [["title", "done"], ["a", "false"]])

    def test_export_missing_path_is_usage_error(self):
        code, _, err = self.run_cli("export")
        self.assertEqual(code, 2)
        self.assertIn("export", err)

    def test_export_extra_args_is_usage_error(self):
        out = self.root / "out.csv"
        code, _, _ = self.run_cli("export", str(out), "extra")
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())

    def test_export_unwritable_path_reports_error(self):
        code, _, err = self.run_cli("export", str(self.root / "no_such_dir" / "out.csv"))
        self.assertEqual(code, 1)
        self.assertIn("export", err)

    def test_export_does_not_modify_data_file(self):
        save([{"title": "a", "done": True}])
        before = (self.root / "todo.json").read_bytes()
        self.run_cli("export", str(self.root / "out.csv"))
        self.assertEqual((self.root / "todo.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
