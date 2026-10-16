"""Durable checks for the PM task allowlists (Q72 T1).

Parses the tracked ``global-config/opencode.json`` and asserts that BOTH live project-manager
lanes (``pm-odd``, ``pm-systematic``) can reach the tiny-fix writer (``gentle-ai-worker`` and its
local tier) and the independent verifier (``gentle-ai-verify`` and its runtime Astra alias) by
listing each key with value ``"allow"`` inside the PM's ``permission.task`` map.

The PositiveControl class proves the validator can fail: a removed key, a downgraded value, an
absent ``permission.task`` block, and an absent PM agent key are each reported rather than
silently passing.

Run: python3 -m unittest tests/test_pm_task_allowlists.py -v
"""

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "global-config" / "opencode.json"

# The two live project-manager lanes; pm-sdd was retired by Q65 (5aadb9f).
PM_NAMES = ("pm-odd", "pm-systematic")

# Tiny-fix reachability: the named writer (both tiers) and the independent verifier (plus the
# runtime Astra alias that astra-sol-upgrade.ts creates). Owner decisions, 2026-10-15.
TASK_ALLOW_KEYS = (
    "gentle-ai-worker",
    "gentle-ai-worker-local",
    "gentle-ai-verify",
    "gentle-ai-verify-astra",
)

ALLOW = "allow"


def load_config(path=CONFIG_PATH):
    """Load and return the parsed config object from PATH."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def missing_task_allows(data, pms=PM_NAMES, keys=TASK_ALLOW_KEYS):
    """Return (pm, key, reason) triples for each missing allowlist entry.

    An absent PM agent key, an absent or non-object ``permission.task`` block, an absent key, and
    a value other than ``"allow"`` are all reported, so the check never silently passes a
    malformed allowlist.
    """
    missing = []
    for pm in pms:
        agent = data.get("agent", {}).get(pm)
        if not isinstance(agent, dict):
            missing.append((pm, "*", "agent key is absent or not an object"))
            continue
        permission = agent.get("permission")
        if not isinstance(permission, dict):
            missing.append((pm, "*", "permission block is absent or not an object"))
            continue
        task = permission.get("task")
        if not isinstance(task, dict):
            missing.append((pm, "*", "permission.task block is absent or not an object"))
            continue
        for key in keys:
            if key not in task:
                missing.append((pm, key, "task allowlist key is absent"))
            elif task[key] != ALLOW:
                missing.append((pm, key, f"task allowlist value is {task[key]!r}, not {ALLOW!r}"))
    return missing


def probe(path=CONFIG_PATH):
    """Presence probe: one boolean per (pm, key), True when the key maps to allow."""
    data = load_config(path)
    present = {}
    for pm in PM_NAMES:
        task = data.get("agent", {}).get(pm, {}).get("permission", {}).get("task", {})
        for key in TASK_ALLOW_KEYS:
            present[(pm, key)] = isinstance(task, dict) and task.get(key) == ALLOW
    return present


class RealConfig(unittest.TestCase):
    def setUp(self):
        self.assertTrue(CONFIG_PATH.is_file(), f"{CONFIG_PATH} missing")
        self.data = load_config()

    def test_config_is_valid_json_object(self):
        self.assertIsInstance(self.data, dict, "config must parse to a JSON object")

    def test_each_pm_can_reach_the_tiny_fix_writer_and_verifier(self):
        missing = missing_task_allows(self.data)
        self.assertEqual(missing, [], f"PM task allowlist gaps: {missing}")


class PositiveControl(unittest.TestCase):
    """Prove the validator can fail; without this a green run proves nothing."""

    @staticmethod
    def _synthetic():
        return {
            "agent": {
                pm: {"permission": {"task": {key: ALLOW for key in TASK_ALLOW_KEYS}}}
                for pm in PM_NAMES
            }
        }

    def test_removed_key_is_reported(self):
        data = self._synthetic()
        self.assertEqual(missing_task_allows(data), [])
        del data["agent"]["pm-odd"]["permission"]["task"]["gentle-ai-worker"]
        missing = missing_task_allows(data)
        self.assertEqual([(pm, key) for pm, key, _ in missing], [("pm-odd", "gentle-ai-worker")])
        self.assertIn("absent", missing[0][2])

    def test_downgraded_value_is_reported(self):
        data = self._synthetic()
        data["agent"]["pm-systematic"]["permission"]["task"]["gentle-ai-verify"] = "deny"
        missing = missing_task_allows(data)
        self.assertEqual([(pm, key) for pm, key, _ in missing], [("pm-systematic", "gentle-ai-verify")])
        self.assertIn("not 'allow'", missing[0][2])

    def test_absent_task_block_is_reported(self):
        data = self._synthetic()
        del data["agent"]["pm-odd"]["permission"]["task"]
        missing = missing_task_allows(data, pms=("pm-odd",))
        self.assertEqual([(pm, key) for pm, key, _ in missing], [("pm-odd", "*")])
        self.assertIn("permission.task", missing[0][2])

    def test_absent_agent_key_is_reported(self):
        data = self._synthetic()
        del data["agent"]["pm-systematic"]
        missing = missing_task_allows(data, pms=("pm-systematic",))
        self.assertEqual([(pm, key) for pm, key, _ in missing], [("pm-systematic", "*")])
        self.assertIn("agent key", missing[0][2])


if __name__ == "__main__":
    print("task allowlist probe:", probe())
    unittest.main()
