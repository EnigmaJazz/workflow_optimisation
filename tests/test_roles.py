"""Structural checks for roles/ (D26) and the CLAUDE.md manager role (S12-S35)."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROLES = ROOT / "roles"
TIERS = ("tier-1", "tier-2", "tier-2s", "tier-4", "tier-5")
SECTIONS = ("Purpose", "May", "Must not", "Inputs", "Outputs", "Minimality")
# Section 14: every role says minimal never drops these.
PRESERVED = ("tests", "validation", "Risk line")


def read(name):
    return (ROLES / f"{name}.md").read_text()


def section(text, title):
    m = re.search(rf"^## {title}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1) if m else ""


class RoleFiles(unittest.TestCase):
    def test_one_versioned_file_per_tier(self):
        for t in TIERS:
            with self.subTest(tier=t):
                self.assertTrue((ROLES / f"{t}.md").is_file())
                self.assertEqual(read(t).splitlines()[0], "version: 1")

    def test_readme_versions_and_lists_every_file(self):
        text = (ROLES / "README.md").read_text()
        self.assertIn("version", text.lower())
        for t in TIERS:
            self.assertIn(f"{t}.md", text)

    def test_required_sections(self):
        for t in TIERS:
            for s in SECTIONS:
                with self.subTest(tier=t, section=s):
                    self.assertTrue(section(read(t), s).strip())

    def test_minimality_preserves_tests_validation_and_risk_line(self):
        for t in TIERS:
            for word in PRESERVED:
                with self.subTest(tier=t, word=word):
                    self.assertIn(word, section(read(t), "Minimality"))

    def test_minimality_pending_owner_review(self):
        for t in TIERS:
            with self.subTest(tier=t):
                self.assertIn("pending owner review", section(read(t), "Minimality").lower())


class Tier1(unittest.TestCase):
    def test_sequencing_no_integration_detail_no_code(self):
        t = read("tier-1")
        self.assertIn("cross-repository sequencing", section(t, "Purpose"))
        self.assertIn("integration detail", section(t, "Must not"))
        self.assertIn("Write code", section(t, "Must not"))

    def test_registry_pending_open_9(self):
        self.assertIn("pending OPEN-9", read("tier-1"))


class Tier2(unittest.TestCase):
    def test_owner_strings(self):
        t = read("tier-2")
        self.assertIn("writes no code", t)
        self.assertIn("makes no change without an explicit owner override", t)

    def test_contract(self):
        t = read("tier-2")
        self.assertIn("one Claude Code session per repository", t)
        self.assertIn("Haiku", section(t, "May"))
        self.assertIn("code-level", section(t, "Outputs"))
        self.assertIn("above the OpenCode PM layer", t)
        self.assertIn("owns all Engram writes", t)


class Tier2s(unittest.TestCase):
    def test_pending_open_3_and_no_invented_contract(self):
        t = read("tier-2s")
        self.assertIn("pending OPEN-3", t)
        self.assertIn("Global Tooling Changes", t)


class Tier4(unittest.TestCase):
    def test_spec_author_not_planner_or_implementer(self):
        t = read("tier-4")
        self.assertIn("specification", section(t, "Purpose"))
        must_not = section(t, "Must not")
        self.assertIn("per-stage implementation plan", must_not)
        self.assertIn("implement", must_not)
        self.assertIn("luna", section(t, "May"))

    def test_review_wording_treats_bloat_as_defects(self):
        m = section(read("tier-4"), "Minimality")
        for word in ("unnecessary", "duplicated helper", "speculative infrastructure"):
            with self.subTest(word=word):
                self.assertIn(word, m)
        self.assertIn("defect", m)


class ClaudeMd(unittest.TestCase):
    def setUp(self):
        self.text = (ROOT / "CLAUDE.md").read_text()

    def test_advisory_role_replaced(self):
        self.assertNotIn("Advisory by default", self.text)
        self.assertIn("roles/", self.text)

    def test_manager_role(self):
        for s in ("writes no code", "makes no change without an explicit owner override",
                  "Haiku", "Engram"):
            with self.subTest(s=s):
                self.assertIn(s, self.text)

    def test_no_session_authorization_recorded(self):
        self.assertNotIn("authoris", self.text.lower())


if __name__ == "__main__":
    unittest.main()
