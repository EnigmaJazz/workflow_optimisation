"""Durable checks for the sandbox lifecycle ordering rule in agent prompts.

Parses the tracked ``global-config/opencode.json`` and asserts that each of the
sandbox-writing agents carries the ordering rule that ``sandbox_finish`` must be
called before ``sandbox_apply``. The rule is inlined in four agent prompts; a
future editor must not be able to "fix" a failure by deleting the assertion, so
the stable NEEDLE is a module-level constant.

The PositiveControl class proves the validator can fail: a synthetic config with
the needle removed, with an agent key deleted, or with a non-string prompt is
reported as missing rather than silently passing.

Run: python3 -m unittest tests/test_sandbox_lifecycle_prompts.py -v
"""

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "global-config" / "opencode.json"

# Stable part of the rule; an editor must not weaken this by editing the test.
NEEDLE = "Sandbox lifecycle: always call `sandbox_finish` BEFORE `sandbox_apply`"

AGENT_NAMES = ("general", "gentle-ai-worker", "gentle-ai-worker-local", "odd-apply")


def load_config(path=CONFIG_PATH):
    """Load and return the parsed config object from PATH."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def missing_needle_agents(data, names=AGENT_NAMES):
    """Return (name, reason) pairs for each agent whose prompt lacks the needle.

    An absent agent key or a non-string prompt is reported too, so the check
    never silently passes a malformed config.
    """
    missing = []
    for name in names:
        agent = data.get("agent", {}).get(name)
        if agent is None:
            missing.append((name, "agent key is absent"))
            continue
        prompt = agent.get("prompt")
        if not isinstance(prompt, str):
            missing.append((name, f"prompt is not a string: {type(prompt).__name__}"))
            continue
        if NEEDLE not in prompt:
            missing.append((name, "prompt does not contain the lifecycle needle"))
    return missing


def probe(path=CONFIG_PATH):
    """Presence probe: one boolean per agent, True when the needle is present."""
    data = load_config(path)
    present = []
    for name in AGENT_NAMES:
        prompt = data.get("agent", {}).get(name, {}).get("prompt")
        present.append(isinstance(prompt, str) and NEEDLE in prompt)
    return present


class RealConfig(unittest.TestCase):
    def setUp(self):
        self.assertTrue(CONFIG_PATH.is_file(), f"{CONFIG_PATH} missing")
        self.data = load_config()

    def test_config_is_valid_json_object(self):
        self.assertIsInstance(self.data, dict, "config must parse to a JSON object")

    def test_each_agent_prompt_contains_lifecycle_needle(self):
        for name in AGENT_NAMES:
            with self.subTest(agent=name):
                prompt = self.data.get("agent", {}).get(name, {}).get("prompt")
                self.assertIsInstance(prompt, str, f"agent {name!r} prompt must be a string")
                self.assertIn(NEEDLE, prompt, f"agent {name!r} prompt is missing the sandbox lifecycle rule")


class PositiveControl(unittest.TestCase):
    """Prove the validator can fail; without this a green run proves nothing."""

    @staticmethod
    def _synthetic(prompts):
        return {"agent": {name: {"prompt": text} for name, text in prompts.items()}}

    def test_needle_removed_is_reported(self):
        data = self._synthetic({name: NEEDLE + " trailing" for name in AGENT_NAMES})
        self.assertEqual(missing_needle_agents(data), [])
        data["agent"]["general"]["prompt"] = ""
        missing = missing_needle_agents(data)
        self.assertEqual([name for name, _ in missing], ["general"])
        self.assertIn("does not contain", missing[0][1])

    def test_absent_agent_key_is_reported(self):
        data = self._synthetic({name: NEEDLE for name in AGENT_NAMES})
        del data["agent"]["odd-apply"]
        missing = missing_needle_agents(data)
        self.assertEqual([name for name, _ in missing], ["odd-apply"])
        self.assertIn("absent", missing[0][1])

    def test_non_string_prompt_is_reported(self):
        data = self._synthetic({name: NEEDLE for name in AGENT_NAMES})
        data["agent"]["gentle-ai-worker"]["prompt"] = None
        missing = missing_needle_agents(data)
        self.assertEqual([name for name, _ in missing], ["gentle-ai-worker"])
        self.assertIn("not a string", missing[0][1])


if __name__ == "__main__":
    print("presence probe (general, gentle-ai-worker, gentle-ai-worker-local, odd-apply):", probe())
    unittest.main()
