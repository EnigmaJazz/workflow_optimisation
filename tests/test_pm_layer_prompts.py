"""Durable checks for the PM-handoff prompt teaching (Q71 T1).

Parses the tracked ``global-config/opencode.json`` and asserts two things on the
EMBEDDED prompt strings:

- the ``gentle-orchestrator`` prompt names the ``pm-unit-brief/v1`` brief schema
  and its authoritative contract file ``docs/specs/pm-handoff.md``;
- each live project-manager prompt (``pm-odd``, ``pm-systematic``) teaches the
  committed-tracker hash comparison against the orchestrator-supplied value.

Every needle is asserted against ONE agent's own prompt, never against a joined
string, so a needle present in a different agent's prompt cannot satisfy the
check. The PositiveControl class proves each assertion can fail: a needle
removed, an agent key absent, and a non-string prompt are all reported, and a
cross-agent contamination case proves a substring carried by a different agent
does not silence the check.

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

# Stable part of the committed-tracker hash comparison both PM prompts must teach.
PM_COMPLETE_READ_NEEDLE = "compare the tracker at unit start with the brief's `tracker_sha256`"
PM_PLANNING_SKIP_NEEDLE = "hash fields are explicit `none` and comparison is skipped"
PM_REHASH_NEEDLE = "recompute and report the final hash"
PM_FIX_FORWARD_NEEDLE = "fix-forward/re-hash instruction"
PM_OLD_BLOCKING_WORDING = "if the file or supplied hash is absent, the supplied hash is empty"


def assert_no_old_planning_blocking_wording(prompt):
    if PM_OLD_BLOCKING_WORDING in prompt:
        raise AssertionError("planning creation must skip the dispatch-time hash comparison")


def load_config(path=CONFIG_PATH):
    """Load and return the parsed config object from PATH."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def prompt_of(data, name):
    """Return agent NAME's prompt string, or None when absent or not a string."""
    prompt = data.get("agent", {}).get(name, {}).get("prompt")
    return prompt if isinstance(prompt, str) else None


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
            missing.append((name, PM_COMPLETE_READ_NEEDLE, "agent key absent or prompt not a string"))
        else:
            for needle in (PM_COMPLETE_READ_NEEDLE, PM_PLANNING_SKIP_NEEDLE, PM_REHASH_NEEDLE, PM_FIX_FORWARD_NEEDLE):
                if needle not in prompt:
                    missing.append((name, needle, "prompt does not contain the needle"))
    return missing


def probe(path=CONFIG_PATH):
    """Presence probe: one (agent, needle, present) triple per checked needle."""
    data = load_config(path)
    results = []
    orchestrator_prompt = prompt_of(data, ORCHESTRATOR) or ""
    for needle in ORCHESTRATOR_NEEDLES:
        results.append((ORCHESTRATOR, needle, needle in orchestrator_prompt))
    for name in AGENT_NAMES:
        prompt = prompt_of(data, name) or ""
        results.append((name, PM_COMPLETE_READ_NEEDLE, PM_COMPLETE_READ_NEEDLE in prompt))
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

    def test_each_pm_prompt_teaches_committed_tracker_hash_comparison(self):
        for name in AGENT_NAMES:
            with self.subTest(agent=name):
                prompt = prompt_of(self.data, name)
                self.assertIsInstance(prompt, str, f"agent {name!r} prompt must be a string")
                self.assertIn(
                    PM_COMPLETE_READ_NEEDLE,
                    prompt,
                    f"agent {name!r} prompt must teach the committed-tracker hash comparison",
                )


    def test_pm_prompts_do_not_block_planning_creation_for_missing_hashes(self):
        for name in AGENT_NAMES:
            with self.subTest(agent=name):
                assert_no_old_planning_blocking_wording(prompt_of(self.data, name))

    def test_pm_prompts_remain_under_character_cap(self):
        for name in AGENT_NAMES:
            with self.subTest(agent=name):
                prompt = prompt_of(self.data, name)
                self.assertIsInstance(prompt, str, f"agent {name!r} prompt must be a string")
                self.assertLess(len(prompt), 6000, f"agent {name!r} prompt exceeds the 6,000-character cap")
                print(f"{name} prompt characters: {len(prompt)}")


class PositiveControl(unittest.TestCase):
    """Prove the validator can fail; without this a green run proves nothing."""

    @staticmethod
    def _synthetic():
        orchestrator = "orchestrator preamble " + " ".join(ORCHESTRATOR_NEEDLES)
        pm = "pm preamble " + " ".join((PM_COMPLETE_READ_NEEDLE, PM_PLANNING_SKIP_NEEDLE, PM_REHASH_NEEDLE, PM_FIX_FORWARD_NEEDLE))
        return {
            "agent": {
                ORCHESTRATOR: {"prompt": orchestrator},
                "pm-odd": {"prompt": pm},
                "pm-systematic": {"prompt": pm},
            }
        }

    def test_old_planning_blocking_wording_fails_negative_assertion(self):
        with self.assertRaisesRegex(AssertionError, "planning creation must skip"):
            assert_no_old_planning_blocking_wording(
                "Return BLOCKED " + PM_OLD_BLOCKING_WORDING
            )

    def test_removed_hash_comparison_needle_is_reported(self):
        data = self._synthetic()
        self.assertEqual(missing_prompt_needles(data), [])
        data["agent"]["pm-odd"]["prompt"] = "no mechanism here"
        missing = missing_prompt_needles(data)
        self.assertEqual([(agent, needle, reason) for agent, needle, reason in missing],
                         [("pm-odd", needle, "prompt does not contain the needle")
                          for needle in (PM_COMPLETE_READ_NEEDLE, PM_PLANNING_SKIP_NEEDLE, PM_REHASH_NEEDLE, PM_FIX_FORWARD_NEEDLE)])

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
            PM_COMPLETE_READ_NEEDLE + " " + " ".join(ORCHESTRATOR_NEEDLES)
        )
        missing = missing_prompt_needles(data)
        self.assertEqual(len(missing), len(ORCHESTRATOR_NEEDLES) + 3)
        self.assertEqual({agent for agent, _, _ in missing}, {ORCHESTRATOR, "pm-odd"})


if __name__ == "__main__":
    print("presence probe (gentle-orchestrator, pm-odd, pm-systematic):", probe())
    unittest.main()
