from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
from validate_repository import (  # noqa: E402
    check_claude_code,
    frontmatter,
    is_maintained_document,
    is_safe_local_link,
    broken_local_links,
    repository_root,
    visible_markdown,
)


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

    def test_local_links_reject_absolute_and_escape_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            container = Path(temporary)
            root = container / "repo"
            document = root / "docs/final.md"
            document.parent.mkdir(parents=True)
            (root / "docs/ok.md").write_text("ok", encoding="utf-8")
            outside = container / "outside-real.md"
            outside.write_text("outside", encoding="utf-8")
            (root / "docs/link.md").symlink_to(outside)
            self.assertTrue(is_safe_local_link(root, document, "ok.md"))
            self.assertFalse(is_safe_local_link(root, document, "missing.md"))
            self.assertFalse(is_safe_local_link(root, document, str(outside)))
            self.assertFalse(is_safe_local_link(root, document, "../../outside-real.md"))
            self.assertFalse(is_safe_local_link(root, document, "link.md"))
            self.assertFalse(is_safe_local_link(root, document, r"C:\\outside.md"))
            self.assertFalse(is_safe_local_link(root, document, r"\\server\\share\\outside.md"))

    def test_main_link_scan_skips_external_fragments_and_parses_angles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            container = Path(temporary)
            root = container / "repo"
            document = root / "docs/final.md"
            document.parent.mkdir(parents=True)
            outside = container / "outside-real.md"
            outside.write_text("outside", encoding="utf-8")
            (root / "docs/ok.md").write_text("ok", encoding="utf-8")
            text = "[ok](ok.md) [bad](<" + str(outside) + ">) [web](https://example.com) [fragment](#section)"
            self.assertEqual(broken_local_links(root, document, text), ["<" + str(outside) + ">"])

    def test_only_sealed_c_final_is_archived(self) -> None:
        root = Path(tempfile.mkdtemp())
        sealed = root / "records/REIN-CH08-EDD-20260915/formal/seals/C/run/final.md"
        adjacent = root / "records/REIN-CH08-EDD-20260915/formal/seals/C/run/other.md"
        self.assertFalse(is_maintained_document(root, sealed))
        self.assertTrue(is_maintained_document(root, adjacent))


class ClaudeCodeDefinitionTests(unittest.TestCase):
    def make_root(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "skill/veriflow/agents/claude-code").mkdir(parents=True)
        (root / "skill/veriflow/SKILL.md").write_text(
            "---\nname: veriflow\ndescription: verify delivery\n---\n# Veriflow\n", encoding="utf-8"
        )
        self.write_agent(root, "veriflow-coder", "sonnet", "Read, Edit, Write, Bash")
        self.write_agent(root, "veriflow-reviewer", "sonnet", "Read, Grep, Bash")
        plugin = root / "claude-code"
        (plugin / ".claude-plugin").mkdir(parents=True)
        (plugin / ".claude-plugin/plugin.json").write_text('{"name": "veriflow"}', encoding="utf-8")
        (plugin / "skills").mkdir()
        (plugin / "skills/veriflow").symlink_to("../../skill/veriflow")
        (plugin / "agents").symlink_to("../skill/veriflow/agents/claude-code")
        return root

    @staticmethod
    def write_agent(root: Path, name: str, model: str, tools: str) -> None:
        (root / f"skill/veriflow/agents/claude-code/{name}.md").write_text(
            f"---\nname: {name}\ndescription: role\nmodel: {model}\ntools: {tools}\n---\nBody\n",
            encoding="utf-8",
        )

    def test_shipped_definitions_pass(self) -> None:
        self.assertEqual(check_claude_code(repository_root()), [])

    def test_valid_fixture_passes(self) -> None:
        self.assertEqual(check_claude_code(self.make_root()), [])

    def test_subagent_must_be_pinned_to_sonnet(self) -> None:
        for model in ("inherit", "opus", ""):
            with self.subTest(model=model):
                root = self.make_root()
                self.write_agent(root, "veriflow-coder", model, "Read, Edit")
                self.assertTrue(any("model must be 'sonnet'" in e for e in check_claude_code(root)))

    def test_reviewer_is_read_only_and_agents_do_not_delegate(self) -> None:
        root = self.make_root()
        self.write_agent(root, "veriflow-reviewer", "sonnet", "Read, Edit, Bash")
        self.assertTrue(any("read-only agent" in e for e in check_claude_code(root)))
        root = self.make_root()
        self.write_agent(root, "veriflow-coder", "sonnet", "Read, Edit, Agent")
        self.assertTrue(any("must not delegate" in e for e in check_claude_code(root)))

    def test_plugin_links_must_point_at_the_shipped_skill(self) -> None:
        root = self.make_root()
        link = root / "claude-code/skills/veriflow"
        link.unlink()
        (root / "elsewhere").mkdir()
        link.symlink_to(root / "elsewhere")
        self.assertTrue(any("claude-code/skills/veriflow must resolve" in e for e in check_claude_code(root)))

    def test_skill_description_limit_and_malformed_frontmatter(self) -> None:
        root = self.make_root()
        (root / "skill/veriflow/SKILL.md").write_text(
            "---\nname: veriflow\ndescription: " + "x" * 1025 + "\n---\n", encoding="utf-8"
        )
        self.assertTrue(any("description must be" in e for e in check_claude_code(root)))
        self.assertIsNone(frontmatter("# no frontmatter\n"))


if __name__ == "__main__":
    unittest.main()
