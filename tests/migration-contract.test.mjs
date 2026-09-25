import assert from "node:assert/strict"
import fs from "node:fs"
import test from "node:test"
import vm from "node:vm"

const read = (path) => fs.readFileSync(new URL(`../${path}`, import.meta.url), "utf8")
const openCode = JSON.parse(read("global-config/opencode.json"))
const systematic = JSON.parse(read("global-config/systematic.jsonc").replace(/^\s*\/\/.*$/gm, ""))
const fallback = JSON.parse(read("global-config/rate-limit-fallback.json"))
const verifier = read("verify-workflow.sh")
const astra = read("global-config/plugins/astra-sol-upgrade.ts")
const workflow = read("WORKFLOW.md")

const reference = (entry) =>
  typeof entry === "string" ? entry : `${entry.providerID}/${entry.modelID}`
const active = new Set([
  ...Object.values(openCode.agent).map((agent) => agent.model),
  ...Object.values(systematic.agents).map((agent) => agent.model),
  ...Object.values(systematic.categories).map((category) => category.model),
  "openai/gpt-6-astra", // Created at runtime from eligible Sol agents.
].filter(Boolean))

test("all reviewed Sol and Luna allocations use GPT-6", () => {
  for (const source of [JSON.stringify(openCode), JSON.stringify(systematic), JSON.stringify(fallback), astra, workflow]) {
    assert.doesNotMatch(source, /gpt-5\.6-(sol|luna)/)
  }
  assert(active.has("openai/gpt-6-sol"))
  assert(active.has("openai/gpt-6-luna"))
  for (const model of active) assert(fallback.fallbackModels[model], `no exact fallback for ${model}`)
})

test("every effective provider failure has an independent provider", () => {
  const goLuna = "opencode-go/gpt-6-luna"
  assert.equal(reference(fallback.fallbackModels["openai/gpt-6-luna"][0]), goLuna)
  for (const [name, agent] of Object.entries(openCode.agent)) {
    if (agent.model !== "openai/gpt-6-luna" || !fallback.agentFallbackModels[name]) continue
    assert.equal(reference(fallback.agentFallbackModels[name][0]), goLuna, `${name}: Luna override skips OpenCode Go`)
  }
  for (const [source, rule] of Object.entries(fallback.fallbackModels)) {
    const targets = rule.map(reference)
    assert.equal(new Set(targets).size, targets.length, `${source}: duplicate fallback`)
    assert(!targets.includes(source), `${source}: self-fallback`)
    assert(targets.some((target) => target.split("/")[0] !== source.split("/")[0]), `${source}: provider failure has no independent fallback`)
    assert(targets.every((target) => !/gpt-5\.6-(sol|luna)/.test(target)), `${source}: legacy fallback`)
  }
  assert.equal(reference(fallback.fallbackModels["openai/gpt-6-astra"][0]), "openai/gpt-6-sol")
  for (const name of ["frontend-apply", "frontend-dev", "frontend-dev-premium", "vision", "design-iterator"]) {
    const required = fallback.agentRequiredCapabilities[name]
    assert(required?.length, `${name}: capability rule missing`)
    assert(fallback.agentFallbackModels[name]?.some((entry) => required.every((cap) => entry.capabilities.includes(cap))), `${name}: no capable fallback`)
  }
  for (const name of ["review-risk", "review-resilience", "review-readability", "review-reliability", "review-refuter", "review-validator"]) {
    assert(fallback.excludeAgents.includes(name))
    assert(fallback.excludeAgents.includes(`asi-${name}`))
  }
})

test("primary reviews cross model families and both reviewer lanes retain diversity", () => {
  const source = verifier.match(/function normalizeModel\(value\) \{[\s\S]*?\n\}\n(?:\/\/[^\n]*\n)*function modelFamily\(value\) \{[\s\S]*?\n\}/)?.[0]
  assert(source, "runtime family classifier is missing")
  const family = vm.runInNewContext(`${source}\nmodelFamily`)
  assert.equal(family("openai/gpt-6-luna"), family("opencode-go/gpt-6-luna"))
  assert.equal(family("opencode-go/deepseek-v4.1-flash"), family("deepseek/deepseek-flash"))
  for (const [writer, reviewer] of [["general", "gentle-orchestrator"], ["sdd-apply", "sdd-verify"]]) {
    assert.notEqual(family(openCode.agent[writer].model), family(openCode.agent[reviewer].model), `${writer} and ${reviewer} share a model family`)
  }
  assert.equal(openCode.agent.general.model, "openai/gpt-6-luna")
  const gentleLenses = ["review-risk", "review-resilience", "review-readability", "review-reliability", "review-refuter", "review-validator"]
  const systematicBaseline = ["correctness-reviewer", "testing-reviewer", "project-standards-reviewer"]
  for (const [lane, models] of [
    ["Gentle AI", gentleLenses.map((name) => openCode.agent[name].model)],
    ["Systematic", systematicBaseline.map((name) => systematic.agents[name].model)],
  ]) {
    assert(new Set(models.map(family)).size >= 3, `${lane} reviewer spread fell below three families`)
  }
  assert.match(verifier, /PRIMARY_REVIEW_SAME_FAMILY/)
  assert.match(verifier, /REVIEW_FAMILY_SPREAD_INSUFFICIENT/)
})

test("public GitHub MCP is read only and restricted to research agents", () => {
  assert.deepEqual(openCode.mcp.github_ro, {
    type: "remote",
    url: "https://api.githubcopilot.com/mcp/",
    enabled: true,
    oauth: false,
    headers: {
      Authorization: "Bearer {env:GITHUB_REVIEW_TOKEN}",
      "X-MCP-Toolsets": "repos,pull_requests,issues",
      "X-MCP-Readonly": "true",
    },
  })
  assert.equal(openCode.tools["github_ro_*"], false)
  for (const name of ["gentle-orchestrator", "sdd-research"]) {
    assert.equal(openCode.agent[name].tools["github_ro_*"], true, `${name}: GitHub MCP not enabled`)
  }
  for (const [name, agent] of Object.entries(openCode.agent)) {
    if (!["gentle-orchestrator", "sdd-research"].includes(name)) {
      assert.notEqual(agent.tools?.["github_ro_*"], true, `${name}: unexpected GitHub access`)
    }
  }
  assert.equal(systematic.agents["repo-research-analyst"].tools["github_ro_*"], true)
  assert.match(verifier, /GITHUB_RO_RUNTIME_INACTIVE_OR_UNSCOPED/)
  assert.match(verifier, /GITHUB_RO_MUTATION_TOOL_EXPOSED/)
  assert.match(verifier, /GITHUB_RO_UNAUTHORIZED_AGENT_TOOL_EXPOSED/)
})

test("Astra and RDD retain the scoped user-choice contract", () => {
  assert.match(astra, /SOL_MODEL = "openai\/gpt-6-sol"/)
  assert.match(astra, /ASTRA_MODEL = "openai\/gpt-6-astra"/)
  assert.match(astra, /!isImplementationRoute\(name\)/)
  assert.match(verifier, /GENTLE_AI_V3_5_SYNC_NOT_CONFIRMED/)
  assert.match(verifier, /decided\\ by\\ \(default\|global\|clone-local\)/)
  assert.match(workflow, /Only the user may explicitly enable or disable RDD/)
  assert.match(workflow, /`unassessable`/)
  assert.match(workflow, /`targeted_validation_inconclusive`/)
  assert.match(read("global-config/skills/workflow-odd-secure/references/odd-and-review.md"), /Neither agent nor verifier toggles it/)
})
