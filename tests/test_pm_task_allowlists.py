"""Durable checks for the PM task allowlists (Q72 T1).

Parses the tracked ``global-config/opencode.json`` and asserts that BOTH live project-manager
lanes (``pm-odd``, ``pm-systematic``) can reach their named DeepSeek tiny-fix writers and the
independent verifier (``gentle-ai-verify`` and its runtime Astra alias) via ``permission.task``,
while rejecting the orchestrator-only ``general`` lane on every PM. The strict maximum allowlist
and its mutation controls live in ``tests/test_review_pipeline_permissions.py``; this module keeps
the config-level required-lane and forbidden-lane checks.

The PositiveControl class proves the config-level validators can fail: a removed key, a downgraded
value, an absent ``permission.task`` block, an absent PM agent key, and a forbidden ``general``
grant on either PM are each reported rather than silently passing.

Run: python3 -m unittest tests/test_pm_task_allowlists.py -v
"""

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "global-config" / "opencode.json"

# The two live project-manager lanes; pm-sdd was retired by Q65 (5aadb9f).
PM_NAMES = ("pm-odd", "pm-systematic")

# Named tiny-fix writers/verifiers reachable by each PM. `general` is
# orchestrator-only after the 2026-10-19 owner correction; it must not appear in
# either PM task map.
TASK_ALLOW_KEYS = (
    "gentle-ai-worker",
    "gentle-ai-worker-local",
    "gentle-ai-verify",
    "gentle-ai-verify-astra",
)

PM_REQUIRED_TASK_ALLOW = {
    "pm-odd": ("odd-apply", *TASK_ALLOW_KEYS),
    "pm-systematic": TASK_ALLOW_KEYS,
}

# Strict maximum allowlist and general-reintroduction controls execute against the
# production verifier predicate in tests/test_review_pipeline_permissions.py; this
# module keeps the config-level required-lane and absence checks.

ALLOW = "allow"

# The general lane stays orchestrator-only; a PM must not grant it even though
# the required-lane check above only looks for missing or downgraded keys.
FORBIDDEN_TASK_ALLOW = ("general",)


def load_config(path=CONFIG_PATH):
    """Load and return the parsed config object from PATH."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def missing_task_allows(data, pms=PM_NAMES):
    """Return (pm, key, reason) triples for each missing required allowlist entry.

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
        for key in PM_REQUIRED_TASK_ALLOW[pm]:
            if key not in task:
                missing.append((pm, key, "task allowlist key is absent"))
            elif task[key] != ALLOW:
                missing.append((pm, key, f"task allowlist value is {task[key]!r}, not {ALLOW!r}"))
    return missing


def forbidden_task_allows(data, pms=PM_NAMES):
    """Return (pm, key, reason) for each forbidden task lane granted to a PM.

    A structurally malformed ``permission.task`` block is already reported by
    ``missing_task_allows``; this validator adds only the forbidden-lane grant, so
    the real-config check is executable and not a bare ``assertNotIn`` mirror.
    """
    forbidden = []
    for pm in pms:
        task = data.get("agent", {}).get(pm, {}).get("permission", {}).get("task")
        if not isinstance(task, dict):
            continue
        for key in FORBIDDEN_TASK_ALLOW:
            if task.get(key) == ALLOW:
                forbidden.append((pm, key, "orchestrator-only task lane must not be allowed"))
    return forbidden


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

    def test_pm_task_maps_do_not_grant_general(self):
        forbidden = forbidden_task_allows(self.data)
        self.assertEqual(forbidden, [], f"PM forbidden task lanes: {forbidden}")


class PositiveControl(unittest.TestCase):
    """Prove the validator can fail; without this a green run proves nothing."""

    @staticmethod
    def _synthetic():
        return {
            "agent": {
                pm: {
                    "permission": {
                        "task": {key: ALLOW for key in PM_REQUIRED_TASK_ALLOW[pm]}
                    }
                }
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

    def test_general_grant_is_reported_for_both_pms(self):
        for pm in PM_NAMES:
            data = self._synthetic()
            data["agent"][pm]["permission"]["task"]["general"] = ALLOW
            with self.subTest(agent=pm):
                self.assertEqual(
                    forbidden_task_allows(data, pms=(pm,)),
                    [(pm, "general", "orchestrator-only task lane must not be allowed")],
                )
                # Reintroducing `general` must not quietly drop a required
                # writer/verifier lane from the same PM task map.
                self.assertEqual(missing_task_allows(data, pms=(pm,)), [])


if __name__ == "__main__":
    print("task allowlist probe:", probe())
    unittest.main()
