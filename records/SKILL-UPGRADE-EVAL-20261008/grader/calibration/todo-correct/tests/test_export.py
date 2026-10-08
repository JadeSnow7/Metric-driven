import tempfile
import unittest
from pathlib import Path

from todo.commands import export


class ExportTests(unittest.TestCase):
    def test_export_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(export.run([str(Path(directory) / "out.csv")]), 0)


if __name__ == "__main__":
    unittest.main()
