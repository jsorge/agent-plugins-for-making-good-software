import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import validate


class AgentSkillsTests(unittest.TestCase):
    def findings_for(self, skills: str) -> list[tuple[str, str]]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin = root / "plugins" / "fixture"
            (plugin / "skills" / "one").mkdir(parents=True)
            (root / "plugins" / "other" / "skills" / "foreign").mkdir(parents=True)
            agents = plugin / "agents"
            agents.mkdir()
            (agents / "review.md").write_text(
                f'---\nname: review\ndescription: "Review code"\n{skills}\ncolor: blue\n---\nBody\n',
                encoding="utf-8",
            )
            with patch.object(validate, "REPO_ROOT", root):
                return validate.check_agent_frontmatter()

    def test_block_array_resolves_same_plugin_skill(self):
        for indent in ("", "  "):
            with self.subTest(indent=indent):
                self.assertEqual(self.findings_for(f"skills:\n{indent}- one"), [])

    def test_every_array_entry_must_resolve_in_same_plugin(self):
        for indent in ("", "  "):
            for missing in ("absent", "foreign"):
                with self.subTest(indent=indent, missing=missing):
                    findings = self.findings_for(f"skills:\n{indent}- one\n{indent}- {missing}")
                    self.assertEqual(len(findings), 1)
                    self.assertIn(f"skills entry {missing!r}", findings[0][1])

    def test_quoted_array_entries_and_comments(self):
        names = validate._agent_skill_names([
            "skills: # preloads",
            '  - "one"',
            "  # next skill",
            "",
            "  - 'two'",
            "  - three # comment",
            "color: blue",
            "  - unrelated",
        ])
        self.assertEqual(names, ["one", "two", "three"])

    def test_omitted_skills_remains_valid(self):
        self.assertEqual(self.findings_for(""), [])
        self.assertEqual(validate._agent_skill_names(["name: review"]), [])

    def test_legacy_scalar_references_are_still_checked(self):
        self.assertEqual(self.findings_for("skills: one"), [])
        findings = self.findings_for("skills: one, absent")
        self.assertEqual(len(findings), 1)
        self.assertIn("skills entry 'absent'", findings[0][1])


if __name__ == "__main__":
    unittest.main()
