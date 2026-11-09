"""Tests that the global pm-handoff skill is a byte-exact spec mirror."""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "docs" / "specs" / "pm-handoff.md"
SKILL = ROOT / "global-config" / "skills" / "pm-handoff" / "SKILL.md"
CONFIG = ROOT / "global-config" / "opencode.json"
ASSEMBLER = ROOT / "global-config" / "prompts" / "gentle-orchestrator" / "assemble-orchestrator-prompt.py"
FRONTMATTER = re.compile(r"\A---\nname: pm-handoff\ndescription: [^\n]+\n---\n\n\Z")


class PMHandoffSkillTests(unittest.TestCase):
    def test_skill_frontmatter_and_body_match_the_normative_spec(self):
        self.assertTrue(SKILL.is_file(), "global pm-handoff skill must exist")
        spec_text = SPEC.read_text(encoding="utf-8")
        skill_text = SKILL.read_text(encoding="utf-8")
        frontmatter, separator, body = skill_text.partition("# Project-manager unit handoff contract")
        self.assertEqual(separator, "# Project-manager unit handoff contract")
        self.assertIsNotNone(FRONTMATTER.fullmatch(frontmatter))
        expected = frontmatter + separator + body
        self.assertEqual(skill_text, expected)
        self.assertEqual(body, spec_text.removeprefix("# Project-manager unit handoff contract"))
        self.assertEqual(skill_text, frontmatter + spec_text)

    def test_changed_mirror_character_is_detected(self):
        spec_text = SPEC.read_text(encoding="utf-8")
        skill_text = SKILL.read_text(encoding="utf-8")
        frontmatter, _, _ = skill_text.partition("# Project-manager unit handoff contract")
        expected = frontmatter + spec_text
        changed = expected.replace("contract", "Contract", 1)
        self.assertNotEqual(changed, expected, "positive control: a changed mirror character must fail equality")

    def test_pm_prompts_and_assembled_orchestrator_name_skill_and_spec(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        for agent in ("pm-odd", "pm-systematic"):
            prompt = config["agent"][agent]["prompt"]
            self.assertIn("pm-handoff", prompt)
            self.assertIn("docs/specs/pm-handoff.md", prompt)
        assembled = subprocess.run(
            [sys.executable, str(ASSEMBLER)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(assembled.returncode, 0, assembled.stderr)
        self.assertIn("pm-handoff", assembled.stdout)
        self.assertIn("docs/specs/pm-handoff.md", assembled.stdout)


if __name__ == "__main__":
    unittest.main()
