"""Regression tests for the runtime Grok refuter-seat policy."""
import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHECKER = REPO / "verify" / "checkers" / "check-runtime-agents.cjs"
CONFIG = REPO / "global-config" / "opencode.json"
DERIVE = REPO / "scripts" / "derive-v2-config.py"
SANDBOX = Path.home() / "agent-sandbox-integration"
ALLOWED = {"review-refuter", "asi-review-refuter"}


class GrokSeatPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        runtime = shutil.which("node") or shutil.which("bun")
        if runtime is None:
            raise unittest.SkipTest("no JavaScript runtime found (node or bun)")
        source = CHECKER.read_text(encoding="utf-8")
        start_marker = "// grok-seat-policy:begin"
        end_marker = "// grok-seat-policy:end"
        try:
            start = source.index(start_marker) + len(start_marker)
            end = source.index(end_marker, start)
        except ValueError as error:
            raise AssertionError(f"Grok seat policy marker block is missing: {error}") from error
        cls.program = (
            "const hasOwn=(obj,key)=>Object.prototype.hasOwnProperty.call(obj??{},key);"
            + source[start:end]
            + "\nconst input=JSON.parse(require('fs').readFileSync(0,'utf8'));"
            + "const result=grokSeatFailures(input.agents);"
            + "if (typeof grokReachableSeatFailures === 'function') result.push(...grokReachableSeatFailures(input.systematic,input.inventory,input.fallback,input.sourceModels));"
            + "process.stdout.write(JSON.stringify(result))"
        )
        cls.runtime = runtime
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.agents = cls.config["agent"]

    def reachable_failures(self, systematic=None, inventory=None, fallback=None, source_models=None):
        data = {"agents": {}, "systematic": systematic or {}, "inventory": inventory or [],
                "fallback": fallback or {}, "sourceModels": source_models or {}}
        result = subprocess.run([self.runtime, "-e", self.program], input=json.dumps(data),
                               capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_systematic_base_and_profile_grok_seats_are_rejected(self):
        agent = {"name": "repo-research-analyst", "category": ""}
        base = {"agents": {"repo-research-analyst": {"model": "opencode-go/grok-4.7"}}}
        profile = {"profiles": {"review": {"agents": {"repo-research-analyst": {"model": "opencode-go/grok-4.7"}}}}}
        self.assertEqual(self.reachable_failures(base, [agent]),
                         ["GROK_REACHABLE_SEAT: repo-research-analyst=opencode-go/grok-4.7 (systematic:base)"])
        self.assertEqual(self.reachable_failures(profile, [agent]),
                         ["GROK_REACHABLE_SEAT: repo-research-analyst=opencode-go/grok-4.7 (systematic:review)"])

    def test_fallback_grok_seats_and_refuter_exception(self):
        inventory = [{"name": "gentle-ai-verify", "category": ""},
                     {"name": "ordinary-agent", "category": ""},
                     {"name": "review-refuter", "category": ""}]
        source = {"gentle-ai-verify": "openai/gpt-6.1-sol", "ordinary-agent": "openai/gpt-6.1-sol",
                  "review-refuter": "openai/gpt-6.1-sol"}
        target = "opencode-go/grok-4.7"
        self.assertEqual(self.reachable_failures({}, inventory, {"enabled": True, "startProviders": ["openai"],
                            "agentFallbackModels": {"gentle-ai-verify": target}}, source),
                         [f"GROK_REACHABLE_SEAT: gentle-ai-verify={target} (fallback)"])
        self.assertEqual(self.reachable_failures({}, inventory, {"enabled": True, "startProviders": ["openai"],
                            "fallbackModel": target}, source),
                         [f"GROK_REACHABLE_SEAT: gentle-ai-verify={target} (fallback)",
                          f"GROK_REACHABLE_SEAT: ordinary-agent={target} (fallback)"])
        self.assertEqual(self.reachable_failures({}, [inventory[2]], {"enabled": True, "startProviders": ["openai"],
                            "agentFallbackModels": {"review-refuter": target}}, source), [])

    def test_unreachable_fallback_grok_is_not_rejected(self):
        target = "opencode-go/grok-4.7"
        self.assertEqual(self.reachable_failures({}, [{"name": "ordinary-agent", "category": ""}],
                            {"enabled": True, "startProviders": ["anthropic"], "fallbackModel": target},
                            {"ordinary-agent": "openai/gpt-6.1-sol"}), [])

    def test_deployed_agent_outside_inventory_grok_fallback_is_rejected(self):
        target = "opencode-go/grok-4.7"
        self.assertEqual(self.reachable_failures({}, [],
                            {"enabled": True, "startProviders": ["opencode-go"], "sameProviderFallbackMode": "always",
                             "agentFallbackModels": {"pm-odd": target}},
                            {"pm-odd": "opencode-go/muse-spark-1.3-contributor"}),
                         [f"GROK_REACHABLE_SEAT: pm-odd={target} (fallback)"] )

    def policy_failures(self, agents):
        try:
            result = subprocess.run(
                [self.runtime, "-e", self.program],
                input=json.dumps({"agents": agents}),
                capture_output=True,
                text=True,
                check=False,
            )
        except (PermissionError, OSError) as error:
            self.skipTest(f"JavaScript runtime could not execute: {error}")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_real_v1_config_has_no_policy_failures(self):
        self.assertEqual(self.policy_failures(self.agents), [])

    def test_real_v1_has_exactly_the_two_documented_grok_agents(self):
        grok_agents = {
            name for name, agent in self.agents.items()
            if isinstance(agent, dict) and isinstance(agent.get("model"), str) and "grok" in agent["model"].lower()
        }
        self.assertEqual(len(grok_agents), 2)
        self.assertEqual(grok_agents, ALLOWED)

    def test_unapproved_verifier_grok_model_is_rejected(self):
        self.assertEqual(
            self.policy_failures({"gentle-ai-verify": {"model": "opencode-go/grok-4.7"}}),
            ["GROK_OUTSIDE_REFUTER: gentle-ai-verify=opencode-go/grok-4.7"],
        )

    def test_astra_verifier_grok_model_is_rejected(self):
        agents = copy.deepcopy(self.agents)
        agents.setdefault("gentle-ai-verify-astra", {})["model"] = "opencode-go/grok-4.7"
        failures = self.policy_failures(agents)
        self.assertTrue(any(item.startswith("GROK_OUTSIDE_REFUTER: gentle-ai-verify-astra=") for item in failures), failures)

    def test_review_refuter_grok_is_allowed(self):
        self.assertEqual(self.policy_failures({"review-refuter": {"model": "opencode-go/grok-4.7"}}), [])

    def test_asi_review_refuter_grok_is_allowed(self):
        self.assertEqual(self.policy_failures({"asi-review-refuter": {"model": "opencode-go/grok-4.7"}}), [])

    def test_provider_catalog_entry_is_not_scanned_as_an_agent(self):
        config = {"agent": {"ordinary-agent": {"model": "openai/gpt-6.1-sol"}},
                  "provider": {"opencode-go": {"models": {"grok-4.7": {"name": "Grok 4.7"}}}}}
        self.assertEqual(self.policy_failures(config["agent"]), [])

    @unittest.skipUnless(SANDBOX.exists(), "needs the agent-sandbox-integration checkout for V2 derivation")
    def test_derived_v2_config_has_no_grok_seat_failures(self):
        with tempfile.TemporaryDirectory() as output:
            result = subprocess.run(
                ["python3", str(DERIVE), "--source", str(REPO / "global-config"),
                 "--sandbox-repo", str(SANDBOX), "--out", output],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                self.skipTest(f"V2 derive unavailable in this environment: {result.stderr.strip()}")
            derived = json.loads((Path(output) / "opencode.json").read_text(encoding="utf-8"))
            self.assertEqual(self.policy_failures(derived["agent"]), [])


if __name__ == "__main__":
    unittest.main()
