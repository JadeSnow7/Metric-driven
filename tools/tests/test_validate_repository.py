from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
from validate_repository import is_maintained_document, visible_markdown  # noqa: E402


class ValidateRepositoryTests(unittest.TestCase):
    def test_only_task_experiment_and_snapshot_trees_are_excluded(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.assertTrue(is_maintained_document(root, root / "skill/references/experiments/example.md"))
        self.assertFalse(is_maintained_document(root, root / "records/REIN-CH05-16/snapshots/x.md"))
        self.assertFalse(is_maintained_document(root, root / "records/REIN-CH05-16/experiments/x.md"))
        self.assertTrue(is_maintained_document(root, root / "records/OTHER/experiments/x.md"))
        self.assertTrue(is_maintained_document(root, root / "records/REIN-CH05-16/evidence/experiments/x.md"))

    def test_archived_product_copies_are_excluded_but_live_summaries_are_checked(self) -> None:
        root = Path(tempfile.mkdtemp())
        archived = (
            "records/REIN-CH05-16/production/ch06/final-evidence/body-evidence/"
            "body-v1-preserved/06.md"
        )
        sealed = "records/REIN-CH08-EDD-20260915/formal/seals/A/work/docs/chapters/04.md"
        self.assertFalse(is_maintained_document(root, root / archived))
        self.assertFalse(is_maintained_document(root, root / sealed))
        self.assertTrue(is_maintained_document(root, root / "records/REIN-CH08-EDD-20260915/task-summary.md"))

    def test_code_examples_are_not_scanned_but_real_links_remain_visible(self) -> None:
        text = """```
[missing fenced](missing-fenced.md)
```\nInline `[missing inline](missing-inline.md)`\nReal [missing real](missing-real.md)"""
        visible = visible_markdown(text)
        self.assertNotIn("missing-fenced.md", visible)
        self.assertNotIn("missing-inline.md", visible)
        self.assertIn("missing-real.md", visible)


if __name__ == "__main__":
    unittest.main()
