"""Specification advisors, the planner's own explore, and the Argon pre-code seats (owner decision 2026-10-31).

The planner calls `advisor-spec-pre` before Gate 1 and `advisor-spec-post` before Gate 2 on every code unit. They run on the
Sol model with their own luna evidence agent, so Sol advises the plan instead of writing it. `advisor-design-pre` and
`advisor-security-pre` move to Gemini 4 Argon with the existing Gemini 3.8 Flash evidence agent, so no two advisor seats of one
lens share a model before and after.

Run: python3 -m unittest tests/test_spec_advisor_seats.py -v
"""
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG = json.loads((REPO / "global-config" / "opencode.json").read_text(encoding="utf-8"))
FALLBACK = json.loads((REPO / "global-config" / "rate-limit-fallback.json").read_text(encoding="utf-8"))
AGENTS = CONFIG["agent"]

SOL, LUNA, ARGON = "openai/gpt-6.1-sol", "openai/gpt-6-luna", "google/gemini-4-argon"
MUTATION = ("edit", "write", "bash", "sandbox_apply", "sandbox_copy_in", "sandbox_copy_out", "sandbox_discard", "sandbox_finish",
            "host_plan_write", "host_gate_verdict", "host_task_mark", "ctx_memory")


def allowed_mutations(name):
    permission = AGENTS[name].get("permission", {})
    return [tool for tool in MUTATION if permission.get(tool) not in (None, "deny")]


class SpecAdvisors(unittest.TestCase):
    def test_pre_and_post_run_on_sol_high_with_their_own_evidence_agent(self):
        for name in ("advisor-spec-pre", "advisor-spec-post"):
            with self.subTest(name=name):
                seat = AGENTS[name]
                self.assertEqual((seat["model"], seat["variant"], seat["mode"], seat["hidden"]), (SOL, "high", "subagent", True))
                self.assertEqual(seat["permission"]["task"], {"*": "deny", "advisor-spec-evidence": "allow"})
                self.assertIs(seat["tools"]["task"], True)
                self.assertEqual(allowed_mutations(name), [])

    def test_evidence_agent_is_luna_read_only_and_cannot_delegate(self):
        seat = AGENTS["advisor-spec-evidence"]
        self.assertEqual((seat["model"], seat["variant"], seat["mode"], seat["hidden"]), (LUNA, "medium", "subagent", True))
        self.assertEqual(seat["permission"]["task"], {"*": "deny"})
        self.assertIs(seat["tools"]["task"], False)
        self.assertEqual(allowed_mutations("advisor-spec-evidence"), [])

    def test_prompts_state_the_specification_and_edge_case_role(self):
        for name, timing in (("advisor-spec-pre", "before implementation"), ("advisor-spec-post", "after implementation")):
            prompt = AGENTS[name]["prompt"]
            self.assertIn("specification", prompt)
            self.assertIn("edge case", prompt)
            self.assertIn(timing, prompt)
            self.assertIn("advisor-spec-evidence", prompt)
            self.assertIn("Advice is evidence, never approval", prompt)

    def test_a_spec_advisor_is_never_substituted_when_unavailable(self):
        self.assertIn("advisor-spec-pre", FALLBACK["noFallbackAgents"])
        self.assertIn("advisor-spec-post", FALLBACK["noFallbackAgents"])
        self.assertIn("advisor-spec-evidence", FALLBACK["noFallbackAgents"])

    def test_positive_control_a_mutating_grant_is_detected(self):
        AGENTS["advisor-spec-pre"]["permission"]["bash"] = "allow"
        try:
            self.assertEqual(allowed_mutations("advisor-spec-pre"), ["bash"])
        finally:
            AGENTS["advisor-spec-pre"]["permission"]["bash"] = "deny"


class PlannerWiring(unittest.TestCase):
    def test_planner_dispatches_the_spec_advisors_and_its_own_explore(self):
        task = AGENTS["planner"]["permission"]["task"]
        for name in ("advisor-spec-pre", "advisor-spec-post", "planner-explore", "planner-evidence"):
            self.assertEqual(task.get(name), "allow", name)
        self.assertNotIn("explore", task)

    def test_planner_prompt_makes_both_spec_advisors_compulsory(self):
        prompt = AGENTS["planner"]["prompt"]
        self.assertIn("`advisor-spec-pre` is compulsory", prompt)
        self.assertIn("before Gate 1", prompt)
        self.assertIn("`advisor-spec-post` is compulsory", prompt)
        self.assertIn("before Gate 2", prompt)
        self.assertIn("`planner-explore`", prompt)

    def test_planner_explore_is_read_only_and_cannot_delegate(self):
        seat = AGENTS["planner-explore"]
        self.assertEqual((seat["mode"], seat["hidden"]), ("subagent", True))
        self.assertEqual(seat["permission"]["task"]["*"], "deny")
        self.assertEqual(allowed_mutations("planner-explore"), [])


class ArgonPreSeats(unittest.TestCase):
    def test_design_and_security_pre_run_on_argon_with_the_gemini_evidence_agent(self):
        for name in ("advisor-design-pre", "advisor-security-pre"):
            with self.subTest(name=name):
                seat = AGENTS[name]
                self.assertEqual(seat["model"], ARGON)
                self.assertNotIn("variant", seat)
                self.assertEqual(seat["permission"]["task"], {"*": "deny", "advisor-gemini-evidence": "allow"})
                self.assertIs(seat["tools"]["task"], True)
                self.assertEqual(allowed_mutations(name), [])
                for tool in ("read", "sandbox_bash", "sandbox_read", "sandbox_grep"):
                    self.assertEqual(seat["permission"].get(tool), "deny", (name, tool))
                self.assertIn("advisor-gemini-evidence", seat["prompt"])
                self.assertIn("at most 2", seat["prompt"])

    def test_scope_lines_survive_the_move(self):
        self.assertIn("Design scope", AGENTS["advisor-design-pre"]["prompt"])
        self.assertIn("Security scope", AGENTS["advisor-security-pre"]["prompt"])

    def test_post_seats_stay_where_they_were_so_pre_and_post_differ(self):
        self.assertEqual(AGENTS["advisor-design-post"]["model"], "opencode-go/qwen3.7-plus")
        self.assertEqual(AGENTS["advisor-security-post"]["model"], "opencode-go/qwen3.7-plus")
        for lens in ("design", "security"):
            self.assertNotEqual(AGENTS[f"advisor-{lens}-pre"]["model"], AGENTS[f"advisor-{lens}-post"]["model"])

    def test_the_spec_advisor_and_the_argon_seats_are_different_families(self):
        self.assertNotEqual(AGENTS["advisor-spec-pre"]["model"].split("/")[0], AGENTS["advisor-design-pre"]["model"].split("/")[0])

    def test_the_unused_external_pair_is_untouched(self):
        for name in ("advisor-gemini-pre", "advisor-gemini-post"):
            self.assertEqual(AGENTS[name]["model"], ARGON)
            self.assertEqual(AGENTS[name]["permission"]["task"], {"*": "deny", "advisor-gemini-evidence": "allow"})


class SeatTrial(unittest.TestCase):
    """Owner decision 2026-10-31: Claude Agent seats, luna routine verifier, DeepSeek PMs (usage trial; revert on overspend)."""

    def seat(self, name):
        return AGENTS[name]["model"], AGENTS[name].get("variant")

    def test_claude_agent_seats_use_the_cli_aliases_with_effort_as_variant(self):
        self.assertEqual(self.seat("gentle-orchestrator"), ("claude-agent/sonnet", "medium"))
        self.assertEqual(self.seat("planner"), ("claude-agent/opus", "high"))
        self.assertEqual(self.seat("planner-explore"), ("claude-agent/haiku", "low"))

    def test_routine_verifier_is_luna_and_says_so(self):
        seat = AGENTS["gentle-ai-verify-routine"]
        self.assertEqual((seat["model"], seat.get("variant")), (LUNA, "high"))
        self.assertNotIn("haiku", seat["prompt"] + seat["description"])
        self.assertIn("gpt-6-luna", seat["prompt"])

    def test_pms_are_deepseek_without_a_variant(self):
        for name in ("pm-odd", "pm-systematic"):
            self.assertEqual(self.seat(name), ("opencode-go/deepseek-v4.1-flash", None), name)

    def test_claude_agent_models_have_a_fallback_chain_that_leaves_the_claude_plan(self):
        for model in ("claude-agent/sonnet", "claude-agent/opus", "claude-agent/haiku"):
            chain = FALLBACK["fallbackModels"].get(model)
            self.assertTrue(chain, model)
            self.assertNotIn("claude-agent", [entry["providerID"] for entry in chain], model)

    def test_no_other_seat_uses_the_claude_agent_provider(self):
        users = sorted(n for n, a in AGENTS.items() if str(a.get("model", "")).startswith("claude-agent/"))
        self.assertEqual(users, ["gentle-orchestrator", "planner", "planner-explore"])


if __name__ == "__main__":
    unittest.main()
