"""Static checks for the PM handoff contract.

The PM's RUNTIME behaviour is HOST-ONLY. The falsifier is a live `pm-odd`
dispatch whose result envelope records the anchor comparison.
"""

from pathlib import Path
import json
import re
import unittest


SPEC_PATH = Path(__file__).resolve().parents[1] / "docs/specs/pm-handoff.md"
WORKFLOW_PATH = Path(__file__).resolve().parents[1] / "WORKFLOW.md"
ODD_SKILL_PATH = (
    Path(__file__).resolve().parents[1]
    / "global-config/skills/workflow-odd-secure/SKILL.md"
)
SYSTEMATIC_SKILL_PATH = (
    Path(__file__).resolve().parents[1]
    / "global-config/skills/workflow-systematic/SKILL.md"
)
BUDGET_HEADING = "## Verification and advice budget by task type"
SIX_ROUTE_CLASSES = (
    "Tiny fix",
    "Small feature",
    "Substantial feature",
    "Bug investigation",
    "Documentation",
    "Global tooling change",
)
DOCS_ALLOWLIST_TERMS = (
    "odd/tasks/**",
    "odd/advice/**",
    "ROUTER-LOG.md",
    "CLAIM-RETRACTIONS.md",
    "docs/TODO.md",
    "docs/TODO-HISTORY.md",
    "non-Constraints/non-decisions",
    "uncertainty fails closed",
    "Any test/verifier reader disqualifies the unit",
    "WORKFLOW.md",
    "AGENTS.md",
    "docs/specs/**",
    "global-config/**",
    "ANCHOR_MANIFEST",
    "command-changing docs",
    "No automatic source-comment exemption",
)
BUDGET_TERMS = (
    "zero pre-advice",
    "zero post-advice",
    "zero `gentle-ai-verify`",
    "one pre-advice phase",
    "one post-code check",
    "`ce:review` substitutes",
    "explicit exception",
    "security boundary",
    "uncertainty",
    "live fallback/independence",
    "explicitly reduced small-model profile",
    "one independent verifier",
    "Generated inherits source",
    "Counts are check phases, not numbers of baseline reviewers",
    "opencode-go/deepseek-v4.1-flash",
    "NOT treated as a small/reduced profile",
    "owner decision, 2026-10-21",
)
ONE_CORRECTION_TERMS = (
    "one initial writer plus ONE fresh correction writer",
    "all pre-commit post-code gates",
    "`ce:review` and external advice",
    "SAME candidate",
    "finding IDs",
    "one consolidated fix brief",
    "install first, then refine on the installed base",
    "targeted recheck",
    "`NEEDS_INPUT`",
    "`BLOCKED`",
    "`correction_rounds_used`",
    "`0|1`",
    "record any override separately",
    "metadata or a new task ID never silently resets the counter",
    "targeted native validator",
    "no PM advisor or verifier cycle",
    "escalated after commit owes the applicable post-code check on the committed candidate",
    "any correction is a new commit, never rewriting history",
)
LOCAL_WRITER_TERMS = (
    "`gentle-ai-worker-local`",
    "exactly ONE changed file per writer Task",
    "cloud writers may batch a coherent multi-file unit",
)
STATIC_DIAGNOSTIC_SENTENCE = (
    "The FIRST post-code verification pass runs on the SAME INITIAL candidate and includes the "
    "required tests, the post-code advisor or `ce:review`, the verifier where the budget owes one, "
    "and `aft_inspect` or applicable static diagnostics for every changed path. All findings join "
    "the ONE correction batch. Running diagnostics for the first time only after correction is a "
    "process defect."
)


def matrix_section(text):
    """Return the budget section, or raise ValueError when absent."""
    match = re.search(rf"^{re.escape(BUDGET_HEADING)}$", text, re.MULTILINE)
    if not match:
        raise ValueError(BUDGET_HEADING)
    remainder = text[match.end():]
    end = remainder.find("\n## ")
    return remainder if end < 0 else remainder[:end]


def missing_terms(text, terms):
    return [term for term in terms if term not in text]


def verification_budget_errors(text):
    errors = []
    try:
        section = matrix_section(text)
    except ValueError:
        return ["missing section: " + BUDGET_HEADING]
    for term in SIX_ROUTE_CLASSES:
        if term not in section:
            errors.append("missing route class: " + term)
    for term in BUDGET_TERMS:
        if term not in section:
            errors.append("missing budget term: " + term)
    for phrase in ("Repeat this loop as needed", "Repeat as needed"):
        if phrase in text:
            errors.append("open-ended refinement wording remains: " + phrase)
    if "only for a code-changing unit" in text:
        errors.append("code-only post-code gate remains")
    return errors


def docs_allowlist_errors(text):
    try:
        section = matrix_section(text)
    except ValueError:
        return ["missing section: " + BUDGET_HEADING]
    return ["missing allowlist term: " + term for term in missing_terms(section, DOCS_ALLOWLIST_TERMS)]


def one_correction_errors(text):
    try:
        section = matrix_section(text)
    except ValueError:
        return ["missing section: " + BUDGET_HEADING]
    return ["missing correction-cap term: " + term for term in missing_terms(section, ONE_CORRECTION_TERMS)]


def local_writer_errors(text):
    try:
        section = matrix_section(text)
    except ValueError:
        return ["missing section: " + BUDGET_HEADING]
    return ["missing local-writer term: " + term for term in missing_terms(section, LOCAL_WRITER_TERMS)]


def static_diagnostic_errors(text):
    if STATIC_DIAGNOSTIC_SENTENCE not in text:
        return ["missing first-pass static-diagnostic sentence"]
    return []


def envelope_section(spec):
    match = re.search(r"^## Versioned result envelope$", spec, re.MULTILINE)
    if not match:
        return ""
    remainder = spec[match.end():]
    end = remainder.find("\n## ")
    return remainder if end < 0 else remainder[:end]


def envelope_errors(spec):
    envelope = envelope_section(spec)
    terms = (
        '"correction_rounds_used"',
        '`0|1`',
        '"docs_exemption"',
        '"changed_paths"',
        '"rationale"',
        '"stats"',
        '"diff_check"',
        '"branch_head"',
        '"asserted_references"',
        '"pm_check"',
        '"orchestrator_readback"',
        '`advice_record` status `not-applicable`',
        "`git diff --check`",
        "any test reader makes the unit normative",
    )
    return ["missing envelope/docs evidence term: " + term for term in missing_terms(envelope, terms)]


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

    def planner_handoff_gaps(self, spec):
        marker = "## Planner handoff (installed and live)"
        if marker not in spec:
            return [marker]
        section = spec.split(marker, 1)[1].split("\n## ", 1)[0]
        required = ("installed and deployed as of 2026-10-25",
                    "selects only the pre-code advisors the task class and impact require",
                    "RAW output", "never accepts a PM or orchestrator summary",
                    "Gate 1", "Gate 2", "BEFORE the PM completes or ticks the unit",
                    "TECHNICAL only", "no writer and no review lens", "Deferred Q90-D1",
                    "only AFTER the PM layer becomes active")
        gaps = [term for term in required if term not in section]
        for phrase in ("not installed, deployed, or live", "Planned Planner handoff", "source-only",
                       "every applicable `advisor-*-pre`", "EVERY applicable `advisor`"):
            if phrase in section:
                gaps.append("removed phrase remains: " + phrase)
        if "PM closes the unit before Gate 2" in section:
            gaps.append("PM closes before Gate 2")
        return gaps

    def test_planner_handoff_is_live_and_gate_owned(self):
        self.assertEqual(self.planner_handoff_gaps(self.spec), [])
        mutated = self.spec.replace("Gate 2 occurs BEFORE the PM completes or ticks the unit.",
                                    "Gate 2 occurs after the PM completes the unit.", 1)
        self.assertTrue(self.planner_handoff_gaps(mutated))

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
        self.assertIn("branch `HEAD` commit SHA is required for every non-planning unit", brief)
        comparison = spec.split("At unit start, the PM reads the tracker path", 1)[1].split(
            "The PM does not fetch", 1
        )[0]
        self.assertIn("tracker comparison is skipped rather than blocked", comparison)
        self.assertIn(
            "branch `HEAD` commit SHA is required for every non-planning unit and its comparison still runs",
            comparison,
        )
        self.assertIn("including the branch `HEAD` commit SHA, are explicitly `none`", comparison)
        self.assertIn(
            "For every non-planning unit, including a standalone tiny fix, a missing or mismatched branch `HEAD` commit SHA blocks the unit",
            comparison,
        )

    def test_standalone_tiny_fix_positive_control_rejects_removed_standalone_authorization(self):
        marker = "standalone tiny fix"
        self.assertIn(marker, self.spec)
        mutated = self.spec.replace(marker, "unsupported tiny fix")
        with self.assertRaises(AssertionError):
            self.assert_standalone_tiny_fix_anchor_contract(mutated)

    def test_positive_control_detects_removed_nonplanning_branch_sha_authorization(self):
        marker = (
            "branch `HEAD` commit SHA is required for every non-planning unit "
            "and its comparison still runs"
        )
        self.assertEqual(self.spec.count(marker), 1)
        brief = self.spec.split("## PM prompt boundary", 1)[0]
        self.assertNotIn(marker, brief)
        self.assertIn(
            "branch `HEAD` commit SHA is required for every non-planning unit", brief
        )
        mutated = self.spec.replace(
            marker,
            "branch `HEAD` commit SHA is optional for non-planning units "
            "and its comparison is skipped",
        )
        with self.assertRaisesRegex(AssertionError, re.escape(marker)):
            self.assert_standalone_tiny_fix_anchor_contract(mutated)


class VerificationBudgetContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = SPEC_PATH.read_text(encoding="utf-8")
        cls.workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        cls.odd_skill = ODD_SKILL_PATH.read_text(encoding="utf-8")
        cls.systematic_skill = SYSTEMATIC_SKILL_PATH.read_text(encoding="utf-8")

    def test_pm_spec_has_finite_budget_docs_allowlist_and_local_rule(self):
        self.assertEqual(verification_budget_errors(self.spec), [])
        self.assertEqual(docs_allowlist_errors(self.spec), [])
        self.assertEqual(one_correction_errors(self.spec), [])
        self.assertEqual(local_writer_errors(self.spec), [])

    def test_result_envelope_records_correction_rounds_and_docs_evidence(self):
        self.assertEqual(envelope_errors(self.spec), [])
        match = re.search(r"```json\n(.*?)```", self.spec, re.DOTALL)
        assert match is not None, "result envelope must contain a json code fence"
        payload = json.loads(match.group(1))
        self.assertEqual((payload["correction_rounds_used"], "docs_exemption" in payload), (0, True))

    def test_workflow_declares_the_same_finite_budget(self):
        for check in (
            verification_budget_errors,
            docs_allowlist_errors,
            one_correction_errors,
            local_writer_errors,
        ):
            with self.subTest(check=check.__name__):
                self.assertEqual(check(self.workflow), [])

    def test_odd_skill_applies_the_budget_and_local_rule(self):
        self.assertIn(BUDGET_HEADING.removeprefix("## "), self.odd_skill)
        self.assertIn("ONE fresh correction", self.odd_skill)
        self.assertIn("exactly ONE changed file per writer Task", self.odd_skill)
        self.assertIn("true docs/metadata unit", self.odd_skill)
        self.assertIn("`gentle-ai-worker-local`", self.odd_skill)

    def test_systematic_skill_applies_the_budget_without_a_post_code_loop(self):
        self.assertIn(BUDGET_HEADING.removeprefix("## "), self.systematic_skill)
        self.assertIn("ONE fresh correction", self.systematic_skill)
        self.assertIn("exactly ONE changed file per writer Task", self.systematic_skill)
        self.assertIn("true docs/metadata unit", self.systematic_skill)
        self.assertNotIn("post-code advice", self.systematic_skill.lower())

    def test_static_diagnostics_join_the_first_post_code_pass_on_every_surface(self):
        surfaces = {
            "pm-handoff spec": self.spec,
            "WORKFLOW.md": self.workflow,
            "workflow-odd-secure": self.odd_skill,
            "workflow-systematic": self.systematic_skill,
        }
        for name, text in surfaces.items():
            with self.subTest(surface=name):
                self.assertEqual(static_diagnostic_errors(text), [])
        mutated = self.spec.replace("SAME INITIAL candidate", "later candidate", 1)
        self.assertTrue(
            static_diagnostic_errors(mutated),
            "moving diagnostics off the initial candidate must fail the first-pass control",
        )

    def test_mutation_control_rejects_open_allowlist(self):
        mutated = self.spec.replace("uncertainty fails closed", "uncertainty may be inferred", 1)
        self.assertTrue(docs_allowlist_errors(mutated), "an open allowlist must fail the docs control")

    def test_mutation_control_rejects_test_reader_exemption(self):
        mutated = self.spec.replace(
            "Any test/verifier reader disqualifies the unit",
            "A test/verifier reader may be ignored",
            1,
        )
        self.assertTrue(docs_allowlist_errors(mutated), "a test-reader exemption must fail closed")

    def test_mutation_control_rejects_open_ended_correction_loop(self):
        mutated = self.spec.replace(
            "one initial writer plus ONE fresh correction writer",
            "one initial writer and repeat as needed",
            1,
        )
        self.assertTrue(one_correction_errors(mutated), "an open loop must fail the correction cap")

    def test_mutation_control_rejects_unbounded_local_batch(self):
        mutated = self.spec.replace(
            "exactly ONE changed file per writer Task",
            "any number of changed files per writer Task",
            1,
        )
        self.assertTrue(local_writer_errors(mutated), "an unbounded local batch must fail the rule")

    def test_mutation_control_rejects_missing_verifier_tier(self):
        mutated = self.spec.replace("one independent verifier", "an optional verifier")
        self.assertTrue(verification_budget_errors(mutated), "the high verifier tier must be present")

    def test_mutation_control_rejects_missing_correction_counter(self):
        mutated = self.spec.replace('"correction_rounds_used": 0,', "", 1)
        self.assertTrue(envelope_errors(mutated), "the envelope must record correction_rounds_used")

    def test_mutation_controls_reject_code_only_gate_and_native_loop(self):
        code_only = self.spec.replace("only when the unit's actual-diff budget requires it", "only for a code-changing unit", 1)
        self.assertTrue(verification_budget_errors(code_only))
        native_loop = self.spec.replace("no PM advisor or verifier cycle", "a PM advisor or verifier cycle", 1)
        self.assertTrue(one_correction_errors(native_loop))


if __name__ == "__main__":
    unittest.main()
