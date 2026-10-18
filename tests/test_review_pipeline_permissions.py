import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "global-config/opencode.json"
VERIFIER_PATH = ROOT / "verify-workflow.sh"
ALLOWED_AGENTS = {"gentle-orchestrator", "pm-odd", "pm-systematic"}
PIPELINE_RUN = "host_review_pipeline_run"
PERSIST = "host_review_persist"


def permission_failures(agents):
    failures = []
    for name in ALLOWED_AGENTS:
        permission = agents.get(name, {}).get("permission", {})
        if permission.get(PIPELINE_RUN) != "allow":
            failures.append(f"{name}.{PIPELINE_RUN}")
        if permission.get(PERSIST) != "ask":
            failures.append(f"{name}.{PERSIST}")
    for name, agent in agents.items():
        if name in ALLOWED_AGENTS:
            continue
        permission = agent.get("permission", {})
        for tool in (PIPELINE_RUN, PERSIST):
            if tool in permission:
                failures.append(f"{name}.{tool}")
    return failures


class ReviewPipelinePermissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.agents = cls.config["agent"]
        cls.verifier = VERIFIER_PATH.read_text(encoding="utf-8")

    def test_three_agents_receive_exact_permissions_and_pm_tool_maps(self):
        self.assertEqual(self.config["permission"][PIPELINE_RUN], "deny")
        self.assertEqual(self.config["permission"][PERSIST], "deny")
        for name in ALLOWED_AGENTS:
            self.assertEqual(self.agents[name]["permission"][PIPELINE_RUN], "allow")
            self.assertEqual(self.agents[name]["permission"][PERSIST], "ask")
        for name in {"pm-odd", "pm-systematic"}:
            self.assertIs(self.agents[name]["tools"][PIPELINE_RUN], True)
            self.assertIs(self.agents[name]["tools"][PERSIST], True)
        self.assertEqual(permission_failures(self.agents), [])

    def test_missing_pipeline_grant_is_detected(self):
        agents = json.loads(json.dumps(self.agents))
        del agents["pm-odd"]["permission"][PIPELINE_RUN]
        self.assertIn(f"pm-odd.{PIPELINE_RUN}", permission_failures(agents))

    def test_wrong_persist_permission_is_detected(self):
        agents = json.loads(json.dumps(self.agents))
        agents["pm-systematic"]["permission"][PERSIST] = "allow"
        self.assertIn(f"pm-systematic.{PERSIST}", permission_failures(agents))

    def test_grant_to_another_agent_is_detected(self):
        agents = json.loads(json.dumps(self.agents))
        agents["general"]["permission"][PERSIST] = "ask"
        self.assertIn(f"general.{PERSIST}", permission_failures(agents))

    def test_verifier_gates_both_tools_and_exempts_only_allow_exceptions(self):
        gated = self.verifier.split("const gatedHostMutations=[", 1)[1].split("]", 1)[0]
        self.assertIn(f'"{PIPELINE_RUN}"', gated)
        self.assertIn(f'"{PERSIST}"', gated)
        self.assertIn('name!=="host_review_start"', self.verifier)
        self.assertIn('name!=="host_review_materialize"', self.verifier)
        self.assertIn(f'name!=="{PIPELINE_RUN}"', self.verifier)
        self.assertIn("hostReviewPipelineRunExceptionFailures", self.verifier)
        self.assertIn("hostReviewPersistFailures", self.verifier)
        self.assertIn("hostReviewNewGrantSweepFailures", self.verifier)

    def test_extracted_verifier_functions_pass_and_detect_reverted_controls(self):
        names = (
            "hostReviewPipelineRunFailures",
            "hostReviewPersistFailures",
            "hostReviewNewGlobalDefaultFailures",
            "hostReviewNewToolFailures",
            "hostReviewPipelineRunExceptionFailures",
            "hostReviewNewGrantSweepFailures",
        )
        extracted = []
        for name in names:
            start = self.verifier.index(f"function {name}(")
            brace = self.verifier.index("{", start)
            depth = 0
            for index in range(brace, len(self.verifier)):
                if self.verifier[index] == "{":
                    depth += 1
                elif self.verifier[index] == "}":
                    depth -= 1
                    if depth == 0:
                        extracted.append(self.verifier[start : index + 1])
                        break
            else:
                self.fail(f"unterminated verifier function: {name}")
        gated_source = self.verifier.split("const gatedHostMutations=[", 1)[1].split("]", 1)[0]
        gated = re.findall(r'"([^"]+)"', gated_source)
        script = "\n".join(extracted) + "\n" + f"""
const agents={json.dumps(self.agents)};
const gated={json.dumps(gated)};
const cfgPerm=(agent,tool)=>agent?.permission?.[tool];
const show=(value)=>JSON.stringify(value);
const assert=(condition,message)=>{{if(!condition)throw new Error(message)}};
for(const name of {json.dumps(sorted(ALLOWED_AGENTS))}){{
  assert(hostReviewPipelineRunFailures(name,agents[name]).length===0,`pipeline grant rejected: ${{name}}`);
  assert(hostReviewPersistFailures(name,agents[name]).length===0,`persist grant rejected: ${{name}}`);
}}
for(const name of ["pm-odd","pm-systematic"]) assert(hostReviewNewToolFailures(name,agents[name]).length===0,`tool map rejected: ${{name}}`);
assert(hostReviewPipelineRunExceptionFailures(gated,agents["gentle-orchestrator"]).length===0,"orchestrator exception rejected");
assert(hostReviewNewGrantSweepFailures(agents).length===0,"negative sweep rejected configured agents");
assert(hostReviewNewGlobalDefaultFailures("host_review_pipeline_run","deny").length===0,"pipeline default rejected");
assert(hostReviewNewGlobalDefaultFailures("host_review_persist","deny").length===0,"persist default rejected");
assert(hostReviewNewGlobalDefaultFailures("host_review_pipeline_run","allow").length===1,"pipeline default control is vacuous");
assert(hostReviewNewGlobalDefaultFailures("host_review_persist","ask").length===1,"persist default control is vacuous");
assert(hostReviewPipelineRunFailures("omitted",{{permission:{{}}}}).length===1,"pipeline omission control is vacuous");
assert(hostReviewPipelineRunFailures("wrong",{{permission:{{host_review_pipeline_run:"ask"}}}}).length===1,"pipeline value control is vacuous");
assert(hostReviewPersistFailures("omitted",{{permission:{{}}}}).length===1,"persist omission control is vacuous");
assert(hostReviewPersistFailures("wrong",{{permission:{{host_review_persist:"allow"}}}}).length===1,"persist value control is vacuous");
assert(hostReviewNewToolFailures("omitted",{{tools:{{}}}}).length===2,"tool omission control is vacuous");
for(const tool of ["host_review_pipeline_run","host_review_persist"]) assert(hostReviewNewToolFailures("disabled",{{tools:{{[tool]:false}}}}).some(failure=>failure.endsWith(tool)),`tool value control is vacuous: ${{tool}}`);
assert(hostReviewPipelineRunExceptionFailures(gated.filter(name=>name!=="host_review_pipeline_run"),{{permission:{{host_review_pipeline_run:"allow"}}}}).length===1,"exception omission control is vacuous");
assert(hostReviewPipelineRunExceptionFailures(gated,{{permission:{{host_review_pipeline_run:"ask"}}}}).length===1,"exception value control is vacuous");
for(const tool of ["host_review_pipeline_run","host_review_persist"]) assert(hostReviewNewGrantSweepFailures({{"synthetic-fourth-agent":{{permission:{{[tool]:"allow"}}}}}}).length===1,`sweep control is vacuous: ${{tool}}`);
console.log("extracted verifier assertions and positive controls passed");
"""
        try:
            result = subprocess.run(["bun", "-e", script], cwd=ROOT, capture_output=True, text=True, check=False)
        except PermissionError:
            self.skipTest("sandbox policy denies child Bun processes; run the extracted verifier harness directly")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("extracted verifier assertions and positive controls passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
