import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


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
        "gentle-ai-verify-astra",
        "explore",
    ],
    "pm-systematic": [
        "gentle-ai-worker",
        "gentle-ai-worker-local",
        "gentle-ai-verify",
        "gentle-ai-verify-astra",
        "explore",
    ],
}
LEAF_DISPATCH_AGENTS = [
    "odd-apply",
    "gentle-ai-worker",
    "gentle-ai-worker-local",
    "gentle-ai-verify",
    "explore",
]


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
const familyModel=(family)=>family==="gpt"?"openai/gpt-6.1-sol":family==="deepseek"?"opencode-go/deepseek-v4.1-flash":"synthetic/no-family";
const independentRuntime={
  "general":{model:"openai/gpt-6-luna"},
  "gentle-orchestrator":{model:"opencode-go/deepseek-v4.1-flash"},
  "gentle-ai-worker":{model:"opencode-go/deepseek-v4.1-flash"},
  "gentle-ai-verify":{model:"openai/gpt-6-luna"},
  "pm-odd":{model:"openai/gpt-6-luna"},
  "odd-apply":{model:"opencode-go/deepseek-v4.1-flash"},
  "pm-systematic":{model:"openai/gpt-6-luna"},
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
        self.assertEqual(sum(len(v) for v in PM_REQUIRED_DISPATCH.values()), 11, "unexpected required dispatch lane inventory")
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
            "coverage-group-3-taskgraph: 40 controls passed",
            "coverage-group-4-family: 18 controls passed",
            "coverage-group-5-pmgeneral: 10 controls passed",
            "coverage-total: 103 controls passed",
        ):
            self.assertIn(marker, result.stdout)


if __name__ == "__main__":
    unittest.main()
