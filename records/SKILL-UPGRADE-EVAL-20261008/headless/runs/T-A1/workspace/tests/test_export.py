import csv
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
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
        with redirect_stdout(StringIO()):
            return main(list(argv))

    def read_rows(self, path):
        with open(path, encoding="utf-8", newline="") as handle:
            return list(csv.reader(handle))

    def test_commas_quotes_and_newlines_round_trip(self):
        titles = ['buy milk, eggs', 'say "hi"', 'a,"b",c', 'two\nlines', '"', '买牛奶，鸡蛋']
        save([{"title": t, "done": i % 2 == 0} for i, t in enumerate(titles)])
        out = self.root / "out.csv"
        self.assertEqual(self.run_cli("export", str(out)), 0)
        rows = self.read_rows(out)
        self.assertEqual(rows[0], ["title", "done"])
        self.assertEqual(rows[1:], [[t, "true" if i % 2 == 0 else "false"] for i, t in enumerate(titles)])

    def test_empty_list_writes_header_only(self):
        out = self.root / "out.csv"
        self.assertEqual(self.run_cli("export", str(out)), 0)
        self.assertEqual(self.read_rows(out), [["title", "done"]])

    def test_overwrites_existing_file(self):
        out = self.root / "out.csv"
        out.write_text("stale\n" * 10, encoding="utf-8")
        save([{"title": "x", "done": False}])
        self.run_cli("export", str(out))
        self.assertEqual(self.read_rows(out), [["title", "done"], ["x", "false"]])

    def test_missing_or_extra_path_is_usage_error(self):
        self.assertEqual(self.run_cli("export"), 2)
        self.assertEqual(self.run_cli("export", "a", "b"), 2)

    def test_unwritable_path_returns_error(self):
        self.assertEqual(self.run_cli("export", str(self.root / "no_such_dir" / "out.csv")), 1)


if __name__ == "__main__":
    unittest.main()
