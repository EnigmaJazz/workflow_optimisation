"""Systematic 3.24.0 removed the workflow guard and its four systematic_workflow_* tools.

The verifier must not require them, the canonical config must not grant them, and the
ignored workflow_guard key must not be shipped (it logs a deprecation warning per load).
"""
import json
import re
import unittest
from pathlib import Path
try:
    from tests.verifier_source import verifier_text
except ImportError:  # run as a script from tests/
    from verifier_source import verifier_text

REPO = Path(__file__).resolve().parent.parent
REMOVED_TOOL = re.compile(r"systematic_workflow_[a-z_]+")


def strip_jsonc_comments(text):
    return re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)


class SystematicWorkflowToolsRemoved(unittest.TestCase):
    def test_verifier_does_not_require_removed_tools(self):
        text = verifier_text()
        self.assertEqual(REMOVED_TOOL.findall(text), [])

    def test_canonical_config_does_not_grant_removed_tools(self):
        text = (REPO / "global-config/opencode.json").read_text(encoding="utf-8")
        self.assertEqual(REMOVED_TOOL.findall(text), [])

    def test_canonical_config_still_grants_systematic_skill(self):
        # Positive control: the probe can see a systematic_* permission that still exists.
        config = json.loads((REPO / "global-config/opencode.json").read_text(encoding="utf-8"))
        self.assertEqual(config["permission"].get("systematic_skill"), "allow")

    def test_systematic_config_drops_workflow_guard(self):
        text = (REPO / "global-config/systematic.jsonc").read_text(encoding="utf-8")
        config = json.loads(strip_jsonc_comments(text))
        self.assertNotIn("workflow_guard", config)
        self.assertIn("bootstrap", config)


if __name__ == "__main__":
    unittest.main()
