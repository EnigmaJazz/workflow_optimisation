"""Two-tier independent verifier: routine (Haiku) and high-risk (Sol).

``gentle-ai-verify-routine`` is a copy of ``gentle-ai-verify`` on a different model family
from the Planner, the writers and the orchestrator. The orchestrator and both PMs may
dispatch it; no leaf agent may. WORKFLOW.md states when each tier is used.
"""

import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG = json.loads((REPO / "global-config" / "opencode.json").read_text(encoding="utf-8"))
WORKFLOW = (REPO / "WORKFLOW.md").read_text(encoding="utf-8")
HELPERS = (REPO / "global-config" / "plugins" / "lib" / "routing-guard-helpers.ts").read_text(encoding="utf-8")
ROUTINE, HIGH = "gentle-ai-verify-routine", "gentle-ai-verify"
AGENTS = CONFIG["agent"]


class RoutineVerifier(unittest.TestCase):
    def test_seat_is_haiku_high_and_hidden(self):
        seat = AGENTS[ROUTINE]
        self.assertEqual((seat["model"], seat.get("variant")), ("opencode-go/claude-haiku-5-5", "high"))
        self.assertIs(seat["hidden"], True)
        self.assertEqual(seat["mode"], "subagent")

    def test_surface_is_identical_to_the_high_risk_verifier(self):
        for field in ("tools", "permission"):
            self.assertEqual(AGENTS[ROUTINE][field], AGENTS[HIGH][field], field)
        self.assertEqual(AGENTS[ROUTINE]["tools"]["sandbox_bash"], True)
        self.assertEqual(AGENTS[ROUTINE]["tools"]["sandbox_apply"], False)

    def test_prompt_matches_except_the_model_label(self):
        routine = AGENTS[ROUTINE]["prompt"].replace("claude-haiku-5-5", "gpt-6.1-sol")
        self.assertEqual(routine, AGENTS[HIGH]["prompt"])
        self.assertIn("claude-haiku-5-5", AGENTS[ROUTINE]["prompt"])

    def test_only_coordinators_may_dispatch_it(self):
        allowed = sorted(name for name, agent in AGENTS.items()
                         if isinstance(agent.get("permission"), dict)
                         and isinstance(agent["permission"].get("task"), dict)
                         and agent["permission"]["task"].get(ROUTINE) == "allow")
        self.assertEqual(allowed, ["gentle-orchestrator", "pm-odd", "pm-systematic"])

    def test_routine_tier_is_a_different_family_from_planner_and_writers(self):
        self.assertNotIn("claude", AGENTS["planner"]["model"])
        for writer in ("gentle-ai-worker", "odd-apply", "general", "gentle-orchestrator"):
            self.assertNotIn("claude", AGENTS[writer]["model"], writer)

    def test_guard_treats_it_as_a_read_only_specialist(self):
        self.assertRegex(HELPERS, r"gentle-ai-verify-routine")

    def test_workflow_states_when_each_tier_is_used(self):
        self.assertIn("`gentle-ai-verify-routine`", WORKFLOW)
        self.assertRegex(WORKFLOW, r"Risk line names a high-risk item[^\n]*`gentle-ai-verify`")
        self.assertRegex(WORKFLOW, r"`gentle-ai-verify-routine`[^\n]*(otherwise|default)")


if __name__ == "__main__":
    unittest.main()
