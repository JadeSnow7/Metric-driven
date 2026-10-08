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

    def test_export_through_cli_with_special_titles(self):
        titles = [
            "plain",
            'say "hi", then leave',
            'unclosed " quote',
            "multi\nline",
            "中文,标题",
            "",
        ]
        save([{"title": t, "done": i % 2 == 1} for i, t in enumerate(titles)])
        out = self.root / "out.csv"
        code, _ = self.run_cli("export", str(out))
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
        out.write_text("stale,data\n" * 10, encoding="utf-8")
        save([{"title": "a", "done": False}])
        self.assertEqual(self.run_cli("export", str(out))[0], 0)
        self.assertEqual(self.read_rows(out), [["title", "done"], ["a", "false"]])

    def test_missing_or_extra_path_is_usage_error(self):
        self.assertEqual(self.run_cli("export")[0], 2)
        self.assertEqual(self.run_cli("export", "a.csv", "b.csv")[0], 2)

    def test_unwritable_path_reports_error(self):
        code, output = self.run_cli("export", str(self.root / "no_such_dir" / "out.csv"))
        self.assertEqual(code, 1)
        self.assertIn("cannot write", output)


if __name__ == "__main__":
    unittest.main()
