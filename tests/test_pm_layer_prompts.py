"""Durable checks for the PM-handoff prompt teaching (Q71 T1).

Parses the tracked ``global-config/opencode.json`` and asserts three things on the
EMBEDDED prompt strings:

- the ``gentle-orchestrator`` prompt names the ``pm-unit-brief/v1`` brief schema
  and its authoritative contract file ``docs/specs/pm-handoff.md``;
- each live project-manager prompt (``pm-odd``, ``pm-systematic``) teaches the
  read-based line-count/last-line/branch-HEAD anchor and its working-tree limit;
- each PM prompt names only the DeepSeek-family ``odd-apply``/``gentle-ai-worker``
  writers for a mid-unit tiny fix and rejects the stale ``general`` sentence.

Every needle is asserted against ONE agent's own prompt, never against a joined
string, so a needle present in a different agent's prompt cannot satisfy the
check. The PositiveControl class proves each assertion can fail: a needle
removed, an agent key absent, and a non-string prompt are all reported, a
cross-agent contamination case proves a substring carried by a different agent
does not silence the check, and the tiny-fix writer control is mutation-tested
by reintroducing the stale sentence and by dropping a required writer clause.

Run: python3 -m unittest tests/test_pm_layer_prompts.py -v
"""

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "global-config" / "opencode.json"

ORCHESTRATOR = "gentle-orchestrator"

# Only the two live project-manager lanes. pm-sdd was retired by Q65 (5aadb9f)
# and pm-probe is retired; asserting them here would pin non-existent agents.
AGENT_NAMES = ("pm-odd", "pm-systematic")

# The orchestrator must name the brief schema tag AND its authoritative contract
# file, so an orchestrator can build a valid pm-unit-brief/v1 handoff.
ORCHESTRATOR_NEEDLES = ("pm-unit-brief/v1", "docs/specs/pm-handoff.md")
ORCHESTRATOR_FIXED_TOOL_NEEDLES = (
    "ask-gated `host_plan_write`",
    "allow-gated `host_test_run`",
    "never arbitrary caller argv, pipes, redirects, or shell",
    "remains inert until the host tool ships",
)

# The PM must use only observable read output and avoid claiming commit/content equality.
PM_ANCHOR_NEEDLES = (
    "line count",
    "exact last-line text",
    "feature-branch HEAD commit SHA",
    "working-tree tracker",
    "does not establish that the tracker contents are committed",
)
PM_PLANNING_SKIP_NEEDLE = "Planning creation skips the anchor comparison"
PM_OLD_HASH_WORDING = "tracker_sha256"

# Owner correction 2026-10-19: a PM's mid-unit tiny fix dispatches a named
# DeepSeek-family writer, never the orchestrator-only `general` lane.
PM_TINY_FIX_WRITERS = ("odd-apply", "gentle-ai-worker")
PM_TINY_FIX_STALE_SENTENCE = (
    "Tiny-fix option: mid-unit, you may dispatch `general` for a genuinely tiny fix "
    "only within the brief's allowed paths."
)
PM_TINY_FIX_INSTRUCTION = (
    "Tiny-fix option: mid-unit, for a genuinely tiny fix dispatch `odd-apply` or "
    "`gentle-ai-worker` (DeepSeek family), never `general`, and only within the "
    "brief's allowed paths."
)


def assert_no_old_planning_blocking_wording(prompt):
    if PM_OLD_HASH_WORDING in prompt:
        raise AssertionError("PM prompt must not require tracker hashes")


def load_config(path=CONFIG_PATH):
    """Load and return the parsed config object from PATH."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def prompt_of(data, name):
    """Return agent NAME's prompt string, or None when absent or not a string."""
    prompt = data.get("agent", {}).get(name, {}).get("prompt")
    return prompt if isinstance(prompt, str) else None


def fixed_tool_prompt_gaps(prompt):
    """Return the fixed-host-tool needles missing from one orchestrator prompt."""
    text = prompt if isinstance(prompt, str) else ""
    return [needle for needle in ORCHESTRATOR_FIXED_TOOL_NEEDLES if needle not in text]


def missing_prompt_needles(data, agents=AGENT_NAMES):
    """Return (agent, needle, reason) triples for each missing or unreadable needle.

    Each needle is checked only against its own agent's prompt; an absent agent
    key or a non-string prompt is reported too, so the check never silently
    passes a malformed config.
    """
    missing = []
    for needle in ORCHESTRATOR_NEEDLES:
        prompt = prompt_of(data, ORCHESTRATOR)
        if prompt is None:
            missing.append((ORCHESTRATOR, needle, "agent key absent or prompt not a string"))
        elif needle not in prompt:
            missing.append((ORCHESTRATOR, needle, "prompt does not contain the needle"))
    for name in agents:
        prompt = prompt_of(data, name)
        if prompt is None:
            missing.append((name, PM_ANCHOR_NEEDLES[0], "agent key absent or prompt not a string"))
        else:
            for needle in (*PM_ANCHOR_NEEDLES, PM_PLANNING_SKIP_NEEDLE):
                if needle not in prompt:
                    missing.append((name, needle, "prompt does not contain the needle"))
            if PM_OLD_HASH_WORDING in prompt:
                missing.append((name, PM_OLD_HASH_WORDING, "prompt still requires tracker hash"))
    return missing


def tiny_fix_prompt_gaps(data, agents=AGENT_NAMES):
    """Return (agent, reason) for each PM prompt violating the tiny-fix writer contract.

    The exact sentence must occur once per agent, so a stale sentence left beside
    the corrected one is still reported. The named writers and the forbidden
    ``general`` lane are part of that single sentence, which keeps the check from
    drifting into a second, parallel set of needles.
    """
    gaps = []
    for name in agents:
        prompt = prompt_of(data, name)
        if prompt is None:
            gaps.append((name, "agent key absent or prompt not a string"))
            continue
        occurrences = prompt.count(PM_TINY_FIX_INSTRUCTION)
        if occurrences != 1:
            gaps.append((name, f"named writer instruction occurs {occurrences} times, not exactly once"))
        if PM_TINY_FIX_STALE_SENTENCE in prompt:
            gaps.append((name, "stale general tiny-fix sentence present"))
    return gaps


def probe(path=CONFIG_PATH):
    """Presence probe: one (agent, needle, present) triple per checked needle."""
    data = load_config(path)
    results = []
    orchestrator_prompt = prompt_of(data, ORCHESTRATOR) or ""
    for needle in ORCHESTRATOR_NEEDLES:
        results.append((ORCHESTRATOR, needle, needle in orchestrator_prompt))
    for name in AGENT_NAMES:
        prompt = prompt_of(data, name) or ""
        results.extend((name, needle, needle in prompt) for needle in PM_ANCHOR_NEEDLES)
    return results


class RealConfig(unittest.TestCase):
    def setUp(self):
        self.assertTrue(CONFIG_PATH.is_file(), f"{CONFIG_PATH} missing")
        self.data = load_config()

    def test_config_is_valid_json_object(self):
        self.assertIsInstance(self.data, dict, "config must parse to a JSON object")

    def test_orchestrator_prompt_names_brief_contract(self):
        prompt = prompt_of(self.data, ORCHESTRATOR)
        self.assertIsInstance(prompt, str, "orchestrator prompt must be a string")
        for needle in ORCHESTRATOR_NEEDLES:
            with self.subTest(agent=ORCHESTRATOR, needle=needle):
                self.assertIn(
                    needle,
                    prompt,
                    f"{ORCHESTRATOR} prompt is missing {needle!r}",
                )

    def test_orchestrator_prompt_names_narrow_fixed_tool_exceptions(self):
        prompt = prompt_of(self.data, ORCHESTRATOR)
        self.assertIsInstance(prompt, str, "orchestrator prompt must be a string")
        self.assertEqual(fixed_tool_prompt_gaps(prompt), [])

    def test_each_pm_prompt_teaches_readable_anchor_and_working_tree_limit(self):
        for name in AGENT_NAMES:
            with self.subTest(agent=name):
                prompt = prompt_of(self.data, name)
                self.assertIsInstance(prompt, str, f"agent {name!r} prompt must be a string")
                for needle in (*PM_ANCHOR_NEEDLES, PM_PLANNING_SKIP_NEEDLE):
                    self.assertIn(needle, prompt, f"agent {name!r} prompt is missing {needle!r}")
                self.assertNotIn(PM_OLD_HASH_WORDING, prompt)


    def test_pm_prompts_do_not_block_planning_creation_for_missing_hashes(self):
        for name in AGENT_NAMES:
            with self.subTest(agent=name):
                assert_no_old_planning_blocking_wording(prompt_of(self.data, name))

    def test_pm_prompts_use_the_named_deepseek_tiny_fix_writers(self):
        gaps = tiny_fix_prompt_gaps(self.data)
        self.assertEqual(gaps, [], f"PM tiny-fix prompt gaps: {gaps}")

    def test_pm_prompts_remain_under_character_cap(self):
        for name in AGENT_NAMES:
            with self.subTest(agent=name):
                prompt = prompt_of(self.data, name)
                self.assertIsInstance(prompt, str, f"agent {name!r} prompt must be a string")
                self.assertLess(len(prompt), 6000, f"agent {name!r} prompt exceeds the 6,000-character cap")
                print(f"{name} prompt characters: {len(prompt)}, bytes: {len(prompt.encode('utf-8'))}")

class PositiveControl(unittest.TestCase):
    """Prove the validator can fail; without this a green run proves nothing."""

    @staticmethod
    def _synthetic():
        orchestrator = (
            "orchestrator preamble "
            + " ".join((*ORCHESTRATOR_NEEDLES, *ORCHESTRATOR_FIXED_TOOL_NEEDLES))
        )
        pm = "pm preamble " + " ".join(
            (*PM_ANCHOR_NEEDLES, PM_PLANNING_SKIP_NEEDLE, PM_TINY_FIX_INSTRUCTION)
        )
        return {
            "agent": {
                ORCHESTRATOR: {"prompt": orchestrator},
                "pm-odd": {"prompt": pm},
                "pm-systematic": {"prompt": pm},
            }
        }

    def test_old_planning_blocking_wording_fails_negative_assertion(self):
        with self.assertRaisesRegex(AssertionError, "must not require tracker hashes"):
            assert_no_old_planning_blocking_wording("tracker_sha256 is required")

    def test_stale_general_tiny_fix_sentence_is_reported_for_both_pms(self):
        for name in AGENT_NAMES:
            data = self._synthetic()
            prompt = data["agent"][name]["prompt"]
            data["agent"][name]["prompt"] = prompt.replace(
                PM_TINY_FIX_INSTRUCTION, PM_TINY_FIX_STALE_SENTENCE
            )
            with self.subTest(agent=name):
                gaps = tiny_fix_prompt_gaps(data)
                self.assertIn((name, "stale general tiny-fix sentence present"), gaps)
                self.assertIn(
                    (name, "named writer instruction occurs 0 times, not exactly once"),
                    gaps,
                )

    def test_dropped_writer_clause_is_reported(self):
        data = self._synthetic()
        writer_clause = f"`{PM_TINY_FIX_WRITERS[0]}` or "
        prompt = data["agent"]["pm-systematic"]["prompt"]
        self.assertIn(writer_clause, prompt)
        data["agent"]["pm-systematic"]["prompt"] = prompt.replace(writer_clause, "", 1)
        gaps = tiny_fix_prompt_gaps(data)
        self.assertIn(
            ("pm-systematic", "named writer instruction occurs 0 times, not exactly once"),
            gaps,
        )

    def test_removed_anchor_needles_are_reported(self):
        data = self._synthetic()
        self.assertEqual(missing_prompt_needles(data), [])
        data["agent"]["pm-odd"]["prompt"] = "no mechanism here"
        missing = missing_prompt_needles(data)
        self.assertEqual(
            [(agent, needle, reason) for agent, needle, reason in missing],
            [("pm-odd", needle, "prompt does not contain the needle")
             for needle in (*PM_ANCHOR_NEEDLES, PM_PLANNING_SKIP_NEEDLE)],
        )

    def test_fixed_tool_needle_removal_is_detected(self):
        data = self._synthetic()
        prompt = data["agent"][ORCHESTRATOR]["prompt"]
        self.assertEqual(fixed_tool_prompt_gaps(prompt), [])
        for needle in ORCHESTRATOR_FIXED_TOOL_NEEDLES:
            with self.subTest(needle=needle):
                mutated = prompt.replace(needle, "", 1)
                self.assertIn(needle, fixed_tool_prompt_gaps(mutated))

    def test_absent_agent_key_is_reported(self):
        data = self._synthetic()
        del data["agent"]["pm-systematic"]
        missing = missing_prompt_needles(data)
        self.assertEqual([agent for agent, _, _ in missing], ["pm-systematic"])
        self.assertIn("absent", missing[0][2])

    def test_non_string_prompt_is_reported(self):
        data = self._synthetic()
        data["agent"][ORCHESTRATOR]["prompt"] = None
        missing = missing_prompt_needles(data)
        self.assertEqual(sorted({agent for agent, _, _ in missing}), [ORCHESTRATOR])
        self.assertTrue(all("not a string" in reason for _, _, reason in missing))

    def test_cross_agent_needle_does_not_silence_check(self):
        # Contamination control: the orchestrator prompt lacks its own needles
        # while a DIFFERENT agent's prompt carries them. A joined-string check
        # would pass; the per-agent check must still report the orchestrator.
        data = self._synthetic()
        data["agent"][ORCHESTRATOR]["prompt"] = "orchestrator without the contract tag"
        data["agent"]["pm-odd"]["prompt"] = (
            PM_ANCHOR_NEEDLES[0] + " " + " ".join(ORCHESTRATOR_NEEDLES)
        )
        missing = missing_prompt_needles(data)
        self.assertEqual(len(missing), len(ORCHESTRATOR_NEEDLES) + len(PM_ANCHOR_NEEDLES))
        self.assertEqual({agent for agent, _, _ in missing}, {ORCHESTRATOR, "pm-odd"})


if __name__ == "__main__":
    print("presence probe (gentle-orchestrator, pm-odd, pm-systematic):", probe())
    unittest.main()
