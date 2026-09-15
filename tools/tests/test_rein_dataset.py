from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
import re
import posixpath
from urllib.parse import unquote, urlsplit
from pathlib import Path


ROOT = Path(__file__).parents[2] / "records/REIN-CH05-16/evidence/specs"


def files_hash(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}


def _visible_markdown(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return text


def _normalized(text: str) -> str:
    return re.sub(r"\bnpm\s+test\b", "npm run test", text)


def _visible_links(text: str) -> list[str]:
    visible = _visible_markdown(text)
    return [target for label, target in re.findall(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+[^)]*)?\)", visible) if label.strip()]


def _visible_body(text: str) -> str:
    text = re.sub(r"`[^`]*`", "", text)
    text = re.sub(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    return re.sub(r"[#*_>`~-]", "", text).strip()


def assertions_hold(case: dict, workspace: Path, expected: dict, *, require_unchanged: bool = False, before: dict[str, str] | None = None) -> bool:
    for assertion in expected["assertions"]:
        if "file" not in assertion:
            continue
        path = workspace / assertion["file"]
        if not path.is_file():
            return False
        text = _visible_markdown(path.read_text(encoding="utf-8"))
        normalized = _normalized(text)
        if assertion.get("require_retained_body") and len(re.findall(r"[A-Za-z\u4e00-\u9fff]", _visible_body(text))) < 4:
            return False
        if "contains" in assertion and _normalized(assertion["contains"]) not in normalized:
            return False
        if "contains_any" in assertion and not any(_normalized(value) in normalized for value in assertion["contains_any"]):
            return False
        if "does_not_contain" in assertion and _normalized(assertion["does_not_contain"]) in normalized:
            return False
        if "does_not_contain_token" in assertion and re.search(r"(?<![A-Za-z0-9_])" + re.escape(assertion["does_not_contain_token"]) + r"(?![A-Za-z0-9_])", text):
            return False
        if assertion.get("must_exist"):
            target = (path.parent / assertion["link_target"]).resolve()
            if not target.is_file() or not target.is_relative_to(workspace.resolve()):
                return False
        if "visible_link_target" in assertion:
            expected_target = posixpath.normpath(unquote(assertion["visible_link_target"]))
            actual_targets = [posixpath.normpath(unquote(target)) for target in _visible_links(text)]
            if expected_target not in actual_targets:
                return False
        for target_name in _visible_links(text):
            parsed = urlsplit(target_name)
            if parsed.scheme or parsed.netloc or target_name.startswith("#"):
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.is_file() or not target.is_relative_to(workspace.resolve()):
                return False
    if before is not None:
        current = files_hash(workspace)
        if case.get("category") == "no_change" and before != current:
            return False
        if case.get("category") != "no_change":
            target = case.get("input_fault", {}).get("file")
            if target and {path: digest for path, digest in current.items() if path != target} != {path: digest for path, digest in before.items() if path != target}:
                return False
    elif require_unchanged and before != files_hash(workspace):
        return False
    return True


class ReinDatasetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.index = json.loads((ROOT / "chapter-16-cases.json").read_text(encoding="utf-8"))

    def test_original_faults_are_nine_failures_and_three_no_change_passes(self) -> None:
        outcomes = []
        for case in self.index["cases"]:
            workspace = ROOT / "chapter-16" / case["id"] / "workspace"
            expected = json.loads((ROOT / "chapter-16" / case["id"] / "expected.json").read_text())
            before = files_hash(workspace)
            outcomes.append(assertions_hold(case, workspace, expected, require_unchanged=case["category"] == "no_change", before=before))
        self.assertEqual(sum(outcomes), 3)
        self.assertEqual(sum(not value for value in outcomes), 9)

    def test_independent_correct_candidates_satisfy_all_oracles(self) -> None:
        replacements = {
            "expired-command-01": ("npm run old-check", "npm run " + next(iter(json.loads((ROOT / "chapter-16/expired-command-01/workspace/package.json").read_text())["scripts"]))),
            "expired-command-02": ("npm run old-build", "npm run " + next(iter(json.loads((ROOT / "chapter-16/expired-command-02/workspace/package.json").read_text())["scripts"]))),
            "expired-command-03": ("npm run old-test", "npm run " + next(iter(json.loads((ROOT / "chapter-16/expired-command-03/workspace/package.json").read_text())["scripts"]))),
            "parameter-change-01": ("--timeout 5", next(flag for flag in re.findall(r'add_argument\("(--[\w-]+)"', (ROOT / "chapter-16/parameter-change-01/workspace/src/cli.py").read_text()) if "timeout" in flag) + " 5"),
            "parameter-change-02": ("--root-dir", re.search(r'add_argument\("(--[\w-]+)"', (ROOT / "chapter-16/parameter-change-02/workspace/src/cli.py").read_text()).group(1)),
            "parameter-change-03": ("API_URL", json.loads((ROOT / "chapter-16/parameter-change-03/workspace/config.schema.json").read_text())["required"][0]),
            "broken-relative-link-01": ("docs/missing.md", "docs/guide.md"),
            "broken-relative-link-02": ("../setup-old.md", "../setup.md"),
            "broken-relative-link-03": ("../api/v0.md", "../api.md"),
        }
        for case in self.index["cases"]:
            source = ROOT / "chapter-16" / case["id"] / "workspace"
            expected = json.loads((ROOT / "chapter-16" / case["id"] / "expected.json").read_text())
            with tempfile.TemporaryDirectory() as temp:
                workspace = Path(temp) / "workspace"
                shutil.copytree(source, workspace)
                if case["id"] in replacements:
                    old, new = replacements[case["id"]]
                    target = workspace / case["input_fault"]["file"]
                    target.write_text(target.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
                before = files_hash(source)
                self.assertTrue(assertions_hold(case, workspace, expected, require_unchanged=case["category"] == "no_change", before=before), case["id"])

    def test_comments_cannot_hide_bad_visible_content(self) -> None:
        expected = {"assertions": [{"file": "README.md", "contains": "Tests", "visible_link_target": "docs/guide.md"}]}
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "docs").mkdir()
            (workspace / "docs/guide.md").write_text("guide", encoding="utf-8")
            (workspace / "README.md").write_text("Only `npm run test` and `--workspace`.", encoding="utf-8")
            self.assertFalse(assertions_hold({}, workspace, expected))
            (workspace / "README.md").write_text("Tests: `npm test`. See [the guide](./docs/guide.md).", encoding="utf-8")
            self.assertTrue(assertions_hold({}, workspace, expected))
            (workspace / "README.md").write_text("Tests: `npm run test`. <!-- [the guide](./docs/guide.md) -->", encoding="utf-8")
            self.assertFalse(assertions_hold({}, workspace, expected))

    def test_link_oracle_accepts_any_nonempty_label_and_normalizes_dot_and_encoding(self) -> None:
        case = next(item for item in self.index["cases"] if item["id"] == "broken-relative-link-01")
        expected = json.loads((ROOT / "chapter-16/broken-relative-link-01/expected.json").read_text())
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "docs").mkdir()
            (workspace / "docs/guide.md").write_text("guide", encoding="utf-8")
            (workspace / "README.md").write_text("See [Guide](docs/guide.md).", encoding="utf-8")
            self.assertTrue(assertions_hold(case, workspace, expected))
            (workspace / "README.md").write_text("See [the guide](./docs/guide.md).", encoding="utf-8")
            self.assertTrue(assertions_hold(case, workspace, expected))

    def test_original_api_name_in_comment_is_still_rejected(self) -> None:
        case = next(item for item in self.index["cases"] if item["id"] == "parameter-change-03")
        expected = json.loads((ROOT / "chapter-16/parameter-change-03/expected.json").read_text())
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "docs").mkdir()
            (workspace / "docs/config.md").write_text("The endpoint uses `API_URL`. <!-- REIN_BASE_URL -->", encoding="utf-8")
            self.assertFalse(assertions_hold(case, workspace, expected))

    def test_parameter_change_fixtures_bind_real_argparse_names(self) -> None:
        import runpy

        cli01 = runpy.run_path(str(ROOT / "chapter-16/parameter-change-01/workspace/src/cli.py"))["parser"]
        with self.assertRaises(SystemExit):
            cli01.parse_args(["--timeout", "5"])
        self.assertEqual(cli01.parse_args(["--timeout-seconds", "5"]).timeout_seconds, 5)

        cli02 = runpy.run_path(str(ROOT / "chapter-16/parameter-change-02/workspace/src/cli.py"))["parser"]
        self.assertEqual(cli02.parse_args(["--workspace", "src"]).workspace, "src")
        with self.assertRaises(SystemExit):
            cli02.parse_args(["--root-dir", "src"])


if __name__ == "__main__":
    unittest.main()
