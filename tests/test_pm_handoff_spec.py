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
        self.assertIn("exact line count", brief)
        self.assertIn("exact literal text of its last line", brief)
        self.assertIn("feature-branch `HEAD` commit SHA", brief)
        self.assertIn("stale or truncated working-tree tracker", brief)
        self.assertIn("does not establish that the tracker contents are committed", brief)
        self.assertIn("does not catch whitespace-only", brief)
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
        for term in ("anchor_comparison", "line_count", "last_line_text", "head_commit_sha", "working-tree", "outcome", "BLOCKED"):
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

    def assert_review_order_contract(self, spec):
        execution = spec.split("## Route validation and ordered execution", 1)[1].split(
            "## Versioned result envelope", 1
        )[0]
        self.assertIn("post-code advisory review from the PM before the work-unit commit", execution)
        self.assertIn("all advisory blockers must be resolved before the work-unit commit", execution)
        commit = execution.index("staged reviewability receipt and authorized PM-owned work-unit commit")
        self.assertIn("native review risk assessment against the committed candidate", execution)
        assessment = execution.index("native review risk assessment against the committed candidate")
        self.assertLess(commit, assessment)
        self.assertIn("The pre-apply assessment requirement is removed", execution)

    def test_pm_advice_blockers_precede_commit_and_native_assessment_follows_it(self):
        self.assert_review_order_contract(self.spec)

    def test_review_order_positive_control_rejects_pre_apply_assessment(self):
        mutated = self.spec.replace(
            "native review risk assessment against the committed candidate",
            "native review risk assessment before apply or install",
            1,
        )
        with self.assertRaises(AssertionError):
            self.assert_review_order_contract(mutated)

    def test_anchor_positive_control_rejects_mutated_anchor_definition(self):
        mutated = self.spec.replace(
            "exact line count", "approximate line count", 1
        )
        with self.assertRaises(AssertionError):
            self.assert_anchor_contract(mutated)

    def test_positive_control_detects_removed_required_anchor_field(self):
        mutated = self.spec.replace("last line", "final paragraph", 1)
        with self.assertRaises(AssertionError):
            self.assert_anchor_contract(mutated)

    def test_standalone_tiny_fix_allows_none_tracker_but_requires_branch_sha(self):
        self.assert_standalone_tiny_fix_anchor_contract(self.spec)

    def assert_standalone_tiny_fix_anchor_contract(self, spec):
        brief = spec.split("## PM prompt boundary", 1)[0]
        self.assertIn("standalone tiny fix", brief)
        self.assertIn("only the tracker-derived line-count and last-line components are `none`", brief)
        self.assertIn("branch `HEAD` commit SHA remains required in every case", brief)
        comparison = spec.split("At unit start, the PM reads the tracker path", 1)[1].split(
            "The PM does not fetch", 1
        )[0]
        self.assertIn("tracker comparison is skipped rather than blocked", comparison)
        self.assertIn("branch `HEAD` SHA remains required and its comparison still runs", comparison)

    def test_standalone_tiny_fix_positive_control_rejects_removed_none_authorization(self):
        marker = "standalone tiny fix"
        self.assertIn(marker, self.spec)
        mutated = self.spec.replace(marker, "unsupported tiny fix")
        with self.assertRaises(AssertionError):
            self.assert_standalone_tiny_fix_anchor_contract(mutated)


if __name__ == "__main__":
    unittest.main()
