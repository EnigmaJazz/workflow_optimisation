import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "global-config/opencode.json"
VERIFIER_PATH = ROOT / "verify-workflow.sh"
HANDOFF_PATH = ROOT / "docs/specs/pm-handoff.md"
PM_TINY_FIX_INSTRUCTION = (
    "Tiny-fix option: mid-unit, for a genuinely tiny fix dispatch `odd-apply` or "
    "`gentle-ai-worker` (DeepSeek family), never `general`, and only within the "
    "brief's allowed paths."
)
PM_TINY_FIX_STALE_SENTENCE = (
    "Tiny-fix option: mid-unit, you may dispatch `general` for a genuinely tiny fix "
    "only within the brief's allowed paths."
)
ALLOWED_AGENTS = {"gentle-orchestrator", "pm-odd", "pm-systematic"}
PIPELINE_RUN = "host_review_pipeline_run"
PERSIST = "host_review_persist"
ASSESS = "host_review_assess"
DIFF_READ = "host_review_diff_read"
PM_REQUIRED_DISPATCH = {
    "pm-odd": [
        "odd-apply",
        "gentle-ai-worker",
        "gentle-ai-worker-local",
        "gentle-ai-verify",
        "gentle-ai-verify-routine",
        "gentle-ai-verify-astra",
        "explore",
        "planner",
    ],
    "pm-systematic": [
        "gentle-ai-worker",
        "gentle-ai-worker-local",
        "gentle-ai-verify",
        "gentle-ai-verify-routine",
        "gentle-ai-verify-astra",
        "explore",
        "planner",
    ],
}
LEAF_DISPATCH_AGENTS = [
    "odd-apply",
    "gentle-ai-worker",
    "gentle-ai-worker-local",
    "gentle-ai-verify",
    "gentle-ai-verify-routine",
    "explore",
]
HOST_TEST_RUN = "host_test_run"
HOST_PLAN_WRITE = "host_plan_write"
HOST_TOOL_PROMPT_FRAGMENTS = (
    "may draft plan documents through the ask-gated `host_plan_write` fixed tool",
    "plan documents only, never code or configuration",
    "narrowly defined, pre-registered tests through the allow-gated `host_test_run` fixed tool",
    "never arbitrary caller argv, pipes, redirects, or shell",
    "a failed or unavailable test run is evidence, never permission to widen authority",
    "`host_test_run` is not implemented in the current surface and remains inert until the host tool ships",
)
HOST_TOOL_FUNCTION_NAMES = (
    "hostTestRunGlobalDefaultFailures",
    "hostPlanWriteGlobalDefaultFailures",
    "hostTestRunOrchestratorFailures",
    "hostPlanWriteOrchestratorFailures",
    "hostTestRunGrantSweepFailures",
    "hostPlanWriteGrantSweepFailures",
    "hostToolPromptFailures",
)


def hardcoded_coordinator_triple_lines(text):
    """Line numbers carrying the retired hard-coded coordinator triple."""
    return [
        number
        for number, line in enumerate(text.splitlines(), 1)
        if '["gentle-orchestrator","pm-odd","pm-systematic"]' in line
    ]


def extract_declaration(text, name):
    """Return the production ``const <name>=...`` declaration line."""
    start = text.index(f"const {name}=")
    end = text.index("\n", start)
    return text[start:end]


def extract_braced_block(text, start_marker):
    """Return the brace-balanced block beginning at ``start_marker``."""
    start = text.index(start_marker)
    brace = text.index("{", start)
    depth = 0
    for index in range(brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise AssertionError(f"unterminated verifier block: {start_marker}")


# Executed against the extracted production predicate. Every control increments
# the group counter only after its assertion passes, so the printed marker proves
# each mutation ran and was detected. Runtime fixtures are test fixtures, never
# live-runtime evidence.
COVERAGE_CONTROLS_TEMPLATE = r"""
const coverageCounts={1:0,2:0,3:0,4:0,5:0};
const control=(group,check)=>{check();coverageCounts[group]+=1;};
const coveragePmAgents=__PM_AGENTS__;
const pmRequired=__PM_REQUIRED__;
const leafAgents=__LEAF_AGENTS__;
const handoff=__HANDOFF_TEXT__;
const identityNeedles=__IDENTITY_NEEDLES__;
const familyPairs=[["general","gentle-orchestrator"],["gentle-ai-worker","gentle-ai-verify"],["pm-odd","odd-apply"],["pm-systematic","gentle-ai-worker"]];
const familyModel=(family)=>family==="gpt"?"openai/gpt-6.1-sol":family==="deepseek"?"opencode-go/deepseek-v4.1-flash":family==="glm"?"opencode-go/glm-5.3-flash":"synthetic/no-family";
const independentRuntime={
  "general":{model:"openai/gpt-6-luna"},
  "gentle-orchestrator":{model:"opencode-go/deepseek-v4.1-flash"},
  "gentle-ai-worker":{model:"opencode-go/deepseek-v4.1-flash"},
  "gentle-ai-verify":{model:"openai/gpt-6-luna"},
  "pm-odd":{model:"opencode-go/glm-5.3-flash"},
  "odd-apply":{model:"opencode-go/deepseek-v4.1-flash"},
  "pm-systematic":{model:"opencode-go/glm-5.3-flash"},
};
function runPrimaryReviewFamilyLoop(deployedAgents,readDebug){
  const failures=[];
  const fail=(message)=>failures.push(message);
  __FAMILY_LOOP__
  return failures;
}

// Group 1: PM identity needles, route-first, prompt shape, tiny-fix instructions.
control(1,()=>{assert(pmIdentityFailures(agents,handoff).length===0,"real PM identity/handoff rejected");});
for(const pm of coveragePmAgents){
  for(const needle of identityNeedles){
    control(1,()=>{
      const mutated=cloneAgents();
      assert(mutated[pm].prompt.includes(needle),`needle absent before mutation: ${pm}: ${needle}`);
      mutated[pm].prompt=mutated[pm].prompt.split(needle).join("");
      assert(!mutated[pm].prompt.includes(needle),`needle removal ineffective: ${pm}: ${needle}`);
      const failures=pmIdentityFailures(mutated,handoff);
      const expected=`PM_IDENTITY_NEEDLE_MISSING: ${pm}: ${needle}`;
      assert(failures.length===1&&failures[0]===expected,`identity needle control not isolated: ${pm}: ${needle} => ${JSON.stringify(failures)}`);
    });
  }
  const route=pm==="pm-odd"?"workflow-odd-secure":"workflow-systematic";
  control(1,()=>{
    const mutated=cloneAgents();
    const clause=`Load \`${route}\` FIRST`;
    assert(mutated[pm].prompt.includes(clause),`route-first clause absent: ${pm}`);
    mutated[pm].prompt=mutated[pm].prompt.split(clause).join("route");
    const failures=pmIdentityFailures(mutated,handoff);
    const expected=`PM_ROUTE_SKILL_NOT_LOADED_FIRST: ${pm}`;
    assert(failures.length===1&&failures[0]===expected,`route-first control not isolated: ${pm} => ${JSON.stringify(failures)}`);
  });
  for(const [label,mutate] of [
    ["missing-agent",(m)=>{delete m[pm]}],
    ["missing-prompt",(m)=>{delete m[pm].prompt}],
    ["nonstring-prompt",(m)=>{m[pm].prompt=42}],
  ]){
    control(1,()=>{
      const mutated=cloneAgents();
      mutate(mutated);
      const failures=pmIdentityFailures(mutated,handoff);
      const expected=`PM_IDENTITY_PROMPT_MISSING: ${pm}`;
      assert(failures.length===1&&failures[0]===expected,`${label} control not isolated: ${pm} => ${JSON.stringify(failures)}`);
    });
  }
  control(1,()=>{
    const mutated=cloneAgents();
    assert(mutated[pm].prompt.includes(__PM_TINYFIX__),`tiny-fix instruction absent: ${pm}`);
    mutated[pm].prompt=mutated[pm].prompt.split(__PM_TINYFIX__).join("Tiny-fix option removed.");
    const failures=pmIdentityFailures(mutated,handoff);
    const expected=`PM_TINYFIX_WRITER_INSTRUCTION_MISSING: ${pm}`;
    assert(failures.length===1&&failures[0]===expected,`tiny-fix writer control not isolated: ${pm} => ${JSON.stringify(failures)}`);
  });
  control(1,()=>{
    const mutated=cloneAgents();
    assert(mutated[pm].prompt.includes(__PM_TINYFIX__),`tiny-fix instruction absent: ${pm}`);
    mutated[pm].prompt=mutated[pm].prompt.split(__PM_TINYFIX__).join(__PM_TINYFIX_STALE__);
    const failures=pmIdentityFailures(mutated,handoff);
    assert(failures.length===2&&failures.includes(`PM_TINYFIX_WRITER_INSTRUCTION_MISSING: ${pm}`)&&failures.includes(`PM_TINYFIX_STALE_GENERAL_INSTRUCTION: ${pm}`),`stale tiny-fix control not isolated: ${pm} => ${JSON.stringify(failures)}`);
  });
}
console.log(`coverage-group-1-identity: ${coverageCounts[1]} controls passed`);

// Group 2: handoff schemas/unreadable text and the orchestrator contract pointer.
for(const needle of ["pm-unit-brief/v1","pm-unit-result/v1"]){
  control(2,()=>{
    const mutated=handoff.split(needle).join("");
    const failures=pmIdentityFailures(agents,mutated);
    const expected=`PM_HANDOFF_SCHEMA_MISSING: ${needle}`;
    assert(failures.length===1&&failures[0]===expected,`handoff schema control not isolated: ${needle} => ${JSON.stringify(failures)}`);
  });
}
for(const [label,value] of [["empty",""],["nonstring",42]]){
  control(2,()=>{
    const failures=pmIdentityFailures(agents,value);
    assert(failures.length===1&&failures[0]==="PM_HANDOFF_CONTRACT_UNREADABLE",`${label} handoff control not isolated => ${JSON.stringify(failures)}`);
  });
}
for(const [label,mutate] of [
  ["brief-schema-removed",(m)=>{m["gentle-orchestrator"].prompt=m["gentle-orchestrator"].prompt.split("pm-unit-brief/v1").join("")}],
  ["docs-pointer-removed",(m)=>{m["gentle-orchestrator"].prompt=m["gentle-orchestrator"].prompt.split("docs/specs/pm-handoff.md").join("")}],
  ["orchestrator-prompt-missing",(m)=>{delete m["gentle-orchestrator"].prompt}],
  ["orchestrator-prompt-nonstring",(m)=>{m["gentle-orchestrator"].prompt=42}],
]){
  control(2,()=>{
    const mutated=cloneAgents();
    mutate(mutated);
    const failures=pmIdentityFailures(mutated,handoff);
    assert(failures.length===1&&failures[0]==="ORCHESTRATOR_BRIEF_CONTRACT_POINTER_MISSING",`${label} control not isolated => ${JSON.stringify(failures)}`);
  });
}
console.log(`coverage-group-2-handoff: ${coverageCounts[2]} controls passed`);

// Group 3: coordinator task graph, every required minimum lane, self/peer/deep
// dispatch, leaf dispatch, wildcard deny, arbitrary allow/deny and general.
// The production guard skips only the orchestrator's PM admissions
// (verify-workflow.sh:3130-3131); orchestrator->orchestrator is still checked.
control(3,()=>{assert(coordinatorTaskGraphFailures(agents).length===0,`real coordinator task graph rejected: ${JSON.stringify(coordinatorTaskGraphFailures(agents))}`);});
control(3,()=>{
  const mutated=cloneAgents();
  assert(mutated["gentle-orchestrator"].permission.task["gentle-orchestrator"]!=="allow",`orchestrator self grant already allowed before mutation`);
  mutated["gentle-orchestrator"].permission.task["gentle-orchestrator"]="allow";
  const failures=coordinatorTaskGraphFailures(mutated);
  const expected="COORDINATOR_SELF_OR_DEEP_DISPATCH: gentle-orchestrator.gentle-orchestrator";
  assert(failures.length===1&&failures[0]===expected,`orchestrator self-dispatch control not isolated: ${JSON.stringify(failures)}`);
});
for(const [label,task] of [
  ["absent-map",undefined],
  ["null-map",null],
  ["array-map",[]],
  ["nonobject-string-map","allow"],
]){
  control(3,()=>{
    const mutated=cloneAgents();
    if(task===undefined) delete mutated["gentle-orchestrator"].permission.task;
    else mutated["gentle-orchestrator"].permission.task=task;
    const failures=coordinatorTaskGraphFailures(mutated);
    const expected="ORCHESTRATOR_TASK_MAP_MISSING";
    assert(failures.length===1&&failures[0]===expected,`orchestrator ${label} control not isolated: ${JSON.stringify(failures)}`);
  });
}
for(const pm of coveragePmAgents){
  for(const lane of pmRequired[pm]){
    control(3,()=>{
      const mutated=cloneAgents();
      delete mutated[pm].permission.task[lane];
      const failures=coordinatorTaskGraphFailures(mutated);
      const expected=`PM_REQUIRED_DISPATCH_MISSING: ${pm}.${lane}`;
      assert(failures.length===1&&failures[0]===expected,`required lane control not isolated: ${pm}.${lane} => ${JSON.stringify(failures)}`);
    });
  }
  control(3,()=>{
    const mutated=cloneAgents();
    delete mutated["gentle-orchestrator"].permission.task[pm];
    const failures=coordinatorTaskGraphFailures(mutated);
    const expected=`COORDINATOR_PM_NOT_DISPATCHABLE: ${pm}`;
    assert(failures.length===1&&failures[0]===expected,`orchestrator PM admission control not isolated: ${pm} => ${JSON.stringify(failures)}`);
  });
  for(const target of [pm,coveragePmAgents.find((name)=>name!==pm),"gentle-orchestrator"]){
    control(3,()=>{
      const mutated=cloneAgents();
      mutated[pm].permission.task[target]="allow";
      const failures=coordinatorTaskGraphFailures(mutated);
      const expected=`COORDINATOR_SELF_OR_DEEP_DISPATCH: ${pm}.${target}`;
      assert(failures.includes(expected),`self/peer/orchestrator dispatch control missed ${expected}: ${JSON.stringify(failures)}`);
    });
  }
  for(const wildcard of ["missing","allow"]){
    control(3,()=>{
      const mutated=cloneAgents();
      if(wildcard==="missing") delete mutated[pm].permission.task["*"];
      else mutated[pm].permission.task["*"]="allow";
      const failures=coordinatorTaskGraphFailures(mutated);
      const expected=`PM_TASK_WILDCARD_NOT_DENIED: ${pm}`;
      assert(failures.length===1&&failures[0]===expected,`wildcard ${wildcard} control not isolated: ${pm} => ${JSON.stringify(failures)}`);
    });
  }
  for(const value of ["allow","deny"]){
    control(3,()=>{
      const mutated=cloneAgents();
      mutated[pm].permission.task["arbitrary-writer"]=value;
      const failures=coordinatorTaskGraphFailures(mutated);
      const expected=`PM_TASK_GRANT_UNDECLARED: ${pm}.arbitrary-writer`;
      assert(failures.length===1&&failures[0]===expected,`arbitrary ${value} control not isolated: ${pm} => ${JSON.stringify(failures)}`);
    });
  }
  control(3,()=>{
    const mutated=cloneAgents();
    mutated[pm].permission.task.general="allow";
    const failures=coordinatorTaskGraphFailures(mutated);
    assert(failures.includes(`PM_TASK_GRANT_UNDECLARED: ${pm}.general`)&&failures.includes(`GENERAL_DISPATCH_OUTSIDE_TINY_FIX: ${pm}`),`general dispatch control missed: ${pm} => ${JSON.stringify(failures)}`);
  });
}
for(const leaf of leafAgents){
  control(3,()=>{
    const mutated=cloneAgents();
    mutated[leaf].permission.task={"synthetic-leaf-target":"allow"};
    const failures=coordinatorTaskGraphFailures(mutated);
    const expected=`NON_COORDINATOR_TASK_DISPATCH: ${leaf}`;
    assert(failures.length===1&&failures[0]===expected,`leaf dispatch control not isolated: ${leaf} => ${JSON.stringify(failures)}`);
  });
}
console.log(`coverage-group-3-taskgraph: ${coverageCounts[3]} controls passed`);

// Group 4: execute the production family-rejection loop against configured and
// runtime fixtures for both new PM pairs, preserving the two existing pairs.
control(4,()=>{
  for(const [writer,reviewer] of familyPairs) assert(agents[writer]?.model&&agents[reviewer]?.model,`family pair model missing: ${writer}/${reviewer}`);
  const failures=runPrimaryReviewFamilyLoop(agents,(name)=>({model:agents[name]?.model}));
  assert(failures.length===0,`real configured/runtime family pairs rejected: ${JSON.stringify(failures)}`);
});
control(4,()=>{
  const failures=runPrimaryReviewFamilyLoop(agents,(name)=>independentRuntime[name]);
  assert(failures.length===0,`independent runtime family fixture rejected: ${JSON.stringify(failures)}`);
});
for(const [writer,reviewer] of familyPairs.slice(2)){
  for(const branch of ["configured","runtime"]){
    for(const side of ["writer","reviewer"]){
      for(const mutation of ["same","unknown"]){
        control(4,()=>{
          const configured=cloneAgents();
          const runtime={};
          for(const name of Object.keys(agents)) runtime[name]={model:agents[name].model};
          const other=side==="writer"?reviewer:writer;
          const target=side==="writer"?writer:reviewer;
          const otherFamily=modelFamily(agents[other].model);
          assert(otherFamily,`family fixture missing for ${other}`);
          const badModel=mutation==="same"?familyModel(otherFamily):"synthetic/no-family";
          if(branch==="configured") configured[target].model=badModel;
          else runtime[target].model=badModel;
          const failures=runPrimaryReviewFamilyLoop(configured,(name)=>runtime[name]);
          if(mutation==="same"){
            const expected=`PRIMARY_REVIEW_SAME_FAMILY: ${branch} ${writer} and ${reviewer} both use ${otherFamily}`;
            assert(failures.includes(expected),`same-family ${branch}/${side} control missed ${expected}: ${JSON.stringify(failures)}`);
            assert(failures.filter((failure)=>failure===expected).length===1,`same-family ${branch}/${side} control duplicated: ${JSON.stringify(failures)}`);
          }else{
            const writerModel=branch==="configured"?configured[writer].model:runtime[writer].model;
            const reviewerModel=branch==="configured"?configured[reviewer].model:runtime[reviewer].model;
            const expected=`PRIMARY_REVIEW_FAMILY_UNKNOWN: ${branch} ${writer}=${show(normalizeModel(writerModel))}, ${reviewer}=${show(normalizeModel(reviewerModel))}`;
            assert(failures.includes(expected),`unknown-family ${branch}/${side} control missed ${expected}: ${JSON.stringify(failures)}`);
            assert(failures.filter((failure)=>failure===expected).length===1,`unknown-family ${branch}/${side} control duplicated: ${JSON.stringify(failures)}`);
          }
        });
      }
    }
  }
}
console.log(`coverage-group-4-family: ${coverageCounts[4]} controls passed`);

// Group 5: the production PM general-dispatch helper for both PMs.
for(const pm of coveragePmAgents){
  control(5,()=>{
    const failures=pmGeneralDispatchFailures(pm,agents[pm].permission.task);
    assert(failures.length===0,`real PM general-dispatch control rejected: ${pm} => ${JSON.stringify(failures)}`);
  });
  for(const task of [{general:"deny"},{general:"ask"},undefined]){
    control(5,()=>{
      const failures=pmGeneralDispatchFailures(pm,task);
      assert(failures.length===0,`non-allow general dispatch rejected: ${pm} ${JSON.stringify(task)} => ${JSON.stringify(failures)}`);
    });
  }
  control(5,()=>{
    const failures=pmGeneralDispatchFailures(pm,{general:"allow"});
    const expected=`PM_GENERAL_DISPATCH_NOT_ALLOWED: ${pm}`;
    assert(failures.length===1&&failures[0]===expected,`general allow control not isolated: ${pm} => ${JSON.stringify(failures)}`);
  });
}
console.log(`coverage-group-5-pmgeneral: ${coverageCounts[5]} controls passed`);

const coverageTotal=Object.values(coverageCounts).reduce((sum,value)=>sum+value,0);
console.log(`coverage-total: ${coverageTotal} controls passed`);
"""


PROMPT_BUDGET_CONTROLS = r"""
assert(promptBudgetFailures(agents).length===0,"real prompt budget rejected");
const promptOver={"pm-odd":{prompt:"x".repeat(6000)},"gentle-orchestrator":{prompt:"y".repeat(200000)}};
const promptOverFailures=promptBudgetFailures(promptOver);
assert(promptOverFailures.length===1 && promptOverFailures[0].includes("pm-odd=6000"),"PM prompt cap control is vacuous");
assert(promptBudgetFailures({"pm-odd":{prompt:"x".repeat(5999)}}).length===0,"under-cap PM rejected");
assert(promptBudgetFailures({"gentle-orchestrator":{prompt:"y".repeat(200000)}}).length===0,"orchestrator prompt was capped");
const astralUnder=promptBudgetFailures({"pm-odd":{prompt:"\u{1F600}".repeat(5999)}});
assert(astralUnder.length===0,"codepoint under-cap PM rejected by a UTF-16 count");
const astralOver=promptBudgetFailures({"pm-odd":{prompt:"\u{1F600}".repeat(6000)}});
assert(astralOver.length===1 && astralOver[0].includes("pm-odd=6000"),"codepoint cap control is vacuous");
"""


def permission_failures(agents):
    failures = []
    for name in ALLOWED_AGENTS:
        permission = agents.get(name, {}).get("permission", {})
        if permission.get(PIPELINE_RUN) != "allow":
            failures.append(f"{name}.{PIPELINE_RUN}")
        if permission.get(PERSIST) != "ask":
            failures.append(f"{name}.{PERSIST}")
        if permission.get(ASSESS) != "allow":
            failures.append(f"{name}.{ASSESS}")
        if permission.get(DIFF_READ) != "allow":
            failures.append(f"{name}.{DIFF_READ}")
        if name in {"pm-odd", "pm-systematic"} and agents[name].get("tools", {}).get(ASSESS) is not True:
            failures.append(f"{name}.tools.{ASSESS}")
    for name, agent in agents.items():
        if name in ALLOWED_AGENTS:
            continue
        permission = agent.get("permission", {})
        for tool in (PIPELINE_RUN, PERSIST, ASSESS, DIFF_READ):
            if tool in permission:
                failures.append(f"{name}.{tool}")
    return failures


class ReviewPipelinePermissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.agents = cls.config["agent"]
        cls.verifier = VERIFIER_PATH.read_text(encoding="utf-8")
        cls.handoff = HANDOFF_PATH.read_text(encoding="utf-8")

    def test_three_agents_receive_exact_permissions_and_pm_tool_maps(self):
        self.assertEqual(self.config["permission"][PIPELINE_RUN], "deny")
        self.assertEqual(self.config["permission"][PERSIST], "deny")
        self.assertEqual(self.config["permission"][ASSESS], "deny")
        self.assertEqual(self.config["permission"][DIFF_READ], "deny")
        for name in ALLOWED_AGENTS:
            self.assertEqual(self.agents[name]["permission"][PIPELINE_RUN], "allow")
            self.assertEqual(self.agents[name]["permission"][PERSIST], "ask")
            self.assertEqual(self.agents[name]["permission"][ASSESS], "allow")
            self.assertEqual(self.agents[name]["permission"][DIFF_READ], "allow")
        for name in {"pm-odd", "pm-systematic"}:
            self.assertIs(self.agents[name]["tools"][PIPELINE_RUN], True)
            self.assertIs(self.agents[name]["tools"][PERSIST], True)
            self.assertIs(self.agents[name]["tools"][ASSESS], True)
            self.assertIs(self.agents[name]["tools"][DIFF_READ], True)
        self.assertEqual(permission_failures(self.agents), [])

    def test_pm_task_maps_do_not_grant_general(self):
        for name in ("pm-odd", "pm-systematic"):
            with self.subTest(agent=name):
                self.assertNotIn("general", self.agents[name]["permission"]["task"])

    def test_missing_pipeline_grant_is_detected(self):
        agents = json.loads(json.dumps(self.agents))
        del agents["pm-odd"]["permission"][PIPELINE_RUN]
        self.assertIn(f"pm-odd.{PIPELINE_RUN}", permission_failures(agents))

    def test_wrong_persist_permission_is_detected(self):
        agents = json.loads(json.dumps(self.agents))
        agents["pm-systematic"]["permission"][PERSIST] = "allow"
        self.assertIn(f"pm-systematic.{PERSIST}", permission_failures(agents))

    def test_missing_assess_grant_is_detected(self):
        agents = json.loads(json.dumps(self.agents))
        self.assertEqual(agents["pm-odd"]["permission"][ASSESS], "allow")
        del agents["pm-odd"]["permission"][ASSESS]
        self.assertIn(f"pm-odd.{ASSESS}", permission_failures(agents))

    def test_missing_diff_read_grant_is_detected(self):
        agents = json.loads(json.dumps(self.agents))
        del agents["pm-odd"]["permission"][DIFF_READ]
        self.assertIn(f"pm-odd.{DIFF_READ}", permission_failures(agents))

    def test_grant_to_another_agent_is_detected(self):
        agents = json.loads(json.dumps(self.agents))
        agents["general"]["permission"][PERSIST] = "ask"
        agents["general"]["permission"][ASSESS] = "allow"
        self.assertIn(f"general.{PERSIST}", permission_failures(agents))
        self.assertIn(f"general.{ASSESS}", permission_failures(agents))
        agents["general"]["permission"][DIFF_READ] = "allow"
        self.assertIn(f"general.{DIFF_READ}", permission_failures(agents))

    def test_verifier_gates_both_tools_and_exempts_only_allow_exceptions(self):
        gated = self.verifier.split("const gatedHostMutations=[", 1)[1].split("]", 1)[0]
        self.assertIn(f'"{PIPELINE_RUN}"', gated)
        self.assertIn(f'"{PERSIST}"', gated)
        self.assertIn('name!=="host_review_start"', self.verifier)
        self.assertIn('name!=="host_review_materialize"', self.verifier)
        self.assertIn(f'name!=="{PIPELINE_RUN}"', self.verifier)
        self.assertIn("hostReviewPipelineRunExceptionFailures", self.verifier)
        self.assertIn("hostReviewPersistFailures", self.verifier)
        self.assertIn("hostReviewAssessFailures", self.verifier)
        self.assertIn("HOST_REVIEW_ASSESS_OMITTED_POSITIVE_CONTROL_FAILED", self.verifier)
        self.assertIn("hostReviewNewGrantSweepFailures", self.verifier)

    def test_coordinator_inventory_uses_shared_set_without_hardcoded_triple(self):
        self.assertEqual(hardcoded_coordinator_triple_lines(self.verifier), [])
        self.assertIn('const coordinatorAgents=["gentle-orchestrator",...pmAgents]', self.verifier)
        self.assertNotIn("gentle-orchestrator-legacy", self.verifier)
        planted = "\n".join(
            ["// mutation control", 'for (const name of ["gentle-orchestrator","pm-odd","pm-systematic"]) {']
        )
        self.assertEqual(hardcoded_coordinator_triple_lines(planted), [2])

    def test_extracted_verifier_functions_pass_and_detect_reverted_controls(self):
        names = (
            "hostReviewAssessFailures",
            "hostReviewDiffReadFailures",
            "hostReviewPipelineRunFailures",
            "hostReviewPersistFailures",
            "hostReviewNewGlobalDefaultFailures",
            "hostReviewNewToolFailures",
            "hostReviewPipelineRunExceptionFailures",
            "hostReviewNewGrantSweepFailures",
            "pmGeneralDispatchFailures",
            "pmIdentityFailures",
            "coordinatorTaskGraphFailures",
            "normalizeModel",
            "modelFamily",
            "promptBudgetFailures",
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
        declarations = "\n".join(
            extract_declaration(self.verifier, name)
            for name in ("pmAgents", "coordinatorAgents")
        )
        self.assertIn(
            'const coordinatorAgents=["gentle-orchestrator",...pmAgents]',
            declarations,
            "coordinator set must derive from the shared pmAgents declaration",
        )
        self.assertEqual(sum(len(v) for v in PM_REQUIRED_DISPATCH.values()), 15, "unexpected required dispatch lane inventory")
        identity_needles = json.loads(
            "[" + self.verifier.split("const needles=[", 1)[1].split("]", 1)[0] + "]"
        )
        self.assertEqual(len(identity_needles), 7, "unexpected PM identity needle inventory")
        family_marker = 'for (const [writer,reviewer] of [["general","gentle-orchestrator"]'
        family_loop = extract_braced_block(self.verifier, family_marker)
        for writer, reviewer in (
            ("general", "gentle-orchestrator"),
            ("gentle-ai-worker", "gentle-ai-verify"),
            ("pm-odd", "odd-apply"),
            ("pm-systematic", "gentle-ai-worker"),
        ):
            self.assertEqual(
                family_loop.count(f'["{writer}","{reviewer}"]'),
                1,
                f"family loop must contain exactly one {writer}/{reviewer} pair",
            )
        self.assertNotIn(
            'for (const [writer,reviewer] of [["general","gentle-orchestrator"],'
            '["gentle-ai-worker","gentle-ai-verify"]])',
            self.verifier,
            "legacy two-pair family loop must be replaced",
        )
        prompt_sizes = {
            name: len(agent["prompt"])
            for name, agent in self.agents.items()
            if isinstance(agent.get("prompt"), str)
        }
        coverage_controls = (
            COVERAGE_CONTROLS_TEMPLATE.replace(
                "__PM_AGENTS__", json.dumps(["pm-odd", "pm-systematic"])
            )
            .replace("__PM_REQUIRED__", json.dumps(PM_REQUIRED_DISPATCH))
            .replace("__LEAF_AGENTS__", json.dumps(LEAF_DISPATCH_AGENTS))
            .replace("__HANDOFF_TEXT__", json.dumps(self.handoff))
            .replace("__IDENTITY_NEEDLES__", json.dumps(identity_needles))
            .replace("__PM_TINYFIX__", json.dumps(PM_TINY_FIX_INSTRUCTION))
            .replace("__PM_TINYFIX_STALE__", json.dumps(PM_TINY_FIX_STALE_SENTENCE))
            .replace("__FAMILY_LOOP__", family_loop)
        )
        for placeholder in (
            "__PM_AGENTS__",
            "__PM_REQUIRED__",
            "__LEAF_AGENTS__",
            "__HANDOFF_TEXT__",
            "__IDENTITY_NEEDLES__",
            "__PM_TINYFIX__",
            "__PM_TINYFIX_STALE__",
            "__FAMILY_LOOP__",
        ):
            self.assertNotIn(placeholder, coverage_controls)
        gated_source = self.verifier.split("const gatedHostMutations=[", 1)[1].split("]", 1)[0]
        gated = re.findall(r'"([^"]+)"', gated_source)
        script = "\n".join(extracted) + "\n" + declarations + "\n" + f"""
const agents={json.dumps(self.agents)};
const cloneAgents=()=>JSON.parse(JSON.stringify(agents));
const gated={json.dumps(gated)};
const cfgPerm=(agent,tool)=>agent?.permission?.[tool];
const show=(value)=>JSON.stringify(value);
const assert=(condition,message)=>{{if(!condition)throw new Error(message)}};
for(const name of {json.dumps(sorted(ALLOWED_AGENTS))}){{
  assert(hostReviewAssessFailures(name,agents[name]).length===0,`assess grant rejected: ${{name}}`);
  assert(hostReviewDiffReadFailures(name,agents[name]).length===0,`diff-read grant rejected: ${{name}}`);
  assert(hostReviewPipelineRunFailures(name,agents[name]).length===0,`pipeline grant rejected: ${{name}}`);
  assert(hostReviewPersistFailures(name,agents[name]).length===0,`persist grant rejected: ${{name}}`);
}}
for(const name of ["pm-odd","pm-systematic"]) assert(hostReviewNewToolFailures(name,agents[name]).length===0,`tool map rejected: ${{name}}`);
assert(hostReviewPipelineRunExceptionFailures(gated,agents["gentle-orchestrator"]).length===0,"orchestrator exception rejected");
assert(hostReviewNewGrantSweepFailures(agents).length===0,"negative sweep rejected configured agents");
assert(hostReviewNewGlobalDefaultFailures("host_review_pipeline_run","deny").length===0,"pipeline default rejected");
assert(hostReviewNewGlobalDefaultFailures("host_review_persist","deny").length===0,"persist default rejected");
assert(hostReviewNewGlobalDefaultFailures("host_review_assess","deny").length===0,"assess default rejected");
assert(hostReviewNewGlobalDefaultFailures("host_review_diff_read","deny").length===0,"diff-read default rejected");
assert(hostReviewNewGlobalDefaultFailures("host_review_pipeline_run","allow").length===1,"pipeline default control is vacuous");
assert(hostReviewNewGlobalDefaultFailures("host_review_persist","ask").length===1,"persist default control is vacuous");
assert(hostReviewNewGlobalDefaultFailures("host_review_assess","allow").length===1,"assess default control is vacuous");
assert(hostReviewNewGlobalDefaultFailures("host_review_diff_read","allow").length===1,"diff-read default control is vacuous");
assert(hostReviewPipelineRunFailures("omitted",{{permission:{{}}}}).length===1,"pipeline omission control is vacuous");
assert(hostReviewPipelineRunFailures("wrong",{{permission:{{host_review_pipeline_run:"ask"}}}}).length===1,"pipeline value control is vacuous");
assert(hostReviewAssessFailures("omitted",{{permission:{{}}}}).length===1,"assess omission control is vacuous");
assert(hostReviewAssessFailures("wrong",{{permission:{{host_review_assess:"ask"}}}}).length===1,"assess value control is vacuous");
assert(hostReviewDiffReadFailures("omitted",{{permission:{{}}}}).length===1,"diff-read omission control is vacuous");
assert(hostReviewDiffReadFailures("wrong",{{permission:{{host_review_diff_read:"ask"}}}}).length===1,"diff-read value control is vacuous");
assert(hostReviewPersistFailures("omitted",{{permission:{{}}}}).length===1,"persist omission control is vacuous");
assert(hostReviewPersistFailures("wrong",{{permission:{{host_review_persist:"allow"}}}}).length===1,"persist value control is vacuous");
assert(hostReviewNewToolFailures("omitted",{{tools:{{}}}}).length===4,"tool omission control is vacuous");
for(const tool of ["host_review_assess","host_review_diff_read","host_review_pipeline_run","host_review_persist"]) assert(hostReviewNewToolFailures("disabled",{{tools:{{[tool]:false}}}}).some(failure=>failure.endsWith(tool)),`tool value control is vacuous: ${{tool}}`);
assert(hostReviewPipelineRunExceptionFailures(gated.filter(name=>name!=="host_review_pipeline_run"),{{permission:{{host_review_pipeline_run:"allow"}}}}).length===1,"exception omission control is vacuous");
assert(hostReviewPipelineRunExceptionFailures(gated,{{permission:{{host_review_pipeline_run:"ask"}}}}).length===1,"exception value control is vacuous");
for(const tool of ["host_review_assess","host_review_diff_read","host_review_pipeline_run","host_review_persist"]) assert(hostReviewNewGrantSweepFailures({{"synthetic-fourth-agent":{{permission:{{[tool]:"allow"}}}}}}).length===1,`sweep control is vacuous: ${{tool}}`);
assert(pmGeneralDispatchFailures("pm-odd",agents["pm-odd"].permission.task).length===0,"PM general-dispatch control rejected pm-odd");
assert(pmGeneralDispatchFailures("pm-systematic",agents["pm-systematic"].permission.task).length===0,"PM general-dispatch control rejected pm-systematic");
assert(pmGeneralDispatchFailures("pm-odd",{{general:"allow"}}).length===1,"PM general-dispatch allow control is vacuous");
console.log("extracted verifier assertions and positive controls passed");
""" + "\n" + PROMPT_BUDGET_CONTROLS + "\n" + coverage_controls
        try:
            runtime = shutil.which("bun") or "bun"
            with tempfile.TemporaryDirectory() as tmp:
                script_path = Path(tmp) / "verifier-harness.ts"
                script_path.write_text(script, encoding="utf-8")
                result = subprocess.run(
                    [runtime, str(script_path)],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
        except PermissionError:
            self.skipTest("sandbox policy denies child Bun processes; run the extracted verifier harness directly")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout)
        self.assertIn("extracted verifier assertions and positive controls passed", result.stdout)
        for name, size in prompt_sizes.items():
            self.assertIn(f"prompt-size: {name}={size}", result.stdout)
        for marker in (
            "coverage-group-1-identity: 27 controls passed",
            "coverage-group-2-handoff: 8 controls passed",
            "coverage-group-3-taskgraph: 45 controls passed",
            "coverage-group-4-family: 18 controls passed",
            "coverage-group-5-pmgeneral: 10 controls passed",
            "coverage-total: 108 controls passed",
        ):
            self.assertIn(marker, result.stdout)


class HostFixedToolPermissionTests(unittest.TestCase):
    """Q90 T3a1: the orchestrator-only plan-write and test-run fixed tools."""

    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.agents = cls.config["agent"]
        cls.verifier = VERIFIER_PATH.read_text(encoding="utf-8")
        cls.prompt = cls.agents["gentle-orchestrator"]["prompt"]

    def run_controls(self, body, fragments=None):
        bun = shutil.which("bun")
        if bun is None:
            self.skipTest("Bun runtime not found on PATH; extracted verifier harness requires Bun")
        functions = "\n".join(
            extract_braced_block(self.verifier, f"function {name}(")
            for name in HOST_TOOL_FUNCTION_NAMES
        )
        script = (
            'import { readFileSync } from "node:fs";\n'
            "const show=(value)=>JSON.stringify(value);\n"
            "const cfgPerm=(agent,tool)=>agent?.permission?.[tool];\n"
            "const assert=(condition,message)=>{if(!condition)throw new Error(message)};\n"
            + functions
            + "\nconst config=JSON.parse(readFileSync(process.env.HOST_TOOL_CONFIG_PATH,\"utf8\"));\n"
            "const agents=config.agent;\nconst gp=config.permission;\n"
            "const prompt=readFileSync(process.env.HOST_TOOL_PROMPT_PATH,\"utf8\");\n"
            "const fragments=JSON.parse(readFileSync(process.env.HOST_TOOL_FRAGMENTS_PATH,\"utf8\"));\n"
            + body
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            paths = {
                "HOST_TOOL_CONFIG_PATH": tmp_path / "config.json",
                "HOST_TOOL_PROMPT_PATH": tmp_path / "prompt.txt",
                "HOST_TOOL_FRAGMENTS_PATH": tmp_path / "fragments.json",
            }
            paths["HOST_TOOL_CONFIG_PATH"].write_text(json.dumps(self.config), encoding="utf-8")
            paths["HOST_TOOL_PROMPT_PATH"].write_text(self.prompt, encoding="utf-8")
            paths["HOST_TOOL_FRAGMENTS_PATH"].write_text(
                json.dumps(list(fragments or HOST_TOOL_PROMPT_FRAGMENTS)), encoding="utf-8"
            )
            script_path = tmp_path / "controls.ts"
            script_path.write_text(script, encoding="utf-8")
            environment = dict(os.environ)
            environment.update({key: str(value) for key, value in paths.items()})
            try:
                result = subprocess.run(
                    [bun, str(script_path)],
                    cwd=ROOT, capture_output=True, text=True, env=environment, check=False,
                )
            except PermissionError:
                self.skipTest("sandbox policy denies child Bun processes")
            except (FileNotFoundError, OSError):
                self.skipTest("Bun runtime could not be executed; run the extracted verifier harness directly")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_actual_config_and_tool_maps(self):
        self.assertEqual(self.config["permission"][HOST_TEST_RUN], "deny")
        self.assertEqual(self.config["permission"][HOST_PLAN_WRITE], "deny")
        permission = self.agents["gentle-orchestrator"]["permission"]
        self.assertEqual(permission[HOST_TEST_RUN], "allow")
        self.assertEqual(permission[HOST_PLAN_WRITE], "ask")
        for name, agent in self.agents.items():
            if name != "gentle-orchestrator" and HOST_TEST_RUN in agent.get("permission", {}):
                with self.subTest(agent=name):
                    self.assertEqual(agent["permission"][HOST_TEST_RUN], "deny")
        maps = [("global", self.config.get("tools", {}))] + [
            (name, agent.get("tools", {})) for name, agent in self.agents.items()
        ]
        for name, tools in maps:
            self.assertNotIn(HOST_TEST_RUN, tools)
            if name == "planner":
                self.assertIs(tools.get(HOST_PLAN_WRITE), True)
                self.assertIs(tools.get("host_gate_verdict"), True)
                self.assertIs(tools.get("host_task_mark"), False)
            elif name == "planner-evidence":
                self.assertIs(tools.get(HOST_PLAN_WRITE), False)
                self.assertIs(tools.get("host_gate_verdict"), False)
                self.assertIs(tools.get("host_task_mark"), False)
            else:
                self.assertNotIn(HOST_PLAN_WRITE, tools)
        self.run_controls(
            'assert(hostTestRunGlobalDefaultFailures(gp.host_test_run).length===0,"test-run default");\n'
            'assert(hostPlanWriteGlobalDefaultFailures(gp.host_plan_write).length===0,"plan-write default");\n'
            'assert(hostTestRunOrchestratorFailures(agents["gentle-orchestrator"]).length===0,"test-run grant");\n'
            'assert(hostPlanWriteOrchestratorFailures(agents["gentle-orchestrator"]).length===0,"plan-write grant");\n'
            'assert(hostTestRunGrantSweepFailures(agents).length===0,"test-run sweep");\n'
            'assert(hostPlanWriteGrantSweepFailures(agents,["gentle-orchestrator","pm-odd","pm-systematic","planner"]).length===0,"plan-write sweep");\n'
        )

    def test_negative_controls_remove_or_flip_grants(self):
        self.run_controls(
            r'''
const removed=JSON.parse(JSON.stringify(agents));
delete removed["gentle-orchestrator"].permission.host_test_run;
delete removed["gentle-orchestrator"].permission.host_plan_write;
assert(hostTestRunOrchestratorFailures(removed["gentle-orchestrator"]).includes('ORCHESTRATOR_HOST_TEST_RUN_NOT_ALLOW: undefined'),"missing test-run");
assert(hostPlanWriteOrchestratorFailures(removed["gentle-orchestrator"]).includes('ORCHESTRATOR_HOST_PLAN_WRITE_NOT_ASK: undefined'),"missing plan-write");
const wrong=JSON.parse(JSON.stringify(agents));
wrong["gentle-orchestrator"].permission.host_test_run="ask";
wrong["gentle-orchestrator"].permission.host_plan_write="allow";
assert(hostTestRunOrchestratorFailures(wrong["gentle-orchestrator"]).includes('ORCHESTRATOR_HOST_TEST_RUN_NOT_ALLOW: "ask"'),"test-run ask");
assert(hostPlanWriteOrchestratorFailures(wrong["gentle-orchestrator"]).includes('ORCHESTRATOR_HOST_PLAN_WRITE_NOT_ASK: "allow"'),"plan-write allow");
assert(hostTestRunGlobalDefaultFailures("allow").includes('HOST_TEST_RUN_GLOBAL_DEFAULT_NOT_DENY: "allow"'),"global test-run");
assert(hostTestRunGlobalDefaultFailures("ask").includes('HOST_TEST_RUN_GLOBAL_DEFAULT_NOT_DENY: "ask"'),"global test-run ask");
assert(hostPlanWriteGlobalDefaultFailures("allow").includes('HOST_PLAN_WRITE_GLOBAL_DEFAULT_NOT_DENY: "allow"'),"global plan-write");
assert(hostPlanWriteGlobalDefaultFailures("ask").includes('HOST_PLAN_WRITE_GLOBAL_DEFAULT_NOT_DENY: "ask"'),"global plan-write ask");
for (const name of ["pm-odd","pm-systematic","general","odd-apply","gentle-ai-worker","review-risk","advisor-security-pre","synthetic-agent"]) {
  for (const value of ["ask","allow"]) {
    const failures=hostTestRunGrantSweepFailures({[name]:{permission:{host_test_run:value}}});
    assert(failures.some((failure)=>failure.includes(`HOST_TEST_RUN_GRANTED_OUTSIDE_ORCHESTRATOR: ${name}="${value}"`)),`sweep ${name}=${value}`);
  }
}
assert(hostTestRunGrantSweepFailures({"gentle-orchestrator":{permission:{host_test_run:"allow"}}}).length===0,"orchestrator allow");
assert(hostTestRunGrantSweepFailures({"pm-odd":{permission:{host_test_run:"deny"}}}).length===0,"explicit deny");
const planAllowed=["gentle-orchestrator","pm-odd","pm-systematic","planner"];
for (const name of ["general","odd-apply","gentle-ai-worker","review-risk","advisor-security-pre","synthetic-agent"]) {
  for (const value of ["ask","allow"]) {
    const failures=hostPlanWriteGrantSweepFailures({[name]:{permission:{host_plan_write:value}}},planAllowed);
    assert(failures.some((failure)=>failure.includes(`HOST_PLAN_WRITE_GRANTED_OUTSIDE_COORDINATORS: ${name}="${value}"`)),`plan-write sweep ${name}=${value}`);
  }
}
assert(hostPlanWriteGrantSweepFailures({"gentle-orchestrator":{permission:{host_plan_write:"ask"}}, "pm-odd":{permission:{host_plan_write:"ask"}}, "pm-systematic":{permission:{host_plan_write:"allow"}}},planAllowed).length===0,"coordinator grants accepted");
assert(hostPlanWriteGrantSweepFailures({"synthetic-agent":{permission:{host_plan_write:"deny"}}, "synthetic-omitted":{permission:{}}},planAllowed).length===0,"deny and undefined non-grants accepted");
''')

    def test_prompt_clauses_and_removal_controls(self):
        self.run_controls(
            r'''
assert(hostToolPromptFailures(prompt).length===0,"real prompt rejected");
assert(hostToolPromptFailures("").length===fragments.length,"empty prompt");
for (const fragment of fragments) {
  const mutated=prompt.replace(fragment,"removed");
  assert(mutated!==prompt,`fragment absent: ${fragment}`);
  assert(hostToolPromptFailures(mutated).some((failure)=>failure.includes(JSON.stringify(fragment))),`removal control: ${fragment}`);
}
''')


    def test_plan_write_sweep_production_wiring_and_controls(self):
        self.assertIn(
            "for (const failure of hostPlanWriteGrantSweepFailures(deployedAgents,planWriterAgents)) fail(failure)",
            self.verifier,
        )
        self.assertIn("HOST_PLAN_WRITE_GRANT_SWEEP_POSITIVE_CONTROL_FAILED", self.verifier)
        self.run_controls(
            r'''
const allowed=["gentle-orchestrator","pm-odd","pm-systematic","planner"];
assert(hostPlanWriteGrantSweepFailures(agents,allowed).length===0,"real config plan-write sweep");
for (const value of ["ask","allow"]) {
  const synthetic=`synthetic-${value}-agent`;
  const detected=hostPlanWriteGrantSweepFailures({[synthetic]:{permission:{host_plan_write:value}}},allowed);
  assert(detected.includes(`HOST_PLAN_WRITE_GRANTED_OUTSIDE_COORDINATORS: ${synthetic}="${value}"`),`synthetic non-coordinator ${value}`);
}
assert(hostPlanWriteGrantSweepFailures({"gentle-orchestrator":{permission:{host_plan_write:"ask"}}, "pm-odd":{permission:{host_plan_write:"ask"}}, "pm-systematic":{permission:{host_plan_write:"allow"}}},allowed).length===0,"synthetic coordinators accepted");
''')

    def test_missing_bun_skips_cleanly(self):
        with mock.patch("shutil.which", return_value=None):
            with self.assertRaises(unittest.SkipTest) as raised:
                self.run_controls("")
        self.assertIn("Bun", str(raised.exception))

    def test_unexecutable_bun_skips_cleanly(self):
        with mock.patch("subprocess.run", side_effect=FileNotFoundError("missing bun")):
            with self.assertRaises(unittest.SkipTest) as raised:
                self.run_controls("")
        self.assertIn("Bun", str(raised.exception))
        self.assertNotIsInstance(raised.exception, AssertionError)


RELAY_REVIEW_AGENTS = [
    "asi-review-risk",
    "asi-review-resilience",
    "asi-review-readability",
    "asi-review-reliability",
    "asi-review-refuter",
    "asi-review-validator",
]
PLAIN_PROVIDER_REVIEW_AGENTS = [
    "review-risk",
    "review-resilience",
    "review-readability",
    "review-reliability",
    "review-refuter",
    "review-validator",
]


class ReviewDispatchPermissionTests(unittest.TestCase):
    """Q90 T3a2: raw task-map review-dispatch enforcement."""

    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.agents = cls.config["agent"]
        cls.verifier = VERIFIER_PATH.read_text(encoding="utf-8")

    def predicate_source(self):
        self.assertIn(
            "function reviewDispatchFailures(",
            self.verifier,
            "missing production reviewDispatchFailures predicate",
        )
        return extract_braced_block(self.verifier, "function reviewDispatchFailures(")

    def declarations(self):
        return "\n".join(
            extract_declaration(self.verifier, name)
            for name in ("relayReviewAgents", "plainProviderReviewAgents")
        )

    def call_site(self):
        lines = [
            line.strip()
            for line in self.verifier.splitlines()
            if line.strip().startswith("for (const failure of reviewDispatchFailures(")
        ]
        self.assertEqual(len(lines), 1, "production reviewDispatchFailures call site must be unique")
        return lines[0]

    def run_script(self, body, predicate=None):
        prelude = (
            'import { readFileSync } from "node:fs";\n'
            'const agents=JSON.parse(readFileSync(process.env.REVIEW_DISPATCH_AGENTS_PATH,"utf8"));\n'
            'const expectedRelay=JSON.parse(readFileSync(process.env.REVIEW_DISPATCH_RELAY_PATH,"utf8"));\n'
            'const expectedPlain=JSON.parse(readFileSync(process.env.REVIEW_DISPATCH_PLAIN_PATH,"utf8"));\n'
            "const assert=(condition,message)=>{if(!condition)throw new Error(message)};\n"
            "const clone=()=>JSON.parse(JSON.stringify(agents));\n"
        )
        lane_guard = (
            'assert(JSON.stringify(relayReviewAgents)===JSON.stringify(expectedRelay),"production relay lane list drift");\n'
            'assert(JSON.stringify(plainProviderReviewAgents)===JSON.stringify(expectedPlain),"production plain lane list drift");\n'
        )
        script = (
            prelude
            + (predicate or self.predicate_source())
            + "\n"
            + self.declarations()
            + "\n"
            + lane_guard
            + body
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            agents_path = tmp_path / "agents.json"
            relay_path = tmp_path / "relay.json"
            plain_path = tmp_path / "plain.json"
            script_path = tmp_path / "review-dispatch-controls.ts"
            agents_path.write_text(json.dumps(self.agents), encoding="utf-8")
            relay_path.write_text(json.dumps(RELAY_REVIEW_AGENTS), encoding="utf-8")
            plain_path.write_text(json.dumps(PLAIN_PROVIDER_REVIEW_AGENTS), encoding="utf-8")
            script_path.write_text(script, encoding="utf-8")
            environment = dict(os.environ)
            environment.update(
                {
                    "REVIEW_DISPATCH_AGENTS_PATH": str(agents_path),
                    "REVIEW_DISPATCH_RELAY_PATH": str(relay_path),
                    "REVIEW_DISPATCH_PLAIN_PATH": str(plain_path),
                }
            )
            try:
                return subprocess.run(
                    [shutil.which("bun") or "bun", str(script_path)],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    env=environment,
                    check=False,
                )
            except PermissionError:
                self.skipTest("sandbox policy denies child Bun processes")

    def assert_script(self, body):
        result = self.run_script(body)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_production_predicate_and_call_site_exist(self):
        self.predicate_source()
        call = self.call_site()
        self.assertIn("deployedAgents", call)
        self.assertIn("relayReviewAgents", call)
        self.assertIn("plainProviderReviewAgents", call)

    def test_real_config_accepted_and_every_orchestrator_lane_required(self):
        self.assert_script(
            r'''
assert(reviewDispatchFailures(agents,relayReviewAgents,plainProviderReviewAgents).length===0,"real config rejected");
for (const name of relayReviewAgents) {
  const mutated=clone();
  delete mutated["gentle-orchestrator"].permission.task[name];
  const failures=reviewDispatchFailures(mutated,relayReviewAgents,plainProviderReviewAgents);
  const expected=`RELAY_TASK_NOT_ALLOWED: ${name}`;
  assert(failures.length===1&&failures[0]===expected,`relay omission not isolated: ${name} => ${JSON.stringify(failures)}`);
}
for (const name of plainProviderReviewAgents) {
  for (const value of ["allow","ask"]) {
    const mutated=clone();
    mutated["gentle-orchestrator"].permission.task[name]=value;
    const failures=reviewDispatchFailures(mutated,relayReviewAgents,plainProviderReviewAgents);
    const expected=`PLAIN_PROVIDER_REVIEW_TASK_NOT_DENIED: ${name}`;
    assert(failures.length===1&&failures[0]===expected,`plain ${value} not isolated: ${name} => ${JSON.stringify(failures)}`);
  }
}
console.log("orchestrator lanes: 6 relay + 12 plain controls passed");
'''
        )

    def test_pm_review_grants_are_rejected_for_allow_and_ask(self):
        result = self.assert_script(
            r'''
for (const pm of ["pm-odd","pm-systematic"]) {
  for (const lane of [...relayReviewAgents,...plainProviderReviewAgents]) {
    for (const value of ["allow","ask"]) {
      const mutated=clone();
      assert(!(lane in mutated[pm].permission.task),`lane already present before mutation: ${pm}.${lane}`);
      mutated[pm].permission.task[lane]=value;
      const failures=reviewDispatchFailures(mutated,relayReviewAgents,plainProviderReviewAgents);
      const expected=`REVIEW_TASK_GRANTED_OUTSIDE_ORCHESTRATOR: ${pm}.${lane}="${value}"`;
      assert(failures.length===1&&failures[0]===expected,`${pm}.${lane}=${value} not isolated => ${JSON.stringify(failures)}`);
    }
  }
}
console.log("PM review grants: 48 controls passed");
'''
        )
        self.assertIn("PM review grants: 48 controls passed", result.stdout)

    def test_partial_glob_review_grants_fail_closed(self):
        result = self.assert_script(
            r'''
const partialGlobs=["asi-*","rev*","*risk","*-risk","*review*"];
const patternAgents=["pm-odd","pm-systematic","advisor-security-pre","odd-apply","gentle-ai-worker"];
for (const agentName of patternAgents) {
  for (const pattern of partialGlobs) {
    for (const value of ["allow","ask"]) {
      const mutated=clone();
      if (!mutated[agentName].permission) mutated[agentName].permission={};
      if (!mutated[agentName].permission.task||typeof mutated[agentName].permission.task!=="object"||Array.isArray(mutated[agentName].permission.task)) mutated[agentName].permission.task={"*":"deny"};
      mutated[agentName].permission.task[pattern]=value;
      const failures=reviewDispatchFailures(mutated,relayReviewAgents,plainProviderReviewAgents);
      const expected=`REVIEW_TASK_GRANTED_OUTSIDE_ORCHESTRATOR: ${agentName}.${pattern}="${value}"`;
      assert(failures.length===1&&failures[0]===expected,`${agentName}.${pattern}=${value} not isolated => ${JSON.stringify(failures)}`);
    }
  }
}
for (const pattern of partialGlobs) {
  for (const value of ["deny",false]) {
    const mutated=clone();
    mutated["pm-odd"].permission.task[pattern]=value;
    const failures=reviewDispatchFailures(mutated,relayReviewAgents,plainProviderReviewAgents);
    assert(failures.length===0,`protective ${pattern}=${JSON.stringify(value)} rejected => ${JSON.stringify(failures)}`);
  }
}
const unrelated=clone();
unrelated["pm-odd"].permission.task["frontend-*"]="ask";
assert(reviewDispatchFailures(unrelated,relayReviewAgents,plainProviderReviewAgents).length===0,"non-review partial glob was flagged");
console.log(`partial-glob review grants: ${partialGlobs.length*patternAgents.length*2} grants + ${partialGlobs.length*2+1} non-grants passed`);
'''
        )
        self.assertIn(
            "partial-glob review grants: 50 grants + 11 non-grants passed",
            result.stdout,
        )

    def test_advisor_writer_and_wildcard_scalar_shapes_fail_closed(self):
        self.assert_script(
            r'''
for (const agentName of ["advisor-security-pre","odd-apply","gentle-ai-worker","general"]) {
  for (const lane of relayReviewAgents) {
    const mutated=clone();
    if (!mutated[agentName].permission) mutated[agentName].permission={};
    if (!mutated[agentName].permission.task||typeof mutated[agentName].permission.task!=="object"||Array.isArray(mutated[agentName].permission.task)) mutated[agentName].permission.task={"*":"deny"};
    mutated[agentName].permission.task[lane]="allow";
    const failures=reviewDispatchFailures(mutated,relayReviewAgents,plainProviderReviewAgents);
    const expected=`REVIEW_TASK_GRANTED_OUTSIDE_ORCHESTRATOR: ${agentName}.${lane}="allow"`;
    assert(failures.length===1&&failures[0]===expected,`${agentName}.${lane} not isolated => ${JSON.stringify(failures)}`);
  }
}
for (const agentName of ["pm-odd","pm-systematic","advisor-security-pre","odd-apply"]) {
  for (const value of ["allow","ask"]) {
    let mutated=clone();
    mutated[agentName].permission.task={"*":value};
    let failures=reviewDispatchFailures(mutated,relayReviewAgents,plainProviderReviewAgents);
    let expected=`REVIEW_TASK_GRANTED_OUTSIDE_ORCHESTRATOR: ${agentName}.*="${value}"`;
    assert(failures.length===1&&failures[0]===expected,`wildcard ${agentName}=${value} not isolated => ${JSON.stringify(failures)}`);
    mutated=clone();
    mutated[agentName].permission.task=value;
    failures=reviewDispatchFailures(mutated,relayReviewAgents,plainProviderReviewAgents);
    expected=`REVIEW_TASK_GRANTED_OUTSIDE_ORCHESTRATOR: ${agentName}="${value}"`;
    assert(failures.length===1&&failures[0]===expected,`scalar ${agentName}=${value} not isolated => ${JSON.stringify(failures)}`);
  }
}
for (const malformed of [[],null,42,true]) {
  const mutated=clone();
  mutated["pm-odd"].permission.task=malformed;
  const failures=reviewDispatchFailures(mutated,relayReviewAgents,plainProviderReviewAgents);
  assert(failures.length===1&&failures[0]==="REVIEW_TASK_MAP_INVALID: pm-odd",`malformed ${JSON.stringify(malformed)} not isolated => ${JSON.stringify(failures)}`);
}
const denied=clone();
denied["pm-odd"].permission.task["asi-review-risk"]="deny";
assert(reviewDispatchFailures(denied,relayReviewAgents,plainProviderReviewAgents).length===0,"named deny review key treated as a grant");
console.log("advisor/writer/wildcard/scalar/malformed controls passed");
'''
        )

    def test_production_call_site_propagates_failures(self):
        call = self.call_site()
        self.assert_script(
            "const runCallSite=(deployedAgents,fail)=>{" + call + "};\n"
            'const bad=clone();\n'
            'bad["pm-odd"].permission.task["asi-review-risk"]="allow";\n'
            "const badFailures=[];\n"
            "runCallSite(bad,(message)=>badFailures.push(message));\n"
            'assert(badFailures.length===1&&badFailures[0]===\'REVIEW_TASK_GRANTED_OUTSIDE_ORCHESTRATOR: pm-odd.asi-review-risk="allow"\',`call site did not propagate: ${JSON.stringify(badFailures)}`);\n'
            "const goodFailures=[];\n"
            "runCallSite(clone(),(message)=>goodFailures.push(message));\n"
            'assert(goodFailures.length===0,`valid call site rejected: ${JSON.stringify(goodFailures)}`);\n'
            'console.log("production call site propagation controls passed");\n'
        )

    def test_always_pass_predicate_mutation_is_rejected(self):
        predicate = self.predicate_source()
        mutated = re.sub(r"return failures\s*\n\}", "return []\n}", predicate, count=1)
        self.assertNotEqual(mutated, predicate, "always-pass predicate mutation did not apply")
        result = self.run_script(
            r'''
const mutated=clone();
mutated["pm-odd"].permission.task["asi-review-risk"]="allow";
const failures=reviewDispatchFailures(mutated,relayReviewAgents,plainProviderReviewAgents);
assert(failures.length===1&&failures[0]==='REVIEW_TASK_GRANTED_OUTSIDE_ORCHESTRATOR: pm-odd.asi-review-risk="allow"',`always-pass predicate was not rejected: ${JSON.stringify(failures)}`);
''',
            predicate=mutated,
        )
        self.assertNotEqual(result.returncode, 0, "always-pass predicate satisfied the negative control")
        self.assertIn("always-pass predicate was not rejected", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
