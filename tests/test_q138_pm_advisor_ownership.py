"""Q138: the Planner lane owns advisor dispatch; the PMs hold no advisor task grant.

Parses the tracked ``global-config/opencode.json`` and asserts that neither live
project-manager lane can dispatch a registered ``advisor-*-pre``/``-post`` seat,
while the Planner keeps every advisor lane and its ``*`` deny. It also pins the
verifier dispatcher allowlist and the Planner-owned prose in ``WORKFLOW.md`` and
``docs/specs/pm-handoff.md``. The PositiveControl class proves every validator can
fail, including the executed verifier predicate control living in
``tests/test_advisor_checker_policy.py``.

Run: python3 -m unittest tests/test_q138_pm_advisor_ownership.py -v
"""

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "global-config" / "opencode.json"
WORKFLOW = REPO / "WORKFLOW.md"
HANDOFF = REPO / "docs/specs/pm-handoff.md"
CHECKER = REPO / "verify/checkers/check-runtime-agents.cjs"

PM_NAMES = ("pm-odd", "pm-systematic")
PLANNER = "planner"
ADVISORS = (
    "advisor-design-pre", "advisor-integration-pre", "advisor-testing-pre",
    "advisor-security-pre", "advisor-maintainability-pre",
    "advisor-design-post", "advisor-integration-post", "advisor-testing-post",
    "advisor-security-post", "advisor-maintainability-post",
    "advisor-spec-pre", "advisor-spec-post",
)
PM_KEPT_LANES = {
    "pm-odd": ("*", "explore", "gentle-ai-worker", "gentle-ai-worker-local",
               "gentle-ai-verify", "gentle-ai-verify-routine",
               "gentle-ai-verify-astra", "odd-apply", "planner"),
    "pm-systematic": ("*", "explore", "gentle-ai-worker", "gentle-ai-worker-local",
                      "gentle-ai-verify", "gentle-ai-verify-routine",
                      "gentle-ai-verify-astra", "planner"),
}
ALLOW = "allow"
DISPATCHABLE = ("allow", "ask")
EXPECTED_DISPATCHER_LINE = 'const advisorDispatchers=new Set(["planner"])'


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def pm_advisor_grants(data):
    """Return (pm, key, value) for every advisor lane a PM can still dispatch."""
    grants = []
    for pm in PM_NAMES:
        agent = data.get("agent", {}).get(pm)
        permission = agent.get("permission") if isinstance(agent, dict) else None
        task = permission.get("task") if isinstance(permission, dict) else None
        if not isinstance(task, dict):
            grants.append((pm, "*", "permission.task missing or not an object"))
            continue
        for key, value in task.items():
            if key.startswith("advisor-") and value in DISPATCHABLE:
                grants.append((pm, key, value))
    return grants


def missing_kept_lanes(data):
    """Return (pm, lane, observed) for each PM lane the removal must not drop."""
    gaps = []
    for pm, lanes in PM_KEPT_LANES.items():
        task = data.get("agent", {}).get(pm, {}).get("permission", {}).get("task", {})
        for lane in lanes:
            expected = "deny" if lane == "*" else ALLOW
            if task.get(lane) != expected:
                gaps.append((pm, lane, task.get(lane)))
    return gaps


def planner_advisor_gaps(data):
    """Return (planner, key, observed) for each missing Planner advisor lane."""
    task = data.get("agent", {}).get(PLANNER, {}).get("permission", {}).get("task", {})
    gaps = []
    if task.get("*") != "deny":
        gaps.append((PLANNER, "*", task.get("*")))
    gaps.extend((PLANNER, name, task.get(name)) for name in ADVISORS if task.get(name) != ALLOW)
    return gaps


def advisor_dispatcher_line(text):
    return next((line.strip() for line in text.splitlines() if "const advisorDispatchers=" in line), "")


def stale_pm_advisor_prose(text):
    """Return every stale PM-advisor ownership phrase still present."""
    stale = []
    for needle in (
        "The PM dispatches the registered `advisor-*-post`",
        "the PM owns dispatch before committing",
        "the Planner section below is source-only",
        "the PM arranges the required independent post-code advice",
        "Until the planned Planner integration is active",
    ):
        if needle in text:
            stale.append(needle)
    return stale


class RealConfig(unittest.TestCase):
    def setUp(self):
        self.data = load(CONFIG_PATH)

    def test_no_pm_can_dispatch_an_advisor(self):
        self.assertEqual(pm_advisor_grants(self.data), [])

    def test_pm_writer_planner_explore_and_verifier_lanes_survive(self):
        self.assertEqual(missing_kept_lanes(self.data), [])

    def test_planner_keeps_every_advisor_lane_under_a_deny_wildcard(self):
        self.assertEqual(planner_advisor_gaps(self.data), [])


class RealProseAndVerifier(unittest.TestCase):
    def test_workflow_names_the_planner_as_the_advisor_dispatcher(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertEqual(stale_pm_advisor_prose(text), [])
        self.assertIn("The Planner dispatches the registered `advisor-*-post` subagents", text)
        self.assertIn("the PMs hold no advisor task grant and never dispatch advisors directly", text)
        self.assertIn("The Planner dispatches and records advisor findings mechanically", text)

    def test_handoff_spec_names_the_planner_for_post_code_advice(self):
        text = HANDOFF.read_text(encoding="utf-8")
        self.assertIn("post-code advisory review from the Planner before the work-unit commit", text)
        self.assertNotIn("post-code advisory review from the PM before the work-unit commit", text)

    def test_verifier_advisor_dispatchers_are_orchestrator_and_planner_only(self):
        line = advisor_dispatcher_line(CHECKER.read_text(encoding="utf-8"))
        self.assertEqual(line, EXPECTED_DISPATCHER_LINE)
        self.assertNotIn("pm-odd", line)
        self.assertNotIn("pm-systematic", line)


class PositiveControl(unittest.TestCase):
    """Prove the validators can fail; a green run otherwise proves nothing."""

    @staticmethod
    def _synthetic():
        return {"agent": {pm: {"permission": {"task": {"*": "deny", "planner": "allow"}}}
                          for pm in PM_NAMES}}

    def test_advisor_allow_is_reported_for_both_pms(self):
        for pm in PM_NAMES:
            data = self._synthetic()
            data["agent"][pm]["permission"]["task"]["advisor-design-pre"] = "allow"
            with self.subTest(pm=pm):
                self.assertEqual(pm_advisor_grants(data), [(pm, "advisor-design-pre", "allow")])

    def test_advisor_ask_is_reported_too(self):
        data = self._synthetic()
        data["agent"]["pm-odd"]["permission"]["task"]["advisor-spec-post"] = "ask"
        self.assertEqual(pm_advisor_grants(data), [("pm-odd", "advisor-spec-post", "ask")])

    def test_dropped_kept_lane_is_reported(self):
        data = self._synthetic()
        del data["agent"]["pm-systematic"]["permission"]["task"]["planner"]
        self.assertIn(("pm-systematic", "planner", None), missing_kept_lanes(data))

    def test_planner_missing_advisor_lane_is_reported(self):
        data = {"agent": {PLANNER: {"permission": {"task": {"*": "deny",
                **{name: "allow" for name in ADVISORS[:-1]}}}}}}
        self.assertEqual(planner_advisor_gaps(data), [(PLANNER, ADVISORS[-1], None)])

    def test_stale_prose_is_reported(self):
        self.assertEqual(stale_pm_advisor_prose("The Planner dispatches advisors."), [])
        self.assertEqual(
            stale_pm_advisor_prose("The PM dispatches the registered `advisor-*-post` seats."),
            ["The PM dispatches the registered `advisor-*-post`"],
        )

    def test_missing_verifier_line_is_reported(self):
        self.assertEqual(advisor_dispatcher_line("nothing here"), "")
        self.assertNotEqual(advisor_dispatcher_line("const advisorDispatchers=new Set([\"pm-odd\"]"),
                            EXPECTED_DISPATCHER_LINE)


if __name__ == "__main__":
    unittest.main()
