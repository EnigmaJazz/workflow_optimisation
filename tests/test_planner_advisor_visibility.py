import copy
import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "verify/checkers/check-runtime-agents.cjs"
CONFIG = ROOT / "global-config/opencode.json"


class PlannerAdvisorVisibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = shutil.which("node") or shutil.which("bun")
        if cls.runtime is None:
            raise unittest.SkipTest("no JavaScript runtime found (node or bun)")

        source = CHECKER.read_text(encoding="utf-8")
        start_marker = "// planner-advisor-visibility:begin"
        end_marker = "// planner-advisor-visibility:end"
        if start_marker not in source or end_marker not in source:
            raise AssertionError("planner-advisor-visibility policy block is missing")
        start = source.index(start_marker) + len(start_marker)
        end = source.index(end_marker, start)
        policy = source[start:end]
        cls.program = (
            policy
            + "\nconst input=JSON.parse(require('fs').readFileSync(0,'utf8'));"
            + "process.stdout.write(JSON.stringify(plannerAdvisorVisibilityFailures(input)))"
        )
        cls.agents = json.loads(CONFIG.read_text(encoding="utf-8"))["agent"]

    def policy_failures(self, agents):
        try:
            result = subprocess.run(
                [self.runtime, "-e", self.program],
                input=json.dumps(agents),
                capture_output=True,
                text=True,
                check=False,
            )
        except (PermissionError, OSError) as error:
            self.skipTest(f"JavaScript runtime could not execute: {error}")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_checked_in_config_has_no_policy_failures(self):
        self.assertEqual(self.policy_failures(self.agents), [])

    def test_hidden_unnamed_allowed_target_is_unreachable(self):
        agents = copy.deepcopy(self.agents)
        agents["advisor-testing-post"]["hidden"] = True
        agents["planner"]["prompt"] = agents["planner"]["prompt"].replace(
            "`advisor-testing-post`", ""
        )
        self.assertIn(
            "PLANNER_ADVISOR_UNREACHABLE: advisor-testing-post",
            self.policy_failures(agents),
        )

    def test_hidden_target_is_accepted_when_named_in_prompt(self):
        agents = copy.deepcopy(self.agents)
        agents["advisor-testing-post"]["hidden"] = True
        agents["planner"]["prompt"] += " `advisor-testing-post`"
        self.assertNotIn(
            "PLANNER_ADVISOR_UNREACHABLE: advisor-testing-post",
            self.policy_failures(agents),
        )

    def test_visible_target_is_accepted_without_prompt_name(self):
        agents = copy.deepcopy(self.agents)
        agents["advisor-testing-post"]["hidden"] = False
        agents["planner"]["prompt"] = agents["planner"]["prompt"].replace(
            "`advisor-testing-post`", ""
        )
        self.assertNotIn(
            "PLANNER_ADVISOR_UNREACHABLE: advisor-testing-post",
            self.policy_failures(agents),
        )

    def test_prompt_name_does_not_hide_missing_agent_entry(self):
        agents = copy.deepcopy(self.agents)
        name = "advisor-missing-test-target"
        agents["planner"]["permission"]["task"][name] = "allow"
        agents["planner"]["prompt"] += f" `{name}`"
        self.assertIn(
            f"PLANNER_ADVISOR_MISSING: {name}",
            self.policy_failures(agents),
        )

    def test_every_planner_task_target_exists_in_config(self):
        task_targets = self.agents["planner"]["permission"]["task"]
        self.assertTrue(all(name == "*" or name in self.agents for name in task_targets))


if __name__ == "__main__":
    unittest.main()
