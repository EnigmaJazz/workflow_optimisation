"""Static checks for the PM handoff contract.

The PM's RUNTIME behaviour is NOT repo-testable. The falsifier is a live
`pm-odd` dispatch whose result envelope records the hash comparison — HOST-ONLY.
"""

from pathlib import Path
import unittest


SPEC_PATH = Path(__file__).resolve().parents[1] / "docs/specs/pm-handoff.md"


class PMHandoffSpecTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = SPEC_PATH.read_text(encoding="utf-8")

    def assert_brief_hash_fields(self, spec):
        brief = spec.split("## PM prompt boundary", 1)[0]
        self.assertIn("`tracker_sha256`", brief)
        self.assertIn("`mirror_sha256`", brief)
        self.assertRegex(brief, r"(?i)orchestrator.{0,100}suppl")

    def test_brief_schema_names_orchestrator_supplied_hashes(self):
        self.assert_brief_hash_fields(self.spec)

    def test_pm_readback_hashes_committed_tracker_and_blocks_bad_values(self):
        readback = self.spec.split("## Route validation and ordered execution", 1)[1].split(
            "## Versioned result envelope", 1
        )[0] + self.spec.split("## Closure and metadata work unit", 1)[1]
        self.assertIn("committed tracker file", readback.lower())
        self.assertIn("sha256", readback.lower())
        self.assertIn("supplied `tracker_sha256`", readback)
        self.assertIn("at unit start", readback.lower())
        self.assertIn("planning", readback.lower())
        self.assertIn("comparison is skipped", readback.lower())
        self.assertIn("recomputes and reports", readback.lower())
        self.assertIn("fix-forward", readback.lower())
        self.assertIn("BLOCKED", readback)
        for outcome in ("stale", "missing"):
            self.assertIn(outcome, readback.lower())

    def test_planning_unit_without_dispatch_hash_skips_comparison(self):
        readback = self.spec.split("## Route validation and ordered execution", 1)[1]
        self.assertIn("explicit `none`", readback)
        self.assertIn("comparison is skipped", readback.lower())

    def test_post_unit_rehash_is_reported_not_blocked(self):
        closure = self.spec.split("## Closure and metadata work unit", 1)[1]
        self.assertIn("recomputes and reports", closure.lower())
        self.assertIn("fix-forward", closure.lower())
        self.assertNotIn("complete Magic Context mirror readback", closure)

    def test_result_envelope_records_hash_comparison_method_outcome_and_hashes(self):
        envelope = self.spec.split('"readback": {', 1)[1].split("\n  }", 1)[0]
        for term in ("method", "outcome", "tracker_sha256", "mirror_sha256", "computed"):
            self.assertIn(term, envelope)

    def test_metadata_worker_keeps_mirror_write_ownership(self):
        closure = self.spec.split("## Closure and metadata work unit", 1)[1]
        self.assertIn("metadata worker mirrors the complete canonical tracker body", closure)
        self.assertIn("reads back both stores", closure)

    def test_positive_control_detects_removed_required_brief_field(self):
        mutated = self.spec.replace("`mirror_sha256`", "`mirror_digest`", 1)
        with self.assertRaises(AssertionError):
            self.assert_brief_hash_fields(mutated)


if __name__ == "__main__":
    unittest.main()
