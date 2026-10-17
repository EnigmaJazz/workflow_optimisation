"""Contract checks for the tiny-fix escalation tripwire.

The runtime escalation cannot be exercised by repository tests: the orchestrator
cannot observe a candidate diff mid-flight. The falsifier is a host workflow that
allows an over-threshold or denylisted candidate to remain Tiny fix at the
pre-apply assessment boundary.
"""

import ast
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUARD = ROOT / "global-config" / "plugins" / "systematic-routing-guard.ts"
ASSEMBLER = ROOT / "global-config" / "prompts" / "gentle-orchestrator" / "assemble-orchestrator-prompt.py"
CONFIG = ROOT / "global-config" / "opencode.json"
PROMPT_TEST = ROOT / "tests" / "test_orchestrator_prompt_source.py"


def read_tripwire_constants():
    source = GUARD.read_text(encoding="utf-8")
    lines_match = re.search(r"const TINY_FIX_MAX_AUTHORED_CHANGED_LINES = (\d+)", source)
    files_match = re.search(r"const TINY_FIX_MAX_TOUCHED_FILES = (\d+)", source)
    denylist_match = re.search(
        r"const TINY_FIX_DENYLIST_PATH_PATTERNS: readonly string\[\] = (\[[^\]]*\])",
        source,
        re.DOTALL,
    )
    if not (lines_match and files_match and denylist_match):
        raise AssertionError("named tiny-fix tripwire constants are missing")
    return source, int(lines_match.group(1)), int(files_match.group(1)), ast.literal_eval(denylist_match.group(1))


def escalation_required(changed_lines, touched_paths, added_or_deleted=False):
    _, max_lines, max_files, patterns = read_tripwire_constants()
    denied = any(
        fnmatch.fnmatchcase(path, pattern)
        for path in touched_paths
        for pattern in patterns
    )
    return changed_lines > max_lines or len(touched_paths) > max_files or added_or_deleted or denied


class TinyFixTripwireContract(unittest.TestCase):
    def test_named_constants_and_predicate_are_present(self):
        source, max_lines, max_files, patterns = read_tripwire_constants()
        self.assertEqual(max_lines, 20)
        self.assertEqual(max_files, 2)
        self.assertTrue(patterns)
        self.assertIn("tinyFixEscalationRequired", source)
        self.assertIn("candidate.authoredChangedLines > TINY_FIX_MAX_AUTHORED_CHANGED_LINES", source)
        self.assertIn("candidate.touchedPaths.length > TINY_FIX_MAX_TOUCHED_FILES", source)
        self.assertIn("candidate.addedOrDeleted", source)

    def test_denylist_covers_protected_paths_and_permissions_surface(self):
        _, _, _, patterns = read_tripwire_constants()
        for path in (
            "verify-workflow.sh",
            "global-config/opencode.json",
            "global-config/systematic.jsonc",
            "global-config/plugins/systematic-routing-guard.ts",
            "global-config/permissions/roles.json",
        ):
            with self.subTest(path=path):
                self.assertTrue(any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns), path)

    def test_prompt_assembler_test_constant_and_embedded_prompt_match(self):
        assembled = subprocess.run([sys.executable, str(ASSEMBLER)], check=True, capture_output=True).stdout
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        embedded = config["agent"]["gentle-orchestrator"]["prompt"].encode("utf-8")
        source = PROMPT_TEST.read_text(encoding="utf-8")
        expected = re.search(r'CURRENT_PROMPT_SHA256 = "([0-9a-f]{64})"', source)
        self.assertIsNotNone(expected, "prompt source test hash constant is missing")
        self.assertEqual(hashlib.sha256(assembled).hexdigest(), expected.group(1))
        self.assertEqual(embedded, assembled, "embedded prompt differs from assembler bytes")

    def test_both_pm_prompts_expose_the_bounded_mid_unit_option(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        for name in ("pm-odd", "pm-systematic"):
            prompt = config["agent"][name]["prompt"]
            with self.subTest(agent=name):
                self.assertIn("Tiny-fix option: mid-unit", prompt)
                self.assertIn("active unit tracker `## Log`", prompt)
                self.assertIn("return envelope", prompt)
                self.assertLess(len(prompt), 6000)


class PositiveControl(unittest.TestCase):
    def test_over_threshold_and_denylisted_changes_fail_the_escalation_predicate(self):
        self.assertTrue(escalation_required(21, ["src/fix.ts"]))
        self.assertTrue(escalation_required(1, ["global-config/opencode.json"]))


if __name__ == "__main__":
    unittest.main()
