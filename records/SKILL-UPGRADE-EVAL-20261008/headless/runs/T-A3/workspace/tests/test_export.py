import csv
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
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
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(list(argv))
        return code, output.getvalue()

    def read_rows(self, path):
        with open(path, encoding="utf-8", newline="") as handle:
            return list(csv.reader(handle))

    def test_exports_through_cli_entrypoint(self):
        save([{"title": "buy milk", "done": False}, {"title": "写报告", "done": True}])
        out = self.root / "out.csv"
        code, _ = self.run_cli("export", str(out))
        self.assertEqual(code, 0)
        self.assertEqual(
            self.read_rows(out),
            [["title", "done"], ["buy milk", "false"], ["写报告", "true"]],
        )

    def test_commas_quotes_and_newlines_round_trip(self):
        titles = ['a, b', 'say "hi"', '"', 'x,"y",z', 'line1\nline2', ' padded ', '=1+1', '']
        save([{"title": t, "done": False} for t in titles])
        out = self.root / "out.csv"
        self.assertEqual(self.run_cli("export", str(out))[0], 0)
        rows = self.read_rows(out)
        self.assertEqual([r[0] for r in rows[1:]], titles)

    def test_empty_list_writes_header_only(self):
        out = self.root / "out.csv"
        self.assertEqual(self.run_cli("export", str(out))[0], 0)
        self.assertEqual(self.read_rows(out), [["title", "done"]])

    def test_overwrites_existing_file(self):
        out = self.root / "out.csv"
        out.write_text("old,old\n" * 10, encoding="utf-8")
        save([{"title": "new", "done": True}])
        self.run_cli("export", str(out))
        self.assertEqual(self.read_rows(out), [["title", "done"], ["new", "true"]])

    def test_wrong_arg_count_is_usage_error(self):
        self.assertEqual(self.run_cli("export")[0], 2)
        self.assertEqual(self.run_cli("export", "a.csv", "b.csv")[0], 2)

    def test_unwritable_path_reports_error(self):
        code, output = self.run_cli("export", str(self.root / "missing" / "out.csv"))
        self.assertEqual(code, 1)
        self.assertIn("cannot write", output)


if __name__ == "__main__":
    unittest.main()
