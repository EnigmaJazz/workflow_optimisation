"""Static checks for the PM handoff contract.

The PM's RUNTIME behaviour is HOST-ONLY. The falsifier is a live `pm-odd`
dispatch whose result envelope records the anchor comparison.
"""

from pathlib import Path
import unittest


SPEC_PATH = Path(__file__).resolve().parents[1] / "docs/specs/pm-handoff.md"


class PMHandoffSpecTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = SPEC_PATH.read_text(encoding="utf-8")

    def assert_anchor_contract(self, spec):
        brief = spec.split("## PM prompt boundary", 1)[0]
        self.assertIn("exact byte (or character) count", brief)
        self.assertIn("exact literal text of its last line", brief)
        self.assertIn("`HEAD` commit SHA", brief)
        self.assertIn("stale tracker", brief)
        self.assertIn("truncated tracker", brief)
        self.assertIn("wrong commit", brief)
        self.assertIn("whitespace-only", brief)
        self.assertIn("not a cryptographic witness", brief)
        self.assertIn("SUSPENDED", brief)
        self.assertIn("deterministic host tool lands", brief)

    def test_brief_specifies_deterministic_anchor_and_suspended_hash_duty(self):
        self.assert_anchor_contract(self.spec)

    def test_readback_requires_anchor_comparison_and_preserves_planning_skip(self):
        readback = self.spec.split("## Route validation and ordered execution", 1)[1].split(
            "## Versioned result envelope", 1
        )[0] + self.spec.split("## Closure and metadata work unit", 1)[1]
        self.assertIn("anchor", readback.lower())
        self.assertIn("at unit start", readback.lower())
        self.assertIn("planning", readback.lower())
        self.assertIn("comparison is skipped", readback.lower())
        self.assertIn("BLOCKED", readback)
        self.assertIn("SUSPENDED", readback)
        self.assertIn("deterministic host tool lands", readback)
        self.assertNotIn("supplied `tracker_sha256`", readback)
        self.assertNotIn("final tracker SHA-256", readback)

    def test_result_envelope_records_anchor_observations_outcome_and_block_reason(self):
        envelope = self.spec.split('"readback": {', 1)[1].split("\n  }", 1)[0]
        for term in ("anchor_comparison", "byte_or_character_count", "last_line_text", "head_commit_sha", "outcome", "BLOCKED"):
            self.assertIn(term, envelope)

    def test_old_hash_obligation_wording_is_gone(self):
        brief = self.spec.split("## PM prompt boundary", 1)[0]
        self.assertNotIn("`tracker_sha256` (unit-start", brief)
        self.assertNotIn("`mirror_sha256` (SHA-256", brief)
        self.assertNotIn("supplied `tracker_sha256`", self.spec)
        self.assertNotIn("computed_tracker_sha256", self.spec)
        self.assertNotIn("supplied_mirror_sha256", self.spec)

    def assert_metadata_ownership_contract(self, spec):
        closure = spec.split("## Closure and metadata work unit", 1)[1]
        self.assertIn("metadata worker updates and commits the repository files only", closure.lower())
        self.assertIn("deterministic host tool", closure.lower())
        self.assertIn("owns the Magic Context mirror write and verification", closure)
        self.assertIn("invoked by the orchestrator", closure)
        self.assertNotIn("metadata worker mirrors the complete canonical tracker body", closure)
        self.assertNotIn("reads back both stores", closure)
        self.assertNotIn("complete Magic Context mirror readback", closure)
        self.assertIn("PM still never reads or touches the mirror body", closure)
        self.assertIn(
            "`metadata_work_unit` covers only the metadata worker's repository-file updates and commit",
            spec,
        )

    def test_deterministic_host_tool_owns_mirror_write_and_verification(self):
        self.assert_metadata_ownership_contract(self.spec)

    def test_ownership_positive_control_rejects_old_metadata_worker_duty(self):
        mutated = self.spec.replace(
            "metadata worker updates and commits the repository files only",
            "metadata worker mirrors the complete canonical tracker body",
            1,
        )
        with self.assertRaises(AssertionError):
            self.assert_metadata_ownership_contract(mutated)

    def test_anchor_positive_control_rejects_mutated_anchor_definition(self):
        mutated = self.spec.replace(
            "exact byte (or character) count", "approximate byte (or character) count", 1
        )
        with self.assertRaises(AssertionError):
            self.assert_anchor_contract(mutated)

    def test_positive_control_detects_removed_required_anchor_field(self):
        mutated = self.spec.replace("last line", "final paragraph", 1)
        with self.assertRaises(AssertionError):
            self.assert_anchor_contract(mutated)


if __name__ == "__main__":
    unittest.main()
