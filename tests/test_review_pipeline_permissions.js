import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const config = JSON.parse(readFileSync(new URL("../global-config/opencode.json", import.meta.url), "utf8"));
const verifier = readFileSync(new URL("../verify-workflow.sh", import.meta.url), "utf8");
const permissionBlock = verifier.slice(verifier.indexOf("const registeredHostReads=["), verifier.indexOf("function reviewAgentLockdownFailures("));
assert.doesNotThrow(() => new Function(permissionBlock), "extracted verifier permission block must parse");
const functionNames = [
  "hostReviewPipelineRunFailures",
  "hostReviewPersistFailures",
  "hostReviewNewGlobalDefaultFailures",
  "hostReviewNewToolFailures",
  "hostReviewPipelineRunExceptionFailures",
  "hostReviewNewGrantSweepFailures",
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
const source = functionNames.map(extractFunction).join("\n");
const cfgPerm = (agent, tool) => agent?.permission?.[tool];
const show = (value) => JSON.stringify(value);
const checks = new Function("cfgPerm", "show", `${source}\nreturn {${functionNames.join(",")}};`)(cfgPerm, show);
const { agent, permission: globalPermissions } = config;
const allowedAgents = ["gentle-orchestrator", "pm-odd", "pm-systematic"];

assert.equal(globalPermissions.host_review_pipeline_run, "deny");
assert.equal(globalPermissions.host_review_persist, "deny");
for (const name of allowedAgents) {
  assert.deepEqual(checks.hostReviewPipelineRunFailures(name, agent[name]), []);
  assert.deepEqual(checks.hostReviewPersistFailures(name, agent[name]), []);
}
for (const name of ["pm-odd", "pm-systematic"]) {
  assert.deepEqual(checks.hostReviewNewToolFailures(name, agent[name]), []);
}
assert.deepEqual(checks.hostReviewNewGlobalDefaultFailures("host_review_pipeline_run", globalPermissions.host_review_pipeline_run), []);
assert.deepEqual(checks.hostReviewNewGlobalDefaultFailures("host_review_persist", globalPermissions.host_review_persist), []);
assert.deepEqual(checks.hostReviewPipelineRunExceptionFailures(gated, agent["gentle-orchestrator"]), []);
assert.deepEqual(checks.hostReviewNewGrantSweepFailures(agent), []);

for (const tool of ["host_review_pipeline_run", "host_review_persist"]) {
  assert.equal(globalPermissions[tool], "deny");
  assert.equal(checks.hostReviewNewGlobalDefaultFailures(tool, "allow").length, 1, `${tool} global-default control is vacuous`);
  assert.equal(checks.hostReviewNewGrantSweepFailures({ fourth: { permission: { [tool]: "allow" } } }).length, 1, `${tool} negative-sweep control is vacuous`);
}
assert.equal(checks.hostReviewPipelineRunFailures("omitted", { permission: {} }).length, 1, "pipeline omission control is vacuous");
assert.equal(checks.hostReviewPipelineRunFailures("wrong", { permission: { host_review_pipeline_run: "ask" } }).length, 1, "pipeline value control is vacuous");
assert.equal(checks.hostReviewPersistFailures("omitted", { permission: {} }).length, 1, "persist omission control is vacuous");
assert.equal(checks.hostReviewPersistFailures("wrong", { permission: { host_review_persist: "allow" } }).length, 1, "persist value control is vacuous");
assert.equal(checks.hostReviewNewToolFailures("omitted", { tools: {} }).length, 2, "tool omission control is vacuous");
for (const tool of ["host_review_pipeline_run", "host_review_persist"]) {
  assert.ok(checks.hostReviewNewToolFailures("disabled", { tools: { [tool]: false } }).some((failure) => failure.endsWith(tool)), `${tool} tool-value control is vacuous`);
}
assert.equal(checks.hostReviewPipelineRunExceptionFailures(gated.filter((name) => name !== "host_review_pipeline_run"), { permission: { host_review_pipeline_run: "allow" } }).length, 1, "exception omission control is vacuous");
assert.equal(checks.hostReviewPipelineRunExceptionFailures(gated, { permission: { host_review_pipeline_run: "ask" } }).length, 1, "exception value control is vacuous");

for (const name of allowedAgents) {
  console.log(`${name}: pipeline_run=${agent[name].permission.host_review_pipeline_run} persist=${agent[name].permission.host_review_persist}`);
}
console.log(`sample others default: general pipeline_run=${agent.general.permission.host_review_pipeline_run ?? globalPermissions.host_review_pipeline_run} persist=${agent.general.permission.host_review_persist ?? globalPermissions.host_review_persist}`);
console.log("Extracted verifier assertions passed; all new-key positive controls detected their reverted fixtures.");
