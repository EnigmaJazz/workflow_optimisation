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
    def test_pre_and_post_run_on_argon_with_the_gemini_evidence_agent(self):
        # Owner decision 2026-11-01: the planner stays on Sol, so its spec checkers run on a different family.
        for name in ("advisor-spec-pre", "advisor-spec-post"):
            with self.subTest(name=name):
                seat = AGENTS[name]
                self.assertEqual((seat["model"], seat.get("variant"), seat["mode"], seat["hidden"]), (ARGON, None, "subagent", True))
                self.assertEqual(seat["permission"]["task"], {"*": "deny", "advisor-gemini-evidence": "allow"})
                self.assertIs(seat["tools"]["task"], True)
                self.assertEqual(allowed_mutations(name), [])
                for tool in ("read", "sandbox_bash", "sandbox_read", "sandbox_grep"):
                    self.assertEqual(seat["permission"].get(tool), "deny", (name, tool))

    def test_the_old_sol_evidence_agent_is_gone(self):
        self.assertNotIn("advisor-spec-evidence", AGENTS)

    def test_prompts_state_the_specification_and_edge_case_role(self):
        for name, timing in (("advisor-spec-pre", "before implementation"), ("advisor-spec-post", "after implementation")):
            prompt = AGENTS[name]["prompt"]
            self.assertIn("specification", prompt)
            self.assertIn("edge case", prompt)
            self.assertIn(timing, prompt)
            self.assertIn("advisor-gemini-evidence", prompt)
            self.assertIn("at most 2", prompt)
            self.assertIn("Advice is evidence, never approval", prompt)

    def test_a_spec_advisor_is_never_substituted_when_unavailable(self):
        self.assertIn("advisor-spec-pre", FALLBACK["noFallbackAgents"])
        self.assertIn("advisor-spec-post", FALLBACK["noFallbackAgents"])

    def test_high_risk_verifier_stays_on_sol_and_off_grok(self):
        # Grok on the verifier used 10% of the weekly allowance in one run (2026-11-01).
        self.assertEqual(AGENTS["gentle-ai-verify"]["model"], "openai/gpt-6.1-sol")
        grok = sorted(n for n, a in AGENTS.items() if "grok" in str(a.get("model", "")))
        self.assertEqual(grok, ["asi-review-refuter", "review-refuter"])

    def test_positive_control_a_mutating_grant_is_detected(self):
        AGENTS["advisor-spec-pre"]["permission"]["bash"] = "allow"
        try:
            self.assertEqual(allowed_mutations("advisor-spec-pre"), ["bash"])
        finally:
            AGENTS["advisor-spec-pre"]["permission"]["bash"] = "deny"


class MemoryPolicy(unittest.TestCase):
    def test_new_agents_are_classified_memory_isolated_by_the_verifier(self):
        checker = (REPO / "verify" / "checkers" / "check-runtime-agents.cjs").read_text(encoding="utf-8")
        block = checker.split("const isolatedMemoryAgents=new Set([", 1)[1].split("])", 1)[0]
        for name in ("advisor-spec-pre", "advisor-spec-post"):
            self.assertIn(f'"{name}"', block, name)
            self.assertEqual(AGENTS[name]["permission"]["ctx_memory"], "deny", name)


class PlannerWiring(unittest.TestCase):
    def test_planner_dispatches_the_spec_advisors_and_the_shared_explore(self):
        task = AGENTS["planner"]["permission"]["task"]
        for name in ("advisor-spec-pre", "advisor-spec-post", "explore", "planner-evidence"):
            self.assertEqual(task.get(name), "allow", name)
        self.assertNotIn("planner-explore", task)

    def test_planner_prompt_makes_both_spec_advisors_compulsory(self):
        prompt = AGENTS["planner"]["prompt"]
        self.assertIn("`advisor-spec-pre` is compulsory", prompt)
        self.assertIn("before Gate 1", prompt)
        self.assertIn("`advisor-spec-post` is compulsory", prompt)
        self.assertIn("before Gate 2", prompt)
        self.assertIn("For your own broad reading use `explore`", prompt)

    def test_planner_prompt_names_the_api_credit_carrier_when_the_lane_is_inactive(self):
        # Q99: the compulsory spec advice keeps a carrier while the Antigravity lane is inactive.
        prompt = AGENTS["planner"]["prompt"]
        self.assertIn("When the Antigravity lane is inactive", prompt)
        self.assertIn("`advisor-gemini-pre` carries that same compulsory specification advice "
                      "in place of `advisor-spec-pre`", prompt)
        self.assertIn("`advisor-gemini-post` replaces `advisor-spec-post` at the post position", prompt)
        self.assertEqual(prompt.count("dispatch exactly one carrier per position, never both"), 1)
        self.assertEqual(prompt.count("When the Antigravity lane is inactive"), 1)
        self.assertEqual(prompt.count("Subscription Gemini advisors run only when the external lane is active"), 1)
        self.assertIn("The registered API-credit carriers `advisor-gemini-pre` and `advisor-gemini-post` "
                      "are exempt from that restriction", prompt)


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
        self.assertNotEqual(AGENTS["advisor-spec-pre"]["model"].split("/")[0], AGENTS["planner"]["model"].split("/")[0])

    def test_the_unused_external_pair_is_untouched(self):
        for name in ("advisor-gemini-pre", "advisor-gemini-post"):
            self.assertEqual(AGENTS[name]["model"], ARGON)
            self.assertEqual(AGENTS[name]["permission"]["task"], {"*": "deny", "advisor-gemini-evidence": "allow"})


class SeatsRevertedFromClaudeAgent(unittest.TestCase):
    """Owner decision 2026-11-01: the Q94 Claude Agent seat trial is reverted (usage cost); spec advisors and Argon seats stay."""

    def seat(self, name):
        return AGENTS[name]["model"], AGENTS[name].get("variant")

    def test_orchestrator_planner_and_pms_are_back_on_their_pre_trial_seats(self):
        self.assertEqual(self.seat("gentle-orchestrator"), ("opencode-go/deepseek-v4.1-flash", "default"))
        self.assertEqual(self.seat("planner"), ("openai/gpt-6.1-sol", "high"))
        for name in ("pm-odd", "pm-systematic"):
            self.assertEqual(self.seat(name), ("opencode-go/muse-spark-1.3-contributor", None), name)

    def test_routine_verifier_is_haiku_again(self):
        seat = AGENTS["gentle-ai-verify-routine"]
        self.assertEqual((seat["model"], seat.get("variant")), ("opencode-go/claude-haiku-5-5", "high"))
        self.assertIn("claude-haiku-5-5", seat["prompt"])
        self.assertNotIn("gpt-6-luna", seat["prompt"] + seat["description"])

    def test_no_seat_uses_the_claude_agent_provider_and_planner_explore_is_gone(self):
        users = [n for n, a in AGENTS.items() if str(a.get("model", "")).startswith("claude-agent/")]
        self.assertEqual(users, [])
        self.assertNotIn("planner-explore", AGENTS)

    def test_claude_agent_fallback_chains_are_removed(self):
        self.assertEqual([k for k in FALLBACK["fallbackModels"] if k.startswith("claude-agent/")], [])


if __name__ == "__main__":
    unittest.main()
