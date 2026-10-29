import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const config = JSON.parse(readFileSync(new URL("../global-config/opencode.json", import.meta.url), "utf8"));
// verify-workflow.sh is a thin entry (queue Q04); its checks live in the manifest-listed verify/*.sh modules.
const verifierEntry = readFileSync(new URL("../verify-workflow.sh", import.meta.url), "utf8");
const moduleNames = [...verifierEntry.matchAll(/^\s*"([^ "]+) [0-9a-f]{64}"/gm)].map((m) => m[1]);
assert.ok(moduleNames.length > 10, "verifier manifest lists its modules");
const verifier = [verifierEntry, ...moduleNames.map((name) => readFileSync(new URL(`../verify/${name}`, import.meta.url), "utf8"))].join("\n");
const permissionBlock = verifier.slice(verifier.indexOf("const registeredHostReads=["), verifier.indexOf("function reviewAgentLockdownFailures("));
assert.doesNotThrow(() => new Function(permissionBlock), "extracted verifier permission block must parse");
const functionNames = [
  "hostReviewAssessFailures",
  "hostReviewDiffReadFailures",
  "hostReviewPipelineRunFailures",
  "hostReviewPersistFailures",
  "hostReviewNewGlobalDefaultFailures",
  "hostReviewNewToolFailures",
  "hostReviewPipelineRunExceptionFailures",
  "hostReviewNewGrantSweepFailures",
  "hostTestRunGlobalDefaultFailures",
  "hostPlanWriteGlobalDefaultFailures",
  "hostTestRunOrchestratorFailures",
  "hostPlanWriteOrchestratorFailures",
  "hostTestRunGrantSweepFailures",
  "hostToolPromptFailures",
];

function extractFunction(name) {
  const start = verifier.indexOf(`function ${name}(`);
  assert.notEqual(start, -1, `missing verifier function ${name}`);
  const brace = verifier.indexOf("{", start);
  let depth = 0;
  for (let index = brace; index < verifier.length; index += 1) {
    if (verifier[index] === "{") depth += 1;
    if (verifier[index] === "}") depth -= 1;
    if (depth === 0) return verifier.slice(start, index + 1);
  }
  throw new Error(`unterminated verifier function ${name}`);
}

const gatedSource = verifier.split("const gatedHostMutations=[", 2)[1].split("]", 1)[0];
const gated = [...gatedSource.matchAll(/"([^"]+)"/g)].map((match) => match[1]);

// The production coordinator set is a declaration, not a function. Extract it
// (and its pmAgents dependency) from the verifier so the isolated program cannot
// drift from the real generic set.
function extractDeclaration(name) {
  const start = verifier.indexOf(`const ${name}=`);
  assert.notEqual(start, -1, `missing verifier declaration ${name}`);
  const end = verifier.indexOf("\n", start);
  return verifier.slice(start, end === -1 ? verifier.length : end);
}
const declarations = ["pmAgents", "coordinatorAgents"].map(extractDeclaration).join("\n");
assert.ok(
  declarations.includes('const coordinatorAgents=["gentle-orchestrator",...pmAgents]'),
  "coordinatorAgents must derive from the shared pmAgents declaration",
);

const source = declarations + "\n" + functionNames.map(extractFunction).join("\n");
const cfgPerm = (agent, tool) => agent?.permission?.[tool];
const show = (value) => JSON.stringify(value);
const checks = new Function("cfgPerm", "show", `${source}\nreturn {${functionNames.join(",")}};`)(cfgPerm, show);
const { agent, permission: globalPermissions } = config;
const allowedAgents = ["gentle-orchestrator", "pm-odd", "pm-systematic"];

assert.equal(globalPermissions.host_review_pipeline_run, "deny");
assert.equal(globalPermissions.host_review_persist, "deny");
assert.equal(globalPermissions.host_review_assess, "deny");
assert.equal(globalPermissions.host_review_diff_read, "deny");
for (const name of allowedAgents) {
  assert.deepEqual(checks.hostReviewAssessFailures(name, agent[name]), []);
  assert.deepEqual(checks.hostReviewDiffReadFailures(name, agent[name]), []);
  assert.deepEqual(checks.hostReviewPipelineRunFailures(name, agent[name]), []);
  assert.deepEqual(checks.hostReviewPersistFailures(name, agent[name]), []);
}
for (const name of ["pm-odd", "pm-systematic"]) {
  assert.deepEqual(checks.hostReviewNewToolFailures(name, agent[name]), []);
  assert.equal(agent[name].tools.host_review_assess, true);
}
assert.deepEqual(checks.hostReviewNewGlobalDefaultFailures("host_review_pipeline_run", globalPermissions.host_review_pipeline_run), []);
assert.deepEqual(checks.hostReviewNewGlobalDefaultFailures("host_review_persist", globalPermissions.host_review_persist), []);
assert.deepEqual(checks.hostReviewNewGlobalDefaultFailures("host_review_assess", globalPermissions.host_review_assess), []);
assert.deepEqual(checks.hostReviewNewGlobalDefaultFailures("host_review_diff_read", globalPermissions.host_review_diff_read), []);
assert.deepEqual(checks.hostReviewPipelineRunExceptionFailures(gated, agent["gentle-orchestrator"]), []);
assert.deepEqual(checks.hostReviewNewGrantSweepFailures(agent), []);

for (const tool of ["host_review_assess", "host_review_diff_read", "host_review_pipeline_run", "host_review_persist"]) {
  assert.equal(globalPermissions[tool], "deny");
  assert.equal(checks.hostReviewNewGlobalDefaultFailures(tool, "allow").length, 1, `${tool} global-default control is vacuous`);
  assert.equal(checks.hostReviewNewGrantSweepFailures({ fourth: { permission: { [tool]: "allow" } } }).length, 1, `${tool} negative-sweep control is vacuous`);
}
assert.equal(checks.hostReviewAssessFailures("omitted", { permission: {} }).length, 1, "assess omission control is vacuous");
assert.equal(checks.hostReviewAssessFailures("wrong", { permission: { host_review_assess: "ask" } }).length, 1, "assess value control is vacuous");
assert.equal(checks.hostReviewDiffReadFailures("omitted", { permission: {} }).length, 1, "diff-read omission control is vacuous");
assert.equal(checks.hostReviewDiffReadFailures("wrong", { permission: { host_review_diff_read: "ask" } }).length, 1, "diff-read value control is vacuous");
assert.equal(checks.hostReviewPipelineRunFailures("omitted", { permission: {} }).length, 1, "pipeline omission control is vacuous");
assert.equal(checks.hostReviewPipelineRunFailures("wrong", { permission: { host_review_pipeline_run: "ask" } }).length, 1, "pipeline value control is vacuous");
assert.equal(checks.hostReviewPersistFailures("omitted", { permission: {} }).length, 1, "persist omission control is vacuous");
assert.equal(checks.hostReviewPersistFailures("wrong", { permission: { host_review_persist: "allow" } }).length, 1, "persist value control is vacuous");
assert.equal(checks.hostReviewNewToolFailures("omitted", { tools: {} }).length, 4, "tool omission control is vacuous");
for (const tool of ["host_review_assess", "host_review_diff_read", "host_review_pipeline_run", "host_review_persist"]) {
  assert.ok(checks.hostReviewNewToolFailures("disabled", { tools: { [tool]: false } }).some((failure) => failure.endsWith(tool)), `${tool} tool-value control is vacuous`);
}
assert.equal(checks.hostReviewPipelineRunExceptionFailures(gated.filter((name) => name !== "host_review_pipeline_run"), { permission: { host_review_pipeline_run: "allow" } }).length, 1, "exception omission control is vacuous");
assert.equal(checks.hostReviewPipelineRunExceptionFailures(gated, { permission: { host_review_pipeline_run: "ask" } }).length, 1, "exception value control is vacuous");

// Q90 T3a1: host_plan_write / host_test_run fixed-tool grants.
assert.equal(globalPermissions.host_test_run, "deny");
assert.equal(globalPermissions.host_plan_write, "deny");
const orchestrator = agent["gentle-orchestrator"];
assert.equal(orchestrator.permission.host_test_run, "allow");
assert.equal(orchestrator.permission.host_plan_write, "ask");
for (const [name, configured] of Object.entries(agent)) {
  if (name === "gentle-orchestrator") continue;
  if (configured.permission && "host_test_run" in configured.permission) assert.equal(configured.permission.host_test_run, "deny", `${name} must deny host_test_run`);
}
for (const tools of [config.tools ?? {}, ...Object.values(agent).map((entry) => entry.tools ?? {})]) {
  for (const key of ["host_test_run", "host_plan_write"]) assert.ok(!(key in tools), `host tool ${key} must not be a tools-map key`);
}
assert.deepEqual(checks.hostTestRunGlobalDefaultFailures(globalPermissions.host_test_run), []);
assert.deepEqual(checks.hostPlanWriteGlobalDefaultFailures(globalPermissions.host_plan_write), []);
assert.deepEqual(checks.hostTestRunOrchestratorFailures(orchestrator), []);
assert.deepEqual(checks.hostPlanWriteOrchestratorFailures(orchestrator), []);
assert.deepEqual(checks.hostTestRunGrantSweepFailures(agent), []);
const removed = JSON.parse(JSON.stringify(orchestrator));
delete removed.permission.host_test_run;
delete removed.permission.host_plan_write;
assert.ok(checks.hostTestRunOrchestratorFailures(removed).includes('ORCHESTRATOR_HOST_TEST_RUN_NOT_ALLOW: undefined'), "missing test-run grant control is vacuous");
assert.ok(checks.hostPlanWriteOrchestratorFailures(removed).includes('ORCHESTRATOR_HOST_PLAN_WRITE_NOT_ASK: undefined'), "missing plan-write grant control is vacuous");
assert.ok(checks.hostTestRunOrchestratorFailures({ permission: { host_test_run: "ask" } }).includes('ORCHESTRATOR_HOST_TEST_RUN_NOT_ALLOW: "ask"'), "test-run ask control is vacuous");
assert.ok(checks.hostPlanWriteOrchestratorFailures({ permission: { host_plan_write: "allow" } }).includes('ORCHESTRATOR_HOST_PLAN_WRITE_NOT_ASK: "allow"'), "plan-write allow control is vacuous");
assert.ok(checks.hostTestRunGlobalDefaultFailures("allow").includes('HOST_TEST_RUN_GLOBAL_DEFAULT_NOT_DENY: "allow"'), "test-run global allow control is vacuous");
assert.ok(checks.hostPlanWriteGlobalDefaultFailures("ask").includes('HOST_PLAN_WRITE_GLOBAL_DEFAULT_NOT_DENY: "ask"'), "plan-write global ask control is vacuous");
for (const name of ["pm-odd", "general", "odd-apply", "gentle-ai-worker", "review-risk", "advisor-security-pre", "synthetic-agent"]) {
  for (const value of ["ask", "allow"]) assert.ok(checks.hostTestRunGrantSweepFailures({ [name]: { permission: { host_test_run: value } } }).includes(`HOST_TEST_RUN_GRANTED_OUTSIDE_ORCHESTRATOR: ${name}="${value}"`), `test-run sweep control missed ${name}=${value}`);
}
assert.deepEqual(checks.hostToolPromptFailures(orchestrator.prompt), []);
for (const fragment of [
  "may draft plan documents through the ask-gated `host_plan_write` fixed tool",
  "plan documents only, never code or configuration",
  "narrowly defined, pre-registered tests through the allow-gated `host_test_run` fixed tool",
  "never arbitrary caller argv, pipes, redirects, or shell",
  "a failed or unavailable test run is evidence, never permission to widen authority",
  "`host_test_run` is not implemented in the current surface and remains inert until the host tool ships",
]) {
  const mutated = orchestrator.prompt.replace(fragment, "removed");
  assert.notEqual(mutated, orchestrator.prompt, `fragment absent: ${fragment}`);
  assert.ok(checks.hostToolPromptFailures(mutated).includes(`HOST_TOOL_PROMPT_CLAUSE_MISSING: ${JSON.stringify(fragment)}`), `prompt removal control is vacuous: ${fragment}`);
}


for (const name of allowedAgents) {
  console.log(`${name}: diff_read=${agent[name].permission.host_review_diff_read} assess=${agent[name].permission.host_review_assess} pipeline_run=${agent[name].permission.host_review_pipeline_run} persist=${agent[name].permission.host_review_persist}`);
}
console.log(`sample others default: general diff_read=${agent.general.permission.host_review_diff_read ?? globalPermissions.host_review_diff_read} assess=${agent.general.permission.host_review_assess ?? globalPermissions.host_review_assess} pipeline_run=${agent.general.permission.host_review_pipeline_run ?? globalPermissions.host_review_pipeline_run} persist=${agent.general.permission.host_review_persist ?? globalPermissions.host_review_persist}`);
console.log("Extracted verifier assertions passed; all new-key positive controls detected their reverted fixtures.");
