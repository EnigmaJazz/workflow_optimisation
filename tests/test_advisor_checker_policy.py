import copy
import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "verify/checkers/check-runtime-agents.cjs"
AGENTS = ROOT / "global-config/opencode.json"
FALLBACK = ROOT / "global-config/rate-limit-fallback.json"


def extract_function(source, signature):
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"Unclosed function: {signature}")


class AdvisorCheckerPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        runtime = shutil.which("node") or shutil.which("bun")
        if runtime is None:
            raise unittest.SkipTest("no JavaScript runtime found (node or bun)")

        source = CHECKER.read_text(encoding="utf-8")
        start_marker = "// advisor-model-policy:begin"
        end_marker = "// advisor-model-policy:end"
        start = source.index(start_marker) + len(start_marker)
        end = source.index(end_marker, start)
        policy = source[start:end]
        wildcard = extract_function(source, "function wildcardMatch(")
        cls.program = (
            "let advisorFallbackConfig\n"
            + wildcard
            + policy
            + "\nconst input=JSON.parse(require('fs').readFileSync(0,'utf8'));"
            + "process.stdout.write(JSON.stringify(advisorModelPolicyFailures(input.agents,input.fallback)))"
        )
        cls.runtime = runtime
        cls.agents = json.loads(AGENTS.read_text(encoding="utf-8"))["agent"]
        cls.fallback = json.loads(FALLBACK.read_text(encoding="utf-8"))

    def policy_failures(self, agents):
        try:
            result = subprocess.run(
                [self.runtime, "-e", self.program],
                input=json.dumps({"agents": agents, "fallback": self.fallback}),
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

    def test_explicit_memory_tool_enablement_is_rejected(self):
        agents = copy.deepcopy(self.agents)
        agents["advisor-design-pre"]["tools"]["ctx_memory"] = True
        self.assertIn(
            "ADVISOR_TOOLLESS_MEMORY_NOT_DENIED: advisor-design-pre",
            self.policy_failures(agents),
        )

    def test_memory_permission_allow_is_rejected_for_evidence_agent(self):
        agents = copy.deepcopy(self.agents)
        agents["advisor-evidence"].setdefault("permission", {})["ctx_memory"] = "allow"
        self.assertIn(
            "ADVISOR_EVIDENCE_MEMORY_NOT_DENIED",
            self.policy_failures(agents),
        )

    def test_non_user_ask_for_evidence_is_rejected(self):
        agents = copy.deepcopy(self.agents)
        agents["gentle-orchestrator"].setdefault("permission", {}).setdefault("task", {})[
            "advisor-evidence"
        ] = "ask"
        self.assertIn(
            "ADVISOR_EVIDENCE_DISPATCH_NOT_DENIED: gentle-orchestrator=\"ask\"",
            self.policy_failures(agents),
        )

    def test_inherited_wildcard_ask_for_evidence_is_rejected(self):
        agents = copy.deepcopy(self.agents)
        agents["synthetic-wildcard-ask"] = {"permission": {"task": {"*": "ask"}}}
        self.assertIn(
            "ADVISOR_EVIDENCE_DISPATCH_NOT_DENIED: synthetic-wildcard-ask=\"ask\"",
            self.policy_failures(agents),
        )

    def test_explicit_true_overrides_wildcard_memory_deny(self):
        agents = copy.deepcopy(self.agents)
        agents["advisor-design-pre"]["tools"]["*"] = False
        agents["advisor-design-pre"]["tools"]["ctx_memory"] = True
        self.assertIn(
            "ADVISOR_TOOLLESS_MEMORY_NOT_DENIED: advisor-design-pre",
            self.policy_failures(agents),
        )


if __name__ == "__main__":
    unittest.main()
