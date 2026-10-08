import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from todo.cli import main


class CliTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        os.environ["TODO_FILE"] = str(Path(self.directory.name) / "todo.json")

    def tearDown(self):
        os.environ.pop("TODO_FILE", None)
        self.directory.cleanup()

    def run_cli(self, *argv):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(list(argv))
        return code, output.getvalue()

    def test_add_then_list(self):
        self.assertEqual(self.run_cli("add", "buy", "milk")[0], 0)
        code, output = self.run_cli("list")
        self.assertEqual(code, 0)
        self.assertIn("[ ] buy milk", output)

    def test_unknown_command_shows_usage(self):
        self.assertEqual(main(["nope"]), 2)


if __name__ == "__main__":
    unittest.main()
