cat > "$RUNTIME_AGENT_CHECKER" <<'EOF_RUNTIME_AGENT'
const fs = require("fs")
const path = require("path")
const crypto = require("crypto")
const { execFileSync } = require("child_process")

const nodeModules = process.env.SYSTEMATIC_NODE_MODULES
if (!nodeModules) {
  console.error("   !! missing SYSTEMATIC_NODE_MODULES")
  process.exit(2)
}
let jsonc
try {
  jsonc = require(path.join(nodeModules, "jsonc-parser"))
} catch (error) {
  console.error(`   !! cannot load jsonc-parser from ${nodeModules}: ${error.message}`)
  process.exit(2)
}

const [systematicConfigPath, agentsRoot, agentListPath, debugDir, openCodeConfigPath, fallbackPolicySourcePath, workspaceRoot] = process.argv.slice(2)
const hasOwn = (obj, key) => Object.prototype.hasOwnProperty.call(obj ?? {}, key)
let failures = 0
function fail(msg) { console.error(`   !! ${msg}`); failures++ }
function show(value) { return value === undefined ? "<inherit/none>" : JSON.stringify(value) }
// R3-WORKSPACE-001 / R4-002: the 7th argument is the repository root used to
// resolve repo-relative inputs (notably the orchestrator prompt assembler).
// `path.join` throws on undefined/non-string and silently yields a relative
// path on "", so fail once here, before any use, and gate path construction on
// this flag instead of letting it throw.
const workspaceRootAvailable = typeof workspaceRoot === "string" && workspaceRoot.length > 0
if (!workspaceRootAvailable) {
  fail("WORKSPACE_ROOT_UNAVAILABLE: runtime checker requires a non-empty workspace root argument")
}

function parseJsonc(file) {
  const text = fs.readFileSync(file, "utf8")
  const errors = []
  const value = jsonc.parse(text, errors, { allowTrailingComma: true, disallowComments: false })
  if (errors.length) throw new Error(`${file}: JSONC parse error`)
  return value
}
function isDiscoverableMarkdown(name) { return name.endsWith(".md") && name.toLowerCase() !== "readme.md" }
function declaredTools(file) {
  const text = fs.readFileSync(file, "utf8")
  const fm = text.match(/^---\s*\n([\s\S]*?)\n---/)
  if (!fm) return []
  const m = fm[1].match(/^tools:\s*(.+)$/mi)
  return m ? m[1].split(",").map((x) => x.trim().toLowerCase()).filter(Boolean) : []
}
function walkAgents(root, current=root, out=[], depth=0) {
  if (!fs.existsSync(current) || depth > 2) return out
  for (const entry of fs.readdirSync(current, {withFileTypes:true})) {
    const full=path.join(current,entry.name)
    if (entry.isDirectory()) walkAgents(root,full,out,depth+1)
    else if (entry.isFile() && isDiscoverableMarkdown(entry.name)) {
      const rel=path.relative(root,full); const parts=rel.split(path.sep)
      const tools=declaredTools(full)
      out.push({name:path.basename(entry.name,".md"), category:parts.length>1?parts[0]:"", declaresMutation:tools.includes("edit")||tools.includes("write")})
    }
  }
  return out
}
function exactOverlay(config, agent) {
  const overlays=config.agents && typeof config.agents==="object" ? config.agents : {}
  const qualified=agent.category ? `${agent.category}/${agent.name}` : agent.name
  if (hasOwn(overlays,qualified)) return overlays[qualified]
  if (hasOwn(overlays,agent.name)) return overlays[agent.name]
  return undefined
}
function applyModelOverlay(state, overlay) {
  if (!overlay || typeof overlay!=="object" || Array.isArray(overlay)) return
  if (hasOwn(overlay,"model")) {
    if (!hasOwn(overlay,"variant")) state.variant=undefined
    state.model=overlay.model===null?undefined:overlay.model
  }
  if (hasOwn(overlay,"variant")) state.variant=overlay.variant==null?undefined:overlay.variant
  if (hasOwn(overlay,"disable")) state.disable=overlay.disable===true
}
function applyOpenCodeModelOverlay(state, overlay) {
  applyModelOverlay(state, overlay)
  applyModelOverlay(state, overlay?.opencode)
}
function expectedFor(config, agent) {
  const state={model:undefined,variant:undefined,disable:false}
  if (agent.category) applyOpenCodeModelOverlay(state, config.categories?.[agent.category])
  applyOpenCodeModelOverlay(state, exactOverlay(config,agent))
  const activeProfile=typeof config.profile==="string" ? config.profiles?.[config.profile] : undefined
  if (activeProfile && typeof activeProfile==="object" && !Array.isArray(activeProfile)) {
    if (agent.category) applyOpenCodeModelOverlay(state, activeProfile.categories?.[agent.category])
    applyOpenCodeModelOverlay(state, exactOverlay(activeProfile,agent))
  }
  const disabled=Array.isArray(config.disabled_agents)?config.disabled_agents:[]
  if (disabled.includes(agent.name) || (agent.category && disabled.includes(`${agent.category}/${agent.name}`))) state.disable=true
  return state
}
function normalizeModel(value) {
  if (typeof value==="string") return value
  if (value && typeof value==="object") {
    const provider=value.providerID ?? value.providerId
    const model=value.modelID ?? value.modelId
    if (typeof provider==="string" && typeof model==="string") return `${provider}/${model}`
  }
  return undefined
}
// Provider aliases do not establish review independence: OpenAI and Go Luna
// are the same family, as are direct and Go DeepSeek Flash.
function modelFamily(value) {
  const normalized=normalizeModel(value)?.toLowerCase()
  if (!normalized) return undefined
  // Owner-confirmed Kinver model-family mapping; provider identity avoids
  // misclassifying unrelated models that happen to use a generic model name.
  if (normalized.startsWith("kinver/")) return "qwen"
  const model=normalized.split("/").slice(1).join("/")
  if (/(^|\/)gpt-[0-9]/.test(model)) return "gpt"
  if (model.includes("deepseek")) return "deepseek"
  if (model.includes("glm-")) return "glm"
  if (model.includes("qwen")) return "qwen"
  if (model.includes("kimi")) return "kimi"
  if (model.includes("mimo")) return "mimo"
  if (model.includes("muse")) return "muse"
  if (model.includes("minimax")) return "minimax"
  if (model.includes("grok")) return "grok"
  if (model.includes("gemini")) return "gemini"
  if (model.includes("ling")) return "ling"
  if (model.includes("claude")) return "claude"
  return undefined
}
// supported-variant-validator:begin
// Staged by q90-t30-variants-u1 for the T3.0.2 activation gate; not called against live seats yet.
// Self-contained and marked for extraction. Full model IDs only; no root or plural provider shape.
// The allowed names are the owner/tracker target subset, not the full provider catalog.
const SUPPORTED_VARIANT_TARGETS = Object.freeze({
  "openai/gpt-6-luna": Object.freeze(["none","low","medium","high","xhigh","max"]),
  "opencode-go/glm-5.3-flash": Object.freeze(["low","high","max"]),
  "opencode-go/glm-5.3": Object.freeze(["low","high","max"]),
  "opencode-go/deepseek-v4.1-flash": Object.freeze(["low","high"]),
  "opencode-go/deepseek-v4.1-flash@worker": Object.freeze(["low","high","max"]),
  "opencode-go/deepseek-v4-pro": Object.freeze(["high"]),
  "opencode-go/claude-haiku-5-5": Object.freeze(["high"]),
  "opencode-go/ling-3.1-flash": Object.freeze([]),
  "opencode-go/minimax-m3.1-flash": Object.freeze(["high","xhigh"]),
  "opencode-go/qwen3.8-flash": Object.freeze([]),
  "opencode-go/qwen3.8-max": Object.freeze([]),
  "opencode-go/kimi-k2.7-code": Object.freeze([]),
  "opencode-go/mimo-v2.6-flash": Object.freeze([]),
  "google/gemini-flash-latest": Object.freeze([]),
  "google/gemini-4-argon": Object.freeze([]),
})
function variantValueType(value) {
  if (value === null) return "null"
  if (Array.isArray(value)) return "array"
  return typeof value
}
function supportedVariantFailure(model, variant) {
  if (typeof model !== "string" || model.length === 0) {
    return `SUPPORTED_VARIANT_MODEL_INVALID: model=${JSON.stringify(model)} variant=${JSON.stringify(variant)}`
  }
  if (variant === undefined) return undefined
  if (typeof variant === "string" && variant === "") {
    return `SUPPORTED_VARIANT_EMPTY_REFUSED: model=${model} variant=""`
  }
  if (typeof variant !== "string") {
    return `SUPPORTED_VARIANT_TYPE_REFUSED: model=${model} variantType=${variantValueType(variant)} variant=${JSON.stringify(variant)}`
  }
  const names = Object.prototype.hasOwnProperty.call(SUPPORTED_VARIANT_TARGETS, model) ? SUPPORTED_VARIANT_TARGETS[model] : undefined
  if (names === undefined) {
    return `SUPPORTED_VARIANT_MODEL_UNCLASSIFIED: model=${model} variant=${JSON.stringify(variant)}`
  }
  if (!names.includes(variant)) {
    return `SUPPORTED_VARIANT_UNKNOWN_REFUSED: model=${model} variant=${JSON.stringify(variant)}`
  }
  return undefined
}
// supported-variant-validator:end
function promptBudgetFailures(agents) {
  const failures=[]
  for (const [name,agent] of Object.entries(agents??{})) {
    const prompt=agent?.prompt
    if (typeof prompt!=="string") continue
    // The owner's cap is characters, not UTF-16 code units, so astral text is
    // measured by code point to agree with Python `len(prompt)`.
    const size=Array.from(prompt).length
    console.log(`   prompt-size: ${name}=${size}`)
    if (name.startsWith("pm-") && size>=6000) failures.push(`PM_PROMPT_SIZE_CAP_EXCEEDED: ${name}=${size}`)
  }
  return failures
}
const debugCache = new Map()

function stripAnsi(text) {
  return text.replace(/\x1B\[[0-?]*[ -\/]*[@-~]/g, "")
}

// `opencode debug agent` writes the agent JSON to stdout, but plugins loaded
// during startup may also write informational lines to stdout before it. Treat
// stdout as a mixed diagnostic stream rather than assuming the whole file is
// JSON. Extract a balanced top-level JSON object whose shape is the debug-agent
// payload. This deliberately does not suppress or reinterpret plugin chatter.
function parseDebugAgentStream(text) {
  const clean = stripAnsi(text)

  // Fast path for runtimes with clean stdout.
  try {
    const value = JSON.parse(clean.trim())
    if (value && typeof value === "object" && !Array.isArray(value) && value.tools && typeof value.tools === "object") return value
  } catch {}

  const starts = []
  const lineStart = /(?:^|\n)[\t ]*\{/g
  let match
  while ((match = lineStart.exec(clean)) !== null) {
    const brace = clean.indexOf("{", match.index)
    if (brace >= 0) starts.push(brace)
  }

  // Fallback for a runtime/plugin that writes a prefix and JSON on one line.
  if (starts.length === 0) {
    for (let i = 0; i < clean.length; i++) if (clean[i] === "{") starts.push(i)
  }

  for (const start of starts) {
    let depth = 0
    let inString = false
    let escaped = false
    for (let i = start; i < clean.length; i++) {
      const ch = clean[i]
      if (inString) {
        if (escaped) escaped = false
        else if (ch === "\\") escaped = true
        else if (ch === '"') inString = false
        continue
      }
      if (ch === '"') { inString = true; continue }
      if (ch === "{") depth++
      else if (ch === "}") {
        depth--
        if (depth === 0) {
          try {
            const value = JSON.parse(clean.slice(start, i + 1))
            if (value && typeof value === "object" && !Array.isArray(value) && value.tools && typeof value.tools === "object") return value
          } catch {}
          break
        }
      }
    }
  }
  return undefined
}

function readDebug(name) {
  if (debugCache.has(name)) return debugCache.get(name)
  const file=path.join(debugDir,`${name}.json`)
  if (!fs.existsSync(file)) {
    fail(`RUNTIME_AGENT_PROBE_MISSING: no debug-agent stdout for ${name}`)
    debugCache.set(name, undefined)
    return undefined
  }
  const raw=fs.readFileSync(file,"utf8")
  const value=parseDebugAgentStream(raw)
  if (!value) {
    const preview=stripAnsi(raw).replace(/\s+/g," ").trim().slice(0,180)
    fail(`RUNTIME_AGENT_PROBE_INVALID: ${name}: no debug-agent JSON object found in mixed stdout${preview ? `; prefix=${JSON.stringify(preview)}` : ""}`)
    debugCache.set(name, undefined)
    return undefined
  }
  debugCache.set(name, value)
  return value
}
function tool(debug, name) { return debug?.tools && typeof debug.tools==="object" ? debug.tools[name] : undefined }

// `opencode debug agent` exposes both the agent permission ruleset and a
// convenience tools map. The ruleset is authoritative for built-ins whose tool
// id differs from the permission they request. In particular current OpenCode
// maps edit/write/apply_patch to permission "edit"; apply_patch itself asks for
// permission "edit". Do not infer host-write authority from tools.apply_patch.
function wildcardMatch(value, pattern) {
  if (pattern === "*") return true
  if (typeof value !== "string" || typeof pattern !== "string") return false
  const escaped = pattern.replace(/[.+?^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*")
  return new RegExp(`^${escaped}$`).test(value)
}
function permissionRules(debug) {
  return Array.isArray(debug?.permission) ? debug.permission : []
}
function matchingPermissionRules(debug, permission) {
  return permissionRules(debug).filter((rule) =>
    rule && typeof rule === "object" &&
    typeof rule.permission === "string" &&
    wildcardMatch(permission, rule.permission)
  )
}
function assertPermissionFullyDenied(debug, permission, label) {
  const rules = matchingPermissionRules(debug, permission)
  let lastWildcardDeny = -1
  for (let i = 0; i < rules.length; i++) {
    const rule = rules[i]
    if (rule.pattern === "*" && rule.action === "deny") lastWildcardDeny = i
  }
  if (lastWildcardDeny < 0) {
    fail(`${label}: resolved permission.${permission} has no unconditional deny`)
    return false
  }
  const laterEscape = rules.slice(lastWildcardDeny + 1).find((rule) => rule.action !== "deny")
  if (laterEscape) {
    fail(`${label}: resolved permission.${permission} is re-opened after its wildcard deny by ${JSON.stringify(laterEscape)}`)
    return false
  }
  return true
}
function permissionActionForWildcard(debug, permission) {
  const rules = matchingPermissionRules(debug, permission)
  for (let i = rules.length - 1; i >= 0; i--) {
    const rule = rules[i]
    if (rule.pattern === "*") return rule.action
  }
  return undefined
}
function permissionActionForValue(debug, permission, value) {
  let action
  for (const rule of permissionRules(debug)) {
    if (!rule || typeof rule!=="object") continue
    if (!wildcardMatch(permission, rule.permission)) continue
    if (!wildcardMatch(value, rule.pattern)) continue
    action=rule.action
  }
  return action
}

let systematic, deployed
try { systematic=parseJsonc(systematicConfigPath); deployed=JSON.parse(fs.readFileSync(openCodeConfigPath,"utf8")) }
catch (error) { console.error(`   !! ${error.message}`); process.exit(1) }
const inventory=walkAgents(agentsRoot).sort((a,b)=>a.name.localeCompare(b.name))
const byName=new Map(inventory.map((a)=>[a.name,a]))

const listText=fs.readFileSync(agentListPath,"utf8")
const runtimeNames=new Set()
for (const line of listText.split(/\r?\n/)) {
  const m=line.match(/^(\S+) \((?:primary|subagent|all)\)$/)
  if (m) runtimeNames.add(m[1])
}
for (const agent of inventory) {
  const expected=expectedFor(systematic,agent)
  if (expected.disable) {
    if (runtimeNames.has(agent.name)) fail(`SYSTEMATIC_DISABLED_AGENT_PRESENT: ${agent.name}`)
  } else if (!runtimeNames.has(agent.name)) {
    fail(`SYSTEMATIC_RUNTIME_MISSING: ${agent.name} is absent from opencode agent list`)
  }
}

const deployedAgents=deployed.agent && typeof deployed.agent==="object" ? deployed.agent : {}
const gp=deployed.permission && typeof deployed.permission==="object" ? deployed.permission : {}
if (gp.grep!=="ask") fail(`GLOBAL_GREP_POLICY_CHANGED: expected ask, got ${show(gp.grep)}`)
for (const [name,agent] of Object.entries(deployedAgents)) {
  if (!agent || typeof agent!=="object" || agent.mode!=="subagent") continue
  if (agent.tools?.grep!==false) fail(`SUBAGENT_NATIVE_GREP_TOOL_EXPOSED: ${name}`)
  if (agent.permission?.grep!=="deny") fail(`SUBAGENT_NATIVE_GREP_NOT_DENIED: ${name}`)
  const repoCapable=agent.tools?.["*"]!==false &&
    (agent.tools?.read===true || agent.tools?.sandbox_read===true)
  if (repoCapable && (typeof agent.prompt!=="string" || !agent.prompt.includes("<!-- user:subagent-search-contract -->"))) {
    fail(`SUBAGENT_SEARCH_PROMPT_CONTRACT_MISSING: ${name}`)
  }
}
for (const category of ["workflow","research","review","document-review","design"]) {
  if (systematic.categories?.[category]?.permission?.grep!=="deny") {
    fail(`SYSTEMATIC_CATEGORY_NATIVE_GREP_NOT_DENIED: ${category}`)
  }
}
for (const name of ["asi-review-risk","asi-review-resilience","asi-review-readability","asi-review-reliability","asi-review-refuter","asi-review-validator"]) {
  if (!runtimeNames.has(name)) fail(`RELAY_RUNTIME_AGENT_MISSING: ${name}`)
}
for (const name of Object.keys(deployedAgents)) {
  if (name.endsWith("-astra")) fail(`ASTRA_ALIAS_MUST_NOT_BE_PINNED_IN_OPENCODE_CONFIG: ${name}`)
}
for (const agent of inventory) {
  if (hasOwn(deployedAgents,agent.name)) fail(`SYSTEMATIC_AGENT_SHADOWED: opencode.json defines ${agent.name}; remove it and use systematic.jsonc overlay instead`)
}

const mutators=inventory.filter((a)=>a.declaresMutation)
const controlNames=[...new Set([
  ...mutators.map((a)=>a.name),
  "correctness-reviewer", "testing-reviewer", "repo-research-analyst",
  "adversarial-document-reviewer",
  // Model-sensitive specialist assignments: runtime must match systematic.jsonc.
  "api-contract-reviewer", "architecture-strategist", "reliability-reviewer",
  "data-migrations-reviewer", "deployment-verification-agent",
  "feasibility-reviewer", "design-iterator", "adversarial-reviewer",
  "security-reviewer", "security-lens-reviewer",
])].filter((name)=>byName.has(name))
const reviewedProfileNames=systematic.profiles && typeof systematic.profiles==="object" && !Array.isArray(systematic.profiles)
  ? Object.keys(systematic.profiles)
  : []
let compatibleRuntimeProfiles=new Set(["base",...reviewedProfileNames])
function expectedForProfile(profileName, agent) {
  const candidate={...systematic}
  if (profileName==="base") delete candidate.profile
  else candidate.profile=profileName
  return expectedFor(candidate,agent)
}
for (const name of controlNames) {
  const agent=byName.get(name); const actual=readDebug(name)
  if (!actual) continue
  const model=normalizeModel(actual.model)
  const variant=typeof actual.variant==="string" ? actual.variant : undefined
  const matchingProfiles=[...compatibleRuntimeProfiles].filter((profileName)=>{
    const expected=expectedForProfile(profileName,agent)
    return model===expected.model && variant===expected.variant
  })
  if (matchingProfiles.length===0) {
    const allowed=["base",...reviewedProfileNames].map((profileName)=>{
      const expected=expectedForProfile(profileName,agent)
      return `${profileName}:${show(expected.model)}@${show(expected.variant)}`
    })
    fail(`SYSTEMATIC_RUNTIME_ROUTING_MISMATCH: ${name}: runtime=${show(model)}@${show(variant)} allowed=${allowed.join(",")}`)
  } else {
    compatibleRuntimeProfiles=new Set(matchingProfiles)
  }
  // Built-in edit/write/apply_patch all execute under permission "edit".
  // Validate the resolved permission ruleset, not individual debug-tool booleans.
  assertPermissionFullyDenied(actual, "edit", `SYSTEMATIC_HOST_EDIT_NOT_DENIED: ${name}`)
  if (permissionActionForWildcard(actual,"grep")!=="deny" || tool(actual,"grep")===true) {
    fail(`SYSTEMATIC_NATIVE_GREP_EXPOSED: ${name}`)
  }
  if (agent.declaresMutation) {
    if (tool(actual,"bash")!==false && permissionActionForWildcard(actual,"bash")!=="deny") {
      fail(`SYSTEMATIC_HOST_BASH_EXPOSED: ${name}.bash is not denied`)
    }
    for (const t of ["sandbox_read","sandbox_list","sandbox_grep","sandbox_diff","sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch"]) {
      if (tool(actual,t)!==true) fail(`SYSTEMATIC_SANDBOX_TOOL_MISSING: ${name}.${t} is not enabled at runtime`)
    }
  }
  const memoryExpected = {
    workflow: true,
    research: false,
    design: false,
    review: false,
    "document-review": false,
  }[agent.category]
  if (memoryExpected === undefined) {
    fail(`SYSTEMATIC_MEMORY_RUNTIME_UNCLASSIFIED_CATEGORY: ${agent.category || "<uncategorized>"} for ${name}`)
  } else if (tool(actual,"ctx_memory") !== memoryExpected) {
    fail(`SYSTEMATIC_MEMORY_RUNTIME_MISMATCH: ${name} (${agent.category}) ctx_memory expected ${memoryExpected}, got ${show(tool(actual,"ctx_memory"))}`)
  }
}
if (compatibleRuntimeProfiles.size===0) {
  fail("SYSTEMATIC_RUNTIME_PROFILE_MIXED: runtime agents do not resolve from one reviewed base/profile routing")
} else {
  console.log(`   ok: runtime Systematic routing matches reviewed profile candidate(s): ${[...compatibleRuntimeProfiles].join(",")}`)
}

const SOL_MODEL="openai/gpt-6.1-sol"
const ASTRA_MODEL="openai/gpt-6-astra"
const ASTRA_SUFFIX="-astra"
function isImplementationRoute(name) {
  return name==="general" ||
    name==="jd-fix-agent" ||
    name==="design-iterator" ||
    name==="bug-reproduction-validator" ||
    name==="pr-comment-resolver" ||
    name==="systematic-implementer" ||
    /(^|-)apply($|-)/.test(name) ||
    /(^|-)implement(er|ation)?($|-)/.test(name)
}
// Native review actors never receive an Astra alias (matches astra-sol-upgrade.ts).
function isReviewActor(name) {
  return /^(asi-)?review-(risk|resilience|readability|reliability|refuter|validator)$/.test(name)
}
function sameResolvedSurface(base, alias, baseName, aliasName, field) {
  if (JSON.stringify(base?.[field])!==JSON.stringify(alias?.[field])) {
    fail(`ASTRA_ALIAS_SURFACE_MISMATCH: ${aliasName}.${field} differs from ${baseName}`)
  }
}
function ruleWitness(pattern, fallback) {
  if (typeof pattern!=="string" || !pattern) return fallback
  return pattern.includes("*") ? pattern.replace(/\*/g,"__astra_probe__") : pattern
}
function assertEquivalentPermissions(base, alias, baseName, aliasName) {
  const baseRules=permissionRules(base)
  const aliasRules=permissionRules(alias)
  const knownPermissions=[
    "bash","read","edit","write","glob","grep","list","webfetch","websearch",
    "task","todowrite","question","plan_enter","plan_exit","doom_loop",
    "external_directory","lsp","skill","ctx_search","ctx_expand","ctx_memory",
    "host_register_project","sandbox_read","sandbox_list","sandbox_grep","sandbox_diff",
    "sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch","sandbox_apply",
    "sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_finish",
  ]
  const permissions=new Set([
    ...knownPermissions,
    ...Object.keys(base?.tools??{}),
    ...Object.keys(alias?.tools??{}),
  ])
  for (const rule of [...baseRules,...aliasRules]) {
    if (typeof rule?.permission==="string") permissions.add(ruleWitness(rule.permission,"__astra_permission_probe__"))
  }

  const differences=[]
  for (const permission of permissions) {
    const targets=new Set(["__astra_target_probe__"])
    for (const rule of [...baseRules,...aliasRules]) {
      if (!rule || typeof rule!=="object" || typeof rule.pattern!=="string") continue
      if (!wildcardMatch(permission,rule.permission)) continue
      targets.add(ruleWitness(rule.pattern,"__astra_target_probe__"))
      if (!rule.pattern.includes("*")) targets.add(rule.pattern)
    }
    for (const target of targets) {
      const baseAction=permissionActionForValue(base,permission,target)
      const aliasAction=permissionActionForValue(alias,permission,target)
      if (baseAction!==aliasAction) {
        differences.push({permission,target,base:baseAction??"<none>",alias:aliasAction??"<none>"})
        if (differences.length>=12) break
      }
    }
    if (differences.length>=12) break
  }
  if (differences.length) {
    fail(`ASTRA_ALIAS_EFFECTIVE_PERMISSION_MISMATCH: ${aliasName} differs from ${baseName}; samples=${JSON.stringify(differences)}`)
  }
}

const eligibleSolBases=new Set()
for (const [name,agent] of Object.entries(deployedAgents)) {
  if (agent && typeof agent==="object" && agent.disable!==true && agent.mode!=="primary" &&
      normalizeModel(agent.model)===SOL_MODEL && !isImplementationRoute(name) && !isReviewActor(name)) eligibleSolBases.add(name)
}
for (const agent of inventory) {
  const expected=expectedFor(systematic,agent)
  if (!expected.disable && expected.model===SOL_MODEL && !isImplementationRoute(agent.name) && !isReviewActor(agent.name)) eligibleSolBases.add(agent.name)
}

const runtimeAstraAliases=[...runtimeNames].filter((name)=>name.endsWith(ASTRA_SUFFIX)).sort()
const expectedAstraAliases=[...eligibleSolBases].sort().map((name)=>`${name}${ASTRA_SUFFIX}`)
for (const alias of runtimeAstraAliases) {
  const baseName=alias.slice(0,-ASTRA_SUFFIX.length)
  if (isImplementationRoute(baseName)) fail(`ASTRA_IMPLEMENTATION_ALIAS_FORBIDDEN: ${alias}`)
  if (!eligibleSolBases.has(baseName)) fail(`ASTRA_ALIAS_WITHOUT_ELIGIBLE_SOL_BASE: ${alias}`)
}
for (const alias of expectedAstraAliases) {
  if (!runtimeNames.has(alias)) fail(`ASTRA_RUNTIME_ALIAS_MISSING: ${alias}`)
}

const runtimeOrchestrator=readDebug("gentle-orchestrator")
for (const baseName of [...eligibleSolBases].sort()) {
  const aliasName=`${baseName}${ASTRA_SUFFIX}`
  const base=readDebug(baseName)
  const alias=readDebug(aliasName)
  if (!base || !alias) continue
  if (normalizeModel(base.model)!==SOL_MODEL) {
    fail(`ASTRA_BASE_NOT_SOL_AT_RUNTIME: ${baseName}=${show(normalizeModel(base.model))}`)
  }
  if (normalizeModel(alias.model)!==ASTRA_MODEL || alias.variant!=="xhigh") {
    fail(`ASTRA_ALIAS_MODEL_INVALID: ${aliasName}=${show(normalizeModel(alias.model))}@${show(alias.variant)}`)
  }
  if (alias.hidden!==true) fail(`ASTRA_ALIAS_NOT_HIDDEN: ${aliasName}`)
  for (const field of ["prompt","tools","mode"]) sameResolvedSurface(base,alias,baseName,aliasName,field)
  assertEquivalentPermissions(base,alias,baseName,aliasName)
  assertPermissionFullyDenied(alias,"edit",`ASTRA_ALIAS_HOST_EDIT_NOT_DENIED: ${aliasName}`)
  if (permissionActionForValue(runtimeOrchestrator,"task",aliasName)!=="allow") {
    fail(`ASTRA_ALIAS_NOT_ALLOWED_BY_ORCHESTRATOR: ${aliasName}`)
  }
}
if (eligibleSolBases.size===0) fail("ASTRA_NO_ELIGIBLE_SOL_BASES: selectable upgrade surface would be empty")
else console.log(`   ok: ${eligibleSolBases.size} eligible Sol agents expose equivalent, non-implementation Astra aliases`)

const gga=["review-risk","review-readability","review-reliability","review-resilience","review-refuter","review-validator"]
const generic=new Set()
let genericRuntimeReady=true
for (const name of ["gentle-orchestrator","general"]) {
  const dbg=readDebug(name)
  if (!dbg) { genericRuntimeReady=false; continue }
  const m=normalizeModel(dbg.model)
  if (m) generic.add(m)
  else genericRuntimeReady=false
}
let distinct=false
let ggaRuntimeReady=true
for (const name of gga) {
  const configured=deployedAgents[name]
  if (!configured || typeof configured!=="object" || !hasOwn(configured,"model")) { fail(`GGA_REVIEW_MODEL_UNASSIGNED: ${name}`); ggaRuntimeReady=false; continue }
  const assigned=normalizeModel(configured.model); const actual=readDebug(name)
  if (!actual) { ggaRuntimeReady=false; continue }
  const runtime=normalizeModel(actual.model)
  if (assigned && !generic.has(assigned)) distinct=true
  if (runtime!==assigned) {
    if (runtime && genericRuntimeReady && generic.has(runtime)) fail(`GGA_REVIEW_MODEL_INHERITED: ${name} assigned ${assigned} but runtime primary is generic ${runtime}`)
    else fail(`GGA_REVIEW_PRIMARY_MISMATCH: ${name} assigned ${assigned} but runtime primary is ${show(runtime)}`)
  }
  if (hasOwn(configured,"variant")) {
    const expectedVariant=configured.variant==null?undefined:configured.variant
    const runtimeVariant=typeof actual.variant==="string"?actual.variant:undefined
    if (runtimeVariant!==expectedVariant) fail(`GGA_REVIEW_VARIANT_MISMATCH: ${name}: assigned=${show(expectedVariant)} runtime=${show(runtimeVariant)}`)
  }
}
if (genericRuntimeReady && ggaRuntimeReady && !distinct) {
  fail("GGA_REVIEW_NO_DISTINCT_MODEL_CONTROL: review primaries do not provide a control distinct from general/orchestrator")
}

// pm-seat-policy:begin
// Owner direction 2026-10-28: both PM seats are the same exact Muse Spark Contributor seat
// with no variant (the model defines none); this supersedes the 2026-10-24 GLM high seat.
const PM_SEAT_MODEL="opencode-go/muse-spark-1.3-contributor"
const PM_SEAT_VARIANT=undefined
function pmSeatFailures(agents) {
  const failures=[]
  for (const name of ["pm-odd","pm-systematic"]) {
    const agent=agents?.[name]
    if (!agent || typeof agent!=="object") { failures.push(`PM_SEAT_MISSING: ${name}`); continue }
    const model=normalizeModel(agent.model)
    if (model!==PM_SEAT_MODEL) {
      const family=modelFamily(agent.model)
      failures.push(`${family==="gpt"?"PM_SEAT_OPENAI_MODEL":"PM_SEAT_MODEL_MISMATCH"}: ${name}=${show(model)}`)
    }
    if (agent.variant!==PM_SEAT_VARIANT) {
      failures.push(`PM_SEAT_VARIANT_MISMATCH: ${name}=${show(agent.variant)}`)
    }
  }
  return failures
}
// pm-seat-policy:end
for (const failure of pmSeatFailures(deployedAgents)) fail(failure)

// Compare underlying families, not provider prefixes or exact model IDs.
// A Go Luna fallback for OpenAI Luna does not create an independent reviewer.
// Q59: the dispatcher-to-writer pairs add the GLM PMs against their DeepSeek
// writers; the existing orchestrator/general and worker/verifier pairs remain.
for (const [writer,reviewer] of [["general","gentle-orchestrator"],["gentle-ai-worker","gentle-ai-verify"],["gentle-ai-worker","gentle-ai-verify-routine"],["pm-odd","odd-apply"],["pm-systematic","gentle-ai-worker"]]) {
  for (const [surface,writerModel,reviewerModel] of [
    ["configured",deployedAgents[writer]?.model,deployedAgents[reviewer]?.model],
    ["runtime",readDebug(writer)?.model,readDebug(reviewer)?.model],
  ]) {
    if (!writerModel || !reviewerModel) continue // Missing agents have their own probe errors.
    const writerFamily=modelFamily(writerModel), reviewerFamily=modelFamily(reviewerModel)
    if (!writerFamily || !reviewerFamily) {
      fail(`PRIMARY_REVIEW_FAMILY_UNKNOWN: ${surface} ${writer}=${show(normalizeModel(writerModel))}, ${reviewer}=${show(normalizeModel(reviewerModel))}`)
    } else if (writerFamily===reviewerFamily) {
      fail(`PRIMARY_REVIEW_SAME_FAMILY: ${surface} ${writer} and ${reviewer} both use ${writerFamily}`)
    } else {
      console.log(`   ok: ${surface} ${writer} (${writerFamily}) is reviewed by ${reviewer} (${reviewerFamily})`)
    }
  }
}

for (const [lane,names,configuredModel] of [
  ["Gentle AI 4R",gga,(name)=>deployedAgents[name]?.model],
  ["Systematic baseline",["correctness-reviewer","testing-reviewer","project-standards-reviewer"],(name)=>{
    const agent=byName.get(name)
    return agent ? expectedFor(systematic,agent).model : undefined
  }],
]) {
  for (const [surface,models] of [
    ["configured",names.map(configuredModel)],
    ["runtime",names.map((name)=>readDebug(name)?.model)],
  ]) {
    const families=models.map(modelFamily)
    if (families.some((family)=>!family)) {
      fail(`REVIEW_FAMILY_UNKNOWN: ${lane} ${surface} models=${JSON.stringify(models.map(normalizeModel))}`)
    } else if (new Set(families).size<3) {
      fail(`REVIEW_FAMILY_SPREAD_INSUFFICIENT: ${lane} ${surface} families=${JSON.stringify([...new Set(families)])}`)
    } else {
      console.log(`   ok: ${lane} ${surface} review spans ${[...new Set(families)].join(", ")}`)
    }
  }
}

function pluginPath(ref) {
  if (typeof ref!=="string") return undefined
  if (ref.startsWith("file://")) { try { return new URL(ref).pathname } catch { return undefined } }
  return path.isAbsolute(ref)?ref:undefined
}
function modelString(value) {
  if (typeof value==="string" && value.trim()) return value.trim()
  if (value && typeof value==="object") {
    const provider=value.providerID ?? value.providerId ?? value.provider
    const model=value.modelID ?? value.modelId ?? value.model ?? value.name
    if (typeof provider==="string" && provider.trim() && typeof model==="string" && model.trim()) return `${provider.trim()}/${model.trim()}`
    for (const k of ["id"]) if (typeof value[k]==="string" && value[k].trim()) return value[k].trim()
    if (typeof value.provider==="string" && typeof value.name==="string") return `${value.provider}/${value.name}`
  }
  return undefined
}
function parseModelRef(value, label) {
  const key=modelString(value)
  const slash=typeof key==="string"?key.indexOf("/"):-1
  if (slash<=0 || slash===key.length-1) { fail(`${label}: malformed model reference ${show(value)}`); return undefined }
  const ref={key,provider:key.slice(0,slash),model:key.slice(slash+1)}
  if (!ref.provider || !ref.model || ref.provider===ref.model) { fail(`${label}: malformed model reference ${show(value)}`); return undefined }
  return ref
}
function providerOf(model) { return parseModelRef(model,"MODEL_REFERENCE")?.provider }
function normalizedRule(value, label, sourceModel) {
  const entries=Array.isArray(value)?value:[value]
  if (value===undefined || entries.length===0) { fail(`${label}: empty fallback rule`); return [] }
  const seen=new Set(); const out=[]
  for (const entry of entries) {
    const ref=parseModelRef(entry,label); if (!ref) continue
    if (sourceModel && ref.key===sourceModel) fail(`${label}: chain contains its primary ${sourceModel}`)
    if (seen.has(ref.key)) fail(`${label}: duplicate chain member ${ref.key}`)
    else { seen.add(ref.key); out.push(ref.key) }
  }
  return out
}
function normalizedTargets(value, label, sourceModel) {
  const entries=Array.isArray(value)?value:[value]
  const keys=normalizedRule(value,label,sourceModel)
  return keys.map((key,index)=>{
    const entry=entries[index]
    const ref=parseModelRef(entry,label)
    const capabilities=entry && typeof entry==="object" && Array.isArray(entry.capabilities)?entry.capabilities:[]
    const variant=entry && typeof entry==="object" && typeof entry.variant==="string"?entry.variant:undefined
    if (entry && typeof entry==="object") {
      const supported=new Set(["providerID","modelID","variant","capabilities"])
      for (const field of Object.keys(entry)) if (!supported.has(field)) fail(`${label}: unsupported target field ${field}`)
      if (hasOwn(entry,"variant") && (!variant || !variant.trim())) fail(`${label}: empty target variant for ${key}`)
      if (hasOwn(entry,"capabilities")) {
        if (!Array.isArray(entry.capabilities)) fail(`${label}: capabilities must be an array for ${key}`)
        else {
          if (new Set(entry.capabilities).size!==entry.capabilities.length) fail(`${label}: duplicate capabilities for ${key}`)
          for (const capability of entry.capabilities) if (!["files","tools","vision"].includes(capability)) fail(`${label}: unsupported capability ${show(capability)} for ${key}`)
        }
      }
    }
    return {key,provider:ref?.provider,capabilities,variant}
  })
}
function configuredFallbacks(config, sourceModel, agent) {
  if (!config || typeof config!=="object" || config.enabled===false) return []
  const provider=providerOf(sourceModel); if (!provider) return []
  if (agent && config.agentFallbackModels && typeof config.agentFallbackModels==="object" && hasOwn(config.agentFallbackModels,agent)) {
    return normalizedRule(config.agentFallbackModels[agent],`FALLBACK_AGENT_${agent}`,sourceModel)
  }
  if (config.fallbackModels && typeof config.fallbackModels==="object" && hasOwn(config.fallbackModels,sourceModel)) {
    return normalizedRule(config.fallbackModels[sourceModel],`FALLBACK_EXACT_${sourceModel}`,sourceModel)
  }
  if (config.providerFallbacks && typeof config.providerFallbacks==="object" && hasOwn(config.providerFallbacks,provider)) {
    return normalizedRule(config.providerFallbacks[provider],`FALLBACK_PROVIDER_${provider}`)
  }
  return normalizedRule(config.fallbackModel,"FALLBACK_GLOBAL")
}
function effectiveFallbacks(config, sourceModel, agent, failureScope="provider") {
  const provider=providerOf(sourceModel)
  if (!provider || !Array.isArray(config.startProviders) || !config.startProviders.includes(provider)) return []
  const chain=configuredFallbacks(config,sourceModel,agent).slice()
  const keepSameProvider=config.sameProviderFallbackMode==="always" || (config.sameProviderFallbackMode==="model-specific" && failureScope==="model")
  return keepSameProvider ? chain : chain.filter((target)=>providerOf(target)!==provider)
}
function addRole(map, model, role) {
  const key=normalizeModel(model)
  if (!key) return
  if (!map.has(key)) map.set(key,[])
  map.get(key).push(role)
}
const refs=(Array.isArray(deployed.plugin)?deployed.plugin:[]).filter((x)=>typeof x==="string" && x.includes("opencode-rate-limit-fallback-mapped"))
if (refs.length!==1) fail(`GGA_FALLBACK_PLUGIN_UNRESOLVED: expected one mapped fallback plugin, found ${refs.length}`)
else {
  const p=pluginPath(refs[0])
  if (!p || !fs.existsSync(p)) fail(`GGA_FALLBACK_PLUGIN_SOURCE_MISSING: ${refs[0]}`)
  else {
    const dir=path.dirname(p)
    const sources=[p,path.join(dir,"src","config.ts"),path.join(dir,"src","plugin.ts"),path.join(dir,"src","log.ts")].filter(fs.existsSync).map((x)=>fs.readFileSync(x,"utf8")).join("\n")
    const fallbackDefaultsPath=path.join(dir,"src","config.ts")
    let defaults=""
    if (!fs.existsSync(fallbackDefaultsPath)) fail(`FALLBACK_DEFAULTS_SOURCE_MISSING: ${fallbackDefaultsPath}`)
    else {
      defaults=fs.readFileSync(fallbackDefaultsPath,"utf8")
      const excludedBlock=defaults.match(/DEFAULT_EXCLUDE_AGENTS\s*=\s*\[([\s\S]*?)\]/)?.[1] || ""
      for (const name of ["review-risk","review-resilience","review-readability","review-reliability","review-refuter","review-validator","asi-review-risk","asi-review-resilience","asi-review-readability","asi-review-reliability","asi-review-refuter","asi-review-validator"]) if (!excludedBlock.includes(`"${name}"`)) fail(`FALLBACK_SOURCE_BOUND_REVIEW_EXCLUSION_MISSING: ${name}`)
    }
    const requiredPluginFeatures=[
      ["agentFallbackModels","agent-specific fallback precedence"],
      ["agentRequiredCapabilities","capability-aware replay filtering"],
      ["sourceGraceProviders","non-blocking source-provider grace"],
      ["replayWatchdogMs","replay creation watchdog"],
      ["fallback_dispatch_failed","dispatch-failure chain advancement"],
      ["recorded_fallback_provenance","provenance-scoped home restoration"],
      [".atl","approved project-local fallback log root"],
      ["project_log_skipped","missing-session-directory diagnostic"],
      ["session_directory_unavailable","session-directory lookup fail-closed behavior"],
      ["project_log_write_failed","project-log write-failure diagnostic"],
    ]
    for (const [marker,label] of requiredPluginFeatures) if (!sources.includes(marker)) fail(`FALLBACK_PLUGIN_FEATURE_MISSING: ${label} (${marker})`)
    if (/join\(\s*["']\.git["']\s*,\s*["']gentle-ai["']\s*,\s*["']rate-limit-fallback\.log["']\s*\)/.test(sources)) fail("FALLBACK_PROJECT_LOG_LEGACY_GIT_PATH_PRESENT")
    if (/return\s+context\.directory\b/.test(sources)) fail("FALLBACK_PROJECT_DIRECTORY_UNSAFE_SERVER_CWD_FALLBACK")
    if (!sources.includes("classifyFailureScope") || !sources.includes("sameProviderFallbackMode")) fail("FALLBACK_PLUGIN_FAILURE_SCOPE_ROUTING_MISSING")
    const names=[...sources.matchAll(/["'`]([^"'`\n]*rate-limit-fallback[^"'`\n]*\.json)["'`]/g)].map((m)=>m[1])
    const unique=[...new Set(names)]; const declared=unique.find((x)=>path.basename(x)===x) ?? unique[0]
    if (!declared) fail("GGA_FALLBACK_CONFIG_DISCOVERY_FAILED")
    else {
      const candidates=path.isAbsolute(declared)?[declared]:[path.join(process.env.HOME||"", ".config","opencode",declared),path.resolve(dir,declared)]
      const cfgPath=candidates.find(fs.existsSync)
      if (!cfgPath) fail(`GGA_FALLBACK_CONFIG_MISSING: ${declared}`)
      else {
        try {
          const cfg=parseJsonc(cfgPath)
          const supportedFieldsMatch=defaults.match(/SUPPORTED_CONFIG_FIELDS\s*=[\s\S]*?\[([\s\S]*?)\]/)
          const supportedFields=[...(supportedFieldsMatch?.[1] ?? "").matchAll(/["']([^"']+)["']/g)].map((match)=>match[1])
          if (supportedFields.length===0) fail("FALLBACK_CONFIG_SUPPORTED_FIELDS_EXTRACTION_EMPTY")
          else {
            const supportedFieldSet=new Set([...supportedFields,"peakPolicy"])
            for (const key of Object.keys(cfg)) if (!supportedFieldSet.has(key)) fail(`FALLBACK_CONFIG_UNSUPPORTED_FIELD: ${key}`)
          }
          if (cfg.enabled!==true) fail("FALLBACK_CONFIG_DISABLED")
          if (cfg.logging!==true) fail("FALLBACK_LOGGING_NOT_ENABLED")
          if (cfg.advanceGraceMs!==30000) fail(`FALLBACK_ADVANCE_GRACE_MISMATCH: expected 30000, got ${show(cfg.advanceGraceMs)}`)
          if (cfg.sourceGraceMs!==30000) fail(`FALLBACK_SOURCE_GRACE_MISMATCH: expected 30000, got ${show(cfg.sourceGraceMs)}`)
          if (!Array.isArray(cfg.sourceGraceProviders) || !cfg.sourceGraceProviders.includes("opencode-go")) fail(`FALLBACK_GO_SOURCE_GRACE_MISSING: ${show(cfg.sourceGraceProviders)}`)
          if (!(Number.isFinite(cfg.replayWatchdogMs) && cfg.replayWatchdogMs>0)) fail(`FALLBACK_REPLAY_WATCHDOG_INVALID: ${show(cfg.replayWatchdogMs)}`)
          if (cfg.sameProviderFallbackMode!=="model-specific") fail(`FALLBACK_SAME_PROVIDER_MODE_MISMATCH: ${show(cfg.sameProviderFallbackMode)}`)
          if (!Array.isArray(cfg.modelFailurePatterns) || cfg.modelFailurePatterns.length===0) fail("FALLBACK_MODEL_FAILURE_PATTERNS_EMPTY")
          if (!Array.isArray(cfg.providerFailurePatterns) || cfg.providerFailurePatterns.length===0) fail("FALLBACK_PROVIDER_FAILURE_PATTERNS_EMPTY")
          if (cfg.revertToOriginalModel!==true) fail(`FALLBACK_HOME_RESTORE_NOT_EXPLICIT_TRUE: ${show(cfg.revertToOriginalModel)}`)
          const exclusions=Array.isArray(cfg.excludePatterns)?cfg.excludePatterns.map((x)=>String(x).toLowerCase()):[]
          for (const required of ["context length","invalid request","authentication failed","unauthorized","invalid api key"]) if (!exclusions.includes(required)) fail(`FALLBACK_REQUIRED_EXCLUSION_MISSING: ${required}`)
          if (hasOwn(cfg,"peakPolicy")) console.log("   ok: peakPolicy is present but deliberately ignored by the rate-limit plugin")
          if (/glm-5\.2/i.test(JSON.stringify(cfg))) fail("FALLBACK_OBSOLETE_MODEL: GLM-5.2 remains in fallback policy")

          const requiredExcluded=["review-risk","review-resilience","review-readability","review-reliability","review-refuter","review-validator","asi-review-risk","asi-review-resilience","asi-review-readability","asi-review-reliability","asi-review-refuter","asi-review-validator"]
          const excluded=new Set(Array.isArray(cfg.excludeAgents)?cfg.excludeAgents:[])
          for (const name of requiredExcluded) if (!excluded.has(name)) fail(`FALLBACK_BOUND_REVIEW_EXCLUSION_MISSING: ${name}`)

          if (!fallbackPolicySourcePath || !fs.existsSync(fallbackPolicySourcePath)) {
            fail(`FALLBACK_CANONICAL_POLICY_MISSING: ${fallbackPolicySourcePath || "<unset>"}`)
          } else {
            parseJsonc(fallbackPolicySourcePath)
            if (fs.readFileSync(cfgPath).compare(fs.readFileSync(fallbackPolicySourcePath))!==0) {
              fail(`FALLBACK_DEPLOYED_POLICY_DRIFT: ${cfgPath} differs from ${fallbackPolicySourcePath}`)
            }
          }

          const activeRoles=new Map()
          const activeAgentModels=new Map()
          for (const [name,agent] of Object.entries(deployedAgents)) {
            if (agent && typeof agent==="object" && agent.disable!==true) {
              addRole(activeRoles,agent.model,`opencode:${name}`)
              const model=normalizeModel(agent.model); if (model) activeAgentModels.set(name,model)
            }
          }
          for (const agent of inventory) {
            const expected=expectedFor(systematic,agent)
            if (!expected.disable) {
              addRole(activeRoles,expected.model,`systematic:${agent.name}`)
              if (expected.model) activeAgentModels.set(agent.name,expected.model)
            }
          }
          if (eligibleSolBases.size>0) {
            addRole(activeRoles,ASTRA_MODEL,`derived-astra-aliases:${[...eligibleSolBases].sort().join(",")}`)
            for (const name of eligibleSolBases) activeAgentModels.set(`${name}${ASTRA_SUFFIX}`,ASTRA_MODEL)
          }
          const optionalProfileRoles=new Map()
          const definedProfiles=systematic.profiles && typeof systematic.profiles==="object" && !Array.isArray(systematic.profiles)
            ? Object.keys(systematic.profiles)
            : []
          for (const profileName of definedProfiles) {
            const profiled={...systematic,profile:profileName}
            for (const agent of inventory) {
              const expected=expectedFor(profiled,agent)
              if (!expected.disable) addRole(optionalProfileRoles,expected.model,`systematic-profile:${profileName}:${agent.name}`)
            }
          }
          const activeModels=[...activeRoles.keys()].sort()
          const optionalProfileModels=[...optionalProfileRoles.keys()].filter((model)=>!activeRoles.has(model)).sort()
          const supportedModels=new Set([...activeModels,...optionalProfileModels])
          for (const obsolete of ["openai/gpt-5.6-sol","openai/gpt-5.6-luna"]) {
            if (supportedModels.has(obsolete)) fail(`OPENAI_V6_PRIMARY_MIGRATION_INCOMPLETE: ${obsolete}`)
          }
          const activeProviders=new Set([...supportedModels].map((m)=>providerOf(m)).filter(Boolean))
          const starters=Array.isArray(cfg.startProviders)?cfg.startProviders:[]
          if (!Array.isArray(cfg.startProviders) || starters.length===0) fail("FALLBACK_START_PROVIDERS_INVALID")
          if (new Set(starters).size!==starters.length) fail("FALLBACK_START_PROVIDERS_DUPLICATE")
          for (const provider of activeProviders) if (!starters.includes(provider)) fail(`FALLBACK_ACTIVE_PROVIDER_NOT_STARTER: ${provider}`)
          for (const provider of starters) if (!activeProviders.has(provider)) fail(`FALLBACK_UNSUPPORTED_START_PROVIDER: ${provider}`)
          for (const provider of cfg.sourceGraceProviders??[]) if (!starters.includes(provider)) fail(`FALLBACK_SOURCE_GRACE_PROVIDER_NOT_STARTER: ${provider}`)

          const exact=cfg.fallbackModels && typeof cfg.fallbackModels==="object" && !Array.isArray(cfg.fallbackModels)?cfg.fallbackModels:{}
          const providerRules=cfg.providerFallbacks && typeof cfg.providerFallbacks==="object" && !Array.isArray(cfg.providerFallbacks)?cfg.providerFallbacks:{}
          const agentRules=cfg.agentFallbackModels && typeof cfg.agentFallbackModels==="object" && !Array.isArray(cfg.agentFallbackModels)?cfg.agentFallbackModels:{}
          const agentRequirements=cfg.agentRequiredCapabilities && typeof cfg.agentRequiredCapabilities==="object" && !Array.isArray(cfg.agentRequiredCapabilities)?cfg.agentRequiredCapabilities:{}
          const activeFallbackText=JSON.stringify({agentRules,exact,providerRules,global:cfg.fallbackModel})
          if (/gpt-5\.6-(sol|luna)/.test(activeFallbackText)) fail("OPENAI_V6_FALLBACK_MIGRATION_INCOMPLETE: retired Sol/Luna active chain")
          for (const migrated of ["openai/gpt-6.1-sol","openai/gpt-6-luna"]) {
            if (supportedModels.has(migrated) && !hasOwn(exact,migrated)) fail(`OPENAI_V6_EXACT_FALLBACK_MISSING: ${migrated}`)
          }
          const astraChain=Array.isArray(exact[ASTRA_MODEL])?normalizedRule(exact[ASTRA_MODEL],"FALLBACK_ASTRA",ASTRA_MODEL):[]
          if (supportedModels.has(ASTRA_MODEL) && astraChain[0]!==SOL_MODEL) fail(`ASTRA_SOL_DOWNGRADE_MISSING: expected ${SOL_MODEL}, got ${show(astraChain[0])}`)
          for (const [agent,rule] of Object.entries(agentRules)) {
            const source=activeAgentModels.get(agent)
            if (!source) { fail(`FALLBACK_AGENT_RULE_INACTIVE: ${agent}`); continue }
            let targets=normalizedTargets(rule,`FALLBACK_AGENT_${agent}`,source)
            const provider=providerOf(source)
            targets=targets.filter((target)=>target.provider!==provider)
            const required=Array.isArray(agentRequirements[agent])?agentRequirements[agent]:[]
            if (new Set(required).size!==required.length) fail(`FALLBACK_AGENT_CAPABILITY_DUPLICATE: ${agent}`)
            for (const capability of required) if (!["files","tools","vision"].includes(capability)) fail(`FALLBACK_AGENT_CAPABILITY_UNSUPPORTED: ${agent}.${capability}`)
            targets=targets.filter((target)=>required.every((capability)=>target.capabilities.includes(capability)))
            if (targets.length===0) fail(`FALLBACK_AGENT_NO_COMPATIBLE_PROVIDER_FAILURE_CHAIN: ${agent}`)
            else console.log(`   ok: capability-sensitive agent ${agent}; first fallback=${targets[0].key}; required=${JSON.stringify(required)}`)
          }
          for (const agent of Object.keys(agentRequirements)) if (!hasOwn(agentRules,agent)) fail(`FALLBACK_AGENT_REQUIREMENT_WITHOUT_RULE: ${agent}`)
          for (const source of Object.keys(exact)) {
            parseModelRef(source,`FALLBACK_EXACT_SOURCE_${source}`)
            normalizedTargets(exact[source],`FALLBACK_EXACT_${source}`,source)
            if (!supportedModels.has(source)) fail(`FALLBACK_EXACT_SOURCE_INACTIVE: ${source}`)
          }
          for (const [provider,rule] of Object.entries(providerRules)) {
            if (!starters.includes(provider)) fail(`FALLBACK_PROVIDER_RULE_NOT_STARTER: ${provider}`)
            const chain=normalizedTargets(rule,`FALLBACK_PROVIDER_${provider}`).map((target)=>target.key)
            const effective=chain.filter((target)=>providerOf(target)!==provider)
            if (effective.length===0) fail(`FALLBACK_PROVIDER_RULE_EMPTY_EFFECTIVE_CHAIN: ${provider}`)
          }
          for (const provider of activeProviders) if (!hasOwn(providerRules,provider)) fail(`FALLBACK_ACTIVE_PROVIDER_NO_EMERGENCY_RULE: ${provider}`)
          normalizedTargets(cfg.fallbackModel,"FALLBACK_GLOBAL")

          const openCodeDeepSeek41="opencode-go/deepseek-v4.1-flash"
          const directDeepSeek41="deepseek/deepseek-flash"
          const openRouterDeepSeek41="openrouter/deepseek/deepseek-v4.1-flash"
          const fallbackText=JSON.stringify(cfg)
          for (const retiredModel of [
            "muse-spark-1.2-contributor",
            "deepseek-v4-pro",
            "deepseek-v4-flash-vision-exp",
            "deepseek-v4-flash-0731",
          ]) {
            if (fallbackText.includes(retiredModel)) fail(`FALLBACK_RETIRED_MUSE_OR_DEEPSEEK_MODEL: ${retiredModel}`)
          }
          if (!hasOwn(exact,openCodeDeepSeek41)) {
            fail(`DEEPSEEK_V4_1_EXACT_FALLBACK_POLICY_MISSING: ${openCodeDeepSeek41}`)
          } else {
            const modelChain=effectiveFallbacks(cfg,openCodeDeepSeek41,undefined,"model")
            const providerChain=effectiveFallbacks(cfg,openCodeDeepSeek41,undefined,"provider")
            for (const [scope,chain] of [["model",modelChain],["provider",providerChain]]) {
              if (chain[0]!==directDeepSeek41) fail(`DEEPSEEK_V4_1_${scope.toUpperCase()}_FALLBACK_FIRST_MISMATCH: expected ${directDeepSeek41}, got ${show(chain[0])}`)
              if (!chain.includes(openRouterDeepSeek41)) fail(`DEEPSEEK_V4_1_${scope.toUpperCase()}_OPENROUTER_FALLBACK_MISSING: ${openRouterDeepSeek41}`)
              if (scope==="provider" && chain.some((target)=>providerOf(target)==="opencode-go")) {
                fail(`DEEPSEEK_V4_1_PROVIDER_FAILURE_FALLBACK_UNSAFE: same-provider target remains in ${JSON.stringify(chain)}`)
              }
            }
          }

          for (const model of activeModels) {
            if (!hasOwn(exact,model)) fail(`FALLBACK_ACTIVE_MODEL_NO_EXACT_POLICY: ${model}; roles=${activeRoles.get(model).join(",")}`)
            const providerChain=effectiveFallbacks(cfg,model,undefined,"provider")
            const modelChain=effectiveFallbacks(cfg,model,undefined,"model")
            if (providerChain.length===0) fail(`FALLBACK_ACTIVE_MODEL_EMPTY_PROVIDER_FAILURE_CHAIN: ${model}`)
            if (modelChain.length===0) fail(`FALLBACK_ACTIVE_MODEL_EMPTY_MODEL_FAILURE_CHAIN: ${model}`)
            if (providerChain.length && modelChain.length) console.log(`   ok: active primary ${model}; provider-failure=${JSON.stringify(providerChain)}; model-failure=${JSON.stringify(modelChain)}`)
          }
          for (const model of optionalProfileModels) {
            if (!hasOwn(exact,model)) fail(`FALLBACK_PROFILE_MODEL_NO_EXACT_POLICY: ${model}; roles=${optionalProfileRoles.get(model).join(",")}`)
            const providerChain=effectiveFallbacks(cfg,model,undefined,"provider")
            const modelChain=effectiveFallbacks(cfg,model,undefined,"model")
            if (providerChain.length===0 || modelChain.length===0) fail(`FALLBACK_PROFILE_MODEL_EMPTY_EFFECTIVE_CHAIN: ${model}`)
            else console.log(`   ok: optional-profile primary ${model}; provider-failure=${JSON.stringify(providerChain)}; model-failure=${JSON.stringify(modelChain)}`)
          }

          const exactKeys=new Set(Object.keys(exact))
          const graph=new Map([...exactKeys].map((source)=>[source,normalizedRule(exact[source],`FALLBACK_GRAPH_${source}`,source).filter((target)=>exactKeys.has(target))]))
          const visiting=new Set(), visited=new Set(), stack=[]
          function visit(node) {
            if (visiting.has(node)) { const start=stack.indexOf(node); fail(`FALLBACK_EXPLICIT_POLICY_CYCLE: ${[...stack.slice(start),node].join(" -> ")}`); return }
            if (visited.has(node)) return
            visiting.add(node); stack.push(node)
            for (const next of graph.get(node)??[]) visit(next)
            stack.pop(); visiting.delete(node); visited.add(node)
          }
          for (const node of graph.keys()) visit(node)

          const ggaModels=new Set(gga.map((name)=>normalizeModel(deployedAgents[name]?.model)).filter(Boolean))
          if (ggaModels.size<4) fail(`GGA_REVIEW_DIVERSITY_LOST: models=${ggaModels.size}`)
          // Bound review sessions recover through native STATUS-based relaunch;
          // rate-limit replay would bypass transport-injected Task context.

          const judges=["jd-judge-a","jd-judge-b"].map((name)=>({name,model:normalizeModel(deployedAgents[name]?.model)})).map((x)=>({...x,first:x.model?effectiveFallbacks(cfg,x.model)[0]:undefined}))
          if (judges.some((x)=>!x.model || !x.first)) fail(`JUDGMENT_DAY_FALLBACK_MISSING: ${JSON.stringify(judges)}`)
          else {
            if (new Set(judges.map((x)=>x.model)).size!==2) fail(`JUDGMENT_DAY_PRIMARY_DIVERSITY_LOST: ${JSON.stringify(judges)}`)
            if (new Set(judges.map((x)=>x.first)).size!==2 || new Set(judges.map((x)=>providerOf(x.first))).size!==2) fail(`JUDGMENT_DAY_FALLBACK_DIVERSITY_LOST: ${JSON.stringify(judges)}`)
          }
          console.log(`   ok: ${activeModels.length} active and ${optionalProfileModels.length} optional-profile primary models have exact effective fallback policies from ${cfgPath}`)
        } catch (error) { fail(`GGA_FALLBACK_CONFIG_INVALID: ${error.message}`) }
      }
    }
  }
}

if (gp.edit!=="deny") fail(`HOST_EDIT_NOT_DENIED: global permission.edit=${show(gp.edit)}`)
if (gp.write!=="deny") fail(`HOST_WRITE_NOT_DENIED: global permission.write=${show(gp.write)}`)
if (gp.ctx_search!=="allow") fail(`MAGIC_CONTEXT_SEARCH_NOT_ALLOW: ${show(gp.ctx_search)}`)
if (gp.ctx_expand!=="allow") fail(`MAGIC_CONTEXT_EXPAND_NOT_ALLOW: ${show(gp.ctx_expand)}`)
if (gp.ctx_memory!=="deny") fail(`MAGIC_CONTEXT_MEMORY_DEFAULT_NOT_DENY: ${show(gp.ctx_memory)}`)
if (gp.host_register_project!=="deny") fail(`HOST_REGISTER_PROJECT_DEFAULT_NOT_DENY: ${show(gp.host_register_project)}`)
if (gp.bash!=="deny" || gp.bash_status!=="deny" || gp.bash_watch!=="deny" || gp.bash_write!=="deny" || gp.bash_kill!=="deny" || gp.apply_patch!=="deny") fail("ORDINARY_HOST_EXECUTION_NOT_DENIED")
if (gp.grep!=="ask") fail(`GREP_PERMISSION_NOT_ASK: ${show(gp.grep)}`)
if (gp.glob!=="allow") fail(`GLOB_PERMISSION_NOT_ALLOW: ${show(gp.glob)}`)
if (gp.sandbox_bash!=="deny") fail(`SANDBOX_BASH_DEFAULT_NOT_DENY: ${show(gp.sandbox_bash)}`)
for (const [name,agent] of Object.entries(deployedAgents)) {
  const usesSandboxBash=cfgTool(agent,"sandbox_bash")===true
  const expected=usesSandboxBash ? "allow" : "deny"
  if (cfgPerm(agent,"sandbox_bash")!==expected) fail(`SANDBOX_BASH_AGENT_PERMISSION_MISMATCH: ${name} expected ${expected}, got ${show(cfgPerm(agent,"sandbox_bash"))}`)
}
for (const t of ["sandbox_apply","sandbox_apply_patch","sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_edit","sandbox_finish","sandbox_write"]) if (gp[t]!=="deny") fail(`SANDBOX_MUTATION_DEFAULT_NOT_DENY: ${t}=${show(gp[t])}`)


const registeredHostReads=["host_review_mode_status","host_review_status","host_review_lens_context","host_sandbox_result"]
const gatedHostMutations=["host_review_diff_read","host_git_commit","host_git_push","host_gh_issue_create","host_plan_append","host_register_project","host_review_start","host_review_materialize","host_review_pipeline_run","host_review_persist","host_review_capture_result","host_review_capture_unachievable","host_review_acknowledge_approved","host_review_capture_correction_plan","host_review_capture_refuter","host_review_capture_validation","host_review_validate","host_review_recover","host_sandbox_result_install","host_git_clear_commit_intent"]
const retiredHostOperations=["host_sdd_verify_validate","host_sdd_attempt_status","host_sdd_attempt_acquire","host_sdd_attempt_begin","host_sdd_attempt_rescope","host_sdd_attempt_finish","host_sdd_attempt_reset","host_sdd_attempt_settle","host_sdd_attempt_grant","host_sdd_archive_compose","host_sdd_status","host_sdd_continue","host_sdd_task_result"]
for (const name of registeredHostReads) if (gp[name]!=="allow") fail(`HOST_READ_PERMISSION_MISMATCH: ${name}`)
for (const name of [...gatedHostMutations,...retiredHostOperations]) if (gp[name]!=="deny") fail(`HOST_MUTATION_OR_RETIRED_DEFAULT_NOT_DENY: ${name}`)
for (const name of ["host_system","host_service_status","host_service_logs","host_tailscale_status","host_memory","host_disk_usage","host_network_listeners","host_process_list","host_docker_list","host_docker_logs"]) if (gp[name]==="allow") fail(`UNREGISTERED_HOST_INSPECTION_ADVERTISED: ${name}`)

function cfgTool(agent,t) { return agent?.tools && typeof agent.tools==="object" ? agent.tools[t] : undefined }
function cfgPerm(agent,t) { return agent?.permission && typeof agent.permission==="object" ? agent.permission[t] : undefined }
// Q90 T3a1: the orchestrator-only fixed-tool surface. Plan drafting is ask-gated;
// the narrowly defined pre-registered test runner is allow-gated. Neither is a
// generic shell/edit authority, and no other agent may receive either grant.
function hostTestRunGlobalDefaultFailures(value) {
  return value==="deny" ? [] : [`HOST_TEST_RUN_GLOBAL_DEFAULT_NOT_DENY: ${show(value)}`]
}
function hostPlanWriteGlobalDefaultFailures(value) {
  return value==="deny" ? [] : [`HOST_PLAN_WRITE_GLOBAL_DEFAULT_NOT_DENY: ${show(value)}`]
}
function hostTestRunOrchestratorFailures(agent) {
  return cfgPerm(agent,"host_test_run")==="allow" ? [] : [`ORCHESTRATOR_HOST_TEST_RUN_NOT_ALLOW: ${show(cfgPerm(agent,"host_test_run"))}`]
}
function hostPlanWriteOrchestratorFailures(agent) {
  return cfgPerm(agent,"host_plan_write")==="ask" ? [] : [`ORCHESTRATOR_HOST_PLAN_WRITE_NOT_ASK: ${show(cfgPerm(agent,"host_plan_write"))}`]
}
function hostTestRunGrantSweepFailures(agents) {
  const failures=[]
  for (const [name,agent] of Object.entries(agents??{})) {
    if (name==="gentle-orchestrator") continue
    const value=cfgPerm(agent,"host_test_run")
    if (value!==undefined && value!=="deny") failures.push(`HOST_TEST_RUN_GRANTED_OUTSIDE_ORCHESTRATOR: ${name}=${show(value)}`)
  }
  return failures
}
function hostPlanWriteGrantSweepFailures(agents,allowedAgents) {
  const failures=[]
  const allowed=new Set(allowedAgents??[])
  for (const [name,agent] of Object.entries(agents??{})) {
    if (allowed.has(name)) continue
    const value=cfgPerm(agent,"host_plan_write")
    if (value!==undefined && value!=="deny") failures.push(`HOST_PLAN_WRITE_GRANTED_OUTSIDE_COORDINATORS: ${name}=${show(value)}`)
  }
  return failures
}
function hostToolPromptFailures(prompt) {
  const required=[
    "may draft plan documents through the ask-gated `host_plan_write` fixed tool",
    "plan documents only, never code or configuration",
    "narrowly defined, pre-registered tests through the allow-gated `host_test_run` fixed tool",
    "never arbitrary caller argv, pipes, redirects, or shell",
    "a failed or unavailable test run is evidence, never permission to widen authority",
    "`host_test_run` is not implemented in the current surface and remains inert until the host tool ships",
  ]
  return required.filter((fragment)=>!prompt.includes(fragment)).map((fragment)=>`HOST_TOOL_PROMPT_CLAUSE_MISSING: ${JSON.stringify(fragment)}`)
}
for (const failure of hostTestRunGlobalDefaultFailures(gp.host_test_run)) fail(failure)
const hostTestRunGlobalProbe=hostTestRunGlobalDefaultFailures("allow")
if (!hostTestRunGlobalProbe.includes('HOST_TEST_RUN_GLOBAL_DEFAULT_NOT_DENY: "allow"')) fail("HOST_TEST_RUN_GLOBAL_DEFAULT_POSITIVE_CONTROL_FAILED")
else console.log("   ok: host_test_run global-default positive control detected allow")
for (const failure of hostPlanWriteGlobalDefaultFailures(gp.host_plan_write)) fail(failure)
const hostPlanWriteGlobalProbe=hostPlanWriteGlobalDefaultFailures("ask")
if (!hostPlanWriteGlobalProbe.includes('HOST_PLAN_WRITE_GLOBAL_DEFAULT_NOT_DENY: "ask"')) fail("HOST_PLAN_WRITE_GLOBAL_DEFAULT_POSITIVE_CONTROL_FAILED")
else console.log("   ok: host_plan_write global-default positive control detected ask")
for (const failure of hostTestRunGrantSweepFailures(deployedAgents)) fail(failure)
for (const value of ["ask","allow"]) {
  const probe=hostTestRunGrantSweepFailures({[`synthetic-${value}-agent`]:{permission:{host_test_run:value}}})
  const expected=`HOST_TEST_RUN_GRANTED_OUTSIDE_ORCHESTRATOR: synthetic-${value}-agent=${show(value)}`
  if (!probe.includes(expected)) fail(`HOST_TEST_RUN_GRANT_SWEEP_POSITIVE_CONTROL_FAILED: ${value}`)
}
console.log("   ok: host_test_run is denied globally and granted only to the orchestrator")
function hostReviewAssessFailures(name,agent) {
  const failures=[]
  if (!agent?.permission || typeof agent.permission!=="object" || Array.isArray(agent.permission) || !Object.prototype.hasOwnProperty.call(agent.permission,"host_review_assess") || agent.permission.host_review_assess!=="allow") failures.push(`HOST_REVIEW_ASSESS_NOT_ALLOW: ${name}`)
  return failures
}
function hostReviewDiffReadFailures(name,agent) {
  const failures=[]
  if (!agent?.permission || typeof agent.permission!=="object" || Array.isArray(agent.permission) || !Object.prototype.hasOwnProperty.call(agent.permission,"host_review_diff_read") || agent.permission.host_review_diff_read!=="allow") failures.push(`HOST_REVIEW_DIFF_READ_NOT_ALLOW: ${name}`)
  return failures
}
// Q59 coordinator inventory: coordinator-generic checks use this shared set.
// Orchestrator-only checks below keep fixed-host, tiny-fix and registration names.
const pmAgents=["pm-odd","pm-systematic"]
const coordinatorAgents=["gentle-orchestrator",...pmAgents]
// The Planner is a plan writer and advisor dispatcher, but not a review coordinator.
// Keeping it out of coordinatorAgents avoids requiring the PM/review host grants and
// avoids treating its narrow task map as coordinator deep-dispatch authority.
const planWriterAgents=[...coordinatorAgents,"planner"]
const advisorDispatchAgents=[...coordinatorAgents,"planner"]
for (const failure of hostPlanWriteGrantSweepFailures(deployedAgents,planWriterAgents)) fail(failure)
for (const value of ["ask","allow"]) {
  const synthetic=`synthetic-${value}-plan-writer`
  const probe=hostPlanWriteGrantSweepFailures({[synthetic]:{permission:{host_plan_write:value}}},planWriterAgents)
  const expected=`HOST_PLAN_WRITE_GRANTED_OUTSIDE_COORDINATORS: ${synthetic}=${show(value)}`
  if (!probe.includes(expected)) fail(`HOST_PLAN_WRITE_GRANT_SWEEP_POSITIVE_CONTROL_FAILED: ${value}`)
  const coordinatorProbe=Object.fromEntries(planWriterAgents.map((name)=>[name,{permission:{host_plan_write:value}}]))
  if (hostPlanWriteGrantSweepFailures(coordinatorProbe,planWriterAgents).length!==0) fail(`HOST_PLAN_WRITE_COORDINATOR_POSITIVE_CONTROL_FAILED: ${value}`)
}
console.log("   ok: host_plan_write grants are limited to the coordinator set")
const relayReviewAgents=["asi-review-risk","asi-review-resilience","asi-review-readability","asi-review-reliability","asi-review-refuter","asi-review-validator"]
const plainProviderReviewAgents=["review-risk","review-resilience","review-readability","review-reliability","review-refuter","review-validator"]
for (const name of coordinatorAgents) {
  const agent=deployedAgents[name]
  if (!agent) { fail(`HOST_REVIEW_AGENT_MISSING: ${name}`); continue }
  for (const failure of hostReviewAssessFailures(name,agent)) fail(failure)
  const omitted=hostReviewAssessFailures(`${name}-omitted`,{permission:{}})
  if (!omitted.includes(`HOST_REVIEW_ASSESS_NOT_ALLOW: ${name}-omitted`)) fail(`HOST_REVIEW_ASSESS_OMITTED_POSITIVE_CONTROL_FAILED: ${name}`)
  const mismatched=hostReviewAssessFailures(`${name}-mismatched`,{permission:{host_review_assess:"ask"}})
  if (!mismatched.includes(`HOST_REVIEW_ASSESS_NOT_ALLOW: ${name}-mismatched`)) fail(`HOST_REVIEW_ASSESS_VALUE_POSITIVE_CONTROL_FAILED: ${name}`)
}
for (const name of coordinatorAgents) {
  const agent=deployedAgents[name]
  if (!agent) { fail(`HOST_REVIEW_AGENT_MISSING: ${name}`); continue }
  for (const failure of hostReviewDiffReadFailures(name,agent)) fail(failure)
  const omitted=hostReviewDiffReadFailures(`${name}-omitted`,{permission:{}})
  if (!omitted.includes(`HOST_REVIEW_DIFF_READ_NOT_ALLOW: ${name}-omitted`)) fail(`HOST_REVIEW_DIFF_READ_OMITTED_POSITIVE_CONTROL_FAILED: ${name}`)
  const mismatched=hostReviewDiffReadFailures(`${name}-mismatched`,{permission:{host_review_diff_read:"ask"}})
  if (!mismatched.includes(`HOST_REVIEW_DIFF_READ_NOT_ALLOW: ${name}-mismatched`)) fail(`HOST_REVIEW_DIFF_READ_VALUE_POSITIVE_CONTROL_FAILED: ${name}`)
}
function hostReviewMaterializeFailures(name,agent) {
  const failures=[]
  if (!agent?.permission || typeof agent.permission!=="object" || Array.isArray(agent.permission) || !Object.prototype.hasOwnProperty.call(agent.permission,"host_review_materialize") || agent.permission.host_review_materialize!=="allow") failures.push(`HOST_REVIEW_MATERIALIZE_NOT_ALLOW: ${name}`)
  return failures
}
for (const name of coordinatorAgents) {
  const agent=deployedAgents[name]
  if (!agent) { fail(`HOST_REVIEW_MATERIALIZE_AGENT_MISSING: ${name}`); continue }
  for (const failure of hostReviewMaterializeFailures(name,agent)) fail(failure)
  const omitted=hostReviewMaterializeFailures(`${name}-omitted`,{permission:{}})
  if (!omitted.includes(`HOST_REVIEW_MATERIALIZE_NOT_ALLOW: ${name}-omitted`)) fail(`HOST_REVIEW_MATERIALIZE_OMITTED_POSITIVE_CONTROL_FAILED: ${name}`)
  const mismatched=hostReviewMaterializeFailures(`${name}-mismatched`,{permission:{host_review_materialize:"ask"}})
  if (!mismatched.includes(`HOST_REVIEW_MATERIALIZE_NOT_ALLOW: ${name}-mismatched`)) fail(`HOST_REVIEW_MATERIALIZE_VALUE_POSITIVE_CONTROL_FAILED: ${name}`)
}
function hostReviewPipelineRunFailures(name,agent) {
  const failures=[]
  if (!agent?.permission || typeof agent.permission!=="object" || Array.isArray(agent.permission) || !Object.prototype.hasOwnProperty.call(agent.permission,"host_review_pipeline_run") || agent.permission.host_review_pipeline_run!=="allow") failures.push(`HOST_REVIEW_PIPELINE_RUN_NOT_ALLOW: ${name}`)
  return failures
}
function hostReviewPersistFailures(name,agent) {
  const failures=[]
  if (!agent?.permission || typeof agent.permission!=="object" || Array.isArray(agent.permission) || !Object.prototype.hasOwnProperty.call(agent.permission,"host_review_persist") || agent.permission.host_review_persist!=="ask") failures.push(`HOST_REVIEW_PERSIST_NOT_ASK: ${name}`)
  return failures
}
for (const name of coordinatorAgents) {
  const agent=deployedAgents[name]
  if (!agent) { fail(`HOST_REVIEW_AGENT_MISSING: ${name}`); continue }
  for (const failure of hostReviewPipelineRunFailures(name,agent)) fail(failure)
  for (const failure of hostReviewPersistFailures(name,agent)) fail(failure)
  const pipelineOmitted=hostReviewPipelineRunFailures(`${name}-omitted`,{permission:{}})
  if (!pipelineOmitted.includes(`HOST_REVIEW_PIPELINE_RUN_NOT_ALLOW: ${name}-omitted`)) fail(`HOST_REVIEW_PIPELINE_RUN_OMITTED_POSITIVE_CONTROL_FAILED: ${name}`)
  const pipelineWrong=hostReviewPipelineRunFailures(`${name}-wrong`,{permission:{host_review_pipeline_run:"ask"}})
  if (!pipelineWrong.includes(`HOST_REVIEW_PIPELINE_RUN_NOT_ALLOW: ${name}-wrong`)) fail(`HOST_REVIEW_PIPELINE_RUN_VALUE_POSITIVE_CONTROL_FAILED: ${name}`)
  const persistOmitted=hostReviewPersistFailures(`${name}-omitted`,{permission:{}})
  if (!persistOmitted.includes(`HOST_REVIEW_PERSIST_NOT_ASK: ${name}-omitted`)) fail(`HOST_REVIEW_PERSIST_OMITTED_POSITIVE_CONTROL_FAILED: ${name}`)
  const persistWrong=hostReviewPersistFailures(`${name}-wrong`,{permission:{host_review_persist:"allow"}})
  if (!persistWrong.includes(`HOST_REVIEW_PERSIST_NOT_ASK: ${name}-wrong`)) fail(`HOST_REVIEW_PERSIST_VALUE_POSITIVE_CONTROL_FAILED: ${name}`)
}
function hostReviewNewToolFailures(name,agent) {
  const failures=[]
  for (const tool of ["host_review_assess","host_review_diff_read","host_review_pipeline_run","host_review_persist"]) {
    if (!agent?.tools || typeof agent.tools!=="object" || Array.isArray(agent.tools) || !Object.prototype.hasOwnProperty.call(agent.tools,tool) || agent.tools[tool]!==true) failures.push(`HOST_REVIEW_TOOL_NOT_ENABLED: ${name}.${tool}`)
  }
  return failures
}
for (const name of ["pm-odd","pm-systematic"]) {
  const agent=deployedAgents[name]
  if (!agent) { fail(`HOST_REVIEW_AGENT_MISSING: ${name}`); continue }
  for (const failure of hostReviewNewToolFailures(name,agent)) fail(failure)
  for (const tool of ["host_review_assess","host_review_diff_read","host_review_pipeline_run","host_review_persist"]) {
    const omitted=hostReviewNewToolFailures(`${name}-omitted`,{tools:{}})
    if (!omitted.includes(`HOST_REVIEW_TOOL_NOT_ENABLED: ${name}-omitted.${tool}`)) fail(`HOST_REVIEW_TOOL_OMITTED_POSITIVE_CONTROL_FAILED: ${name}.${tool}`)
    const disabled=hostReviewNewToolFailures(`${name}-disabled`,{tools:{[tool]:false}})
    if (!disabled.includes(`HOST_REVIEW_TOOL_NOT_ENABLED: ${name}-disabled.${tool}`)) fail(`HOST_REVIEW_TOOL_VALUE_POSITIVE_CONTROL_FAILED: ${name}.${tool}`)
  }
}
function hostReviewMaterializeToolFailures(name,agent) {
  const failures=[]
  if (!agent?.tools || typeof agent.tools!=="object" || Array.isArray(agent.tools) || !Object.prototype.hasOwnProperty.call(agent.tools,"host_review_materialize") || agent.tools.host_review_materialize!==true) failures.push(`HOST_REVIEW_MATERIALIZE_TOOL_NOT_ENABLED: ${name}`)
  return failures
}
for (const name of ["pm-odd","pm-systematic"]) {
  const agent=deployedAgents[name]
  if (!agent) { fail(`HOST_REVIEW_MATERIALIZE_AGENT_MISSING: ${name}`); continue }
  for (const failure of hostReviewMaterializeToolFailures(name,agent)) fail(failure)
  const omitted=hostReviewMaterializeToolFailures(`${name}-omitted`,{tools:{}})
  if (!omitted.includes(`HOST_REVIEW_MATERIALIZE_TOOL_NOT_ENABLED: ${name}-omitted`)) fail(`HOST_REVIEW_MATERIALIZE_TOOL_OMITTED_POSITIVE_CONTROL_FAILED: ${name}`)
  const disabled=hostReviewMaterializeToolFailures(`${name}-disabled`,{tools:{host_review_materialize:false}})
  if (!disabled.includes(`HOST_REVIEW_MATERIALIZE_TOOL_NOT_ENABLED: ${name}-disabled`)) fail(`HOST_REVIEW_MATERIALIZE_TOOL_VALUE_POSITIVE_CONTROL_FAILED: ${name}`)
}
function hostReviewMaterializeGlobalDefaultFailures(value) {
  return value==="deny" ? [] : [`HOST_REVIEW_MATERIALIZE_GLOBAL_DEFAULT_NOT_DENY: ${show(value)}`]
}
for (const failure of hostReviewMaterializeGlobalDefaultFailures(gp.host_review_materialize)) fail(failure)
const hostReviewGlobalDefaultProbe=hostReviewMaterializeGlobalDefaultFailures("allow")
if (!hostReviewGlobalDefaultProbe.includes('HOST_REVIEW_MATERIALIZE_GLOBAL_DEFAULT_NOT_DENY: "allow"')) fail("HOST_REVIEW_MATERIALIZE_GLOBAL_DEFAULT_POSITIVE_CONTROL_FAILED")
else console.log("   ok: host_review_materialize global-default positive control detected allow")
function hostReviewNewGlobalDefaultFailures(tool,value) {
  return value==="deny" ? [] : [`HOST_REVIEW_GLOBAL_DEFAULT_NOT_DENY: ${tool}=${show(value)}`]
}
for (const tool of ["host_review_assess","host_review_diff_read","host_review_pipeline_run","host_review_persist"]) {
  for (const failure of hostReviewNewGlobalDefaultFailures(tool,gp[tool])) fail(failure)
  const probe=hostReviewNewGlobalDefaultFailures(tool,"allow")
  if (!probe.includes(`HOST_REVIEW_GLOBAL_DEFAULT_NOT_DENY: ${tool}="allow"`)) fail(`HOST_REVIEW_GLOBAL_DEFAULT_POSITIVE_CONTROL_FAILED: ${tool}`)
}
function hostReviewPipelineRunExceptionFailures(gated,agent) {
  const failures=[]
  if (!gated.includes("host_review_pipeline_run") || cfgPerm(agent,"host_review_pipeline_run")!=="allow") failures.push(`ORCHESTRATOR_HOST_REVIEW_PIPELINE_RUN_EXCEPTION_NOT_ALLOW: ${show(cfgPerm(agent,"host_review_pipeline_run"))}`)
  return failures
}
const pipelineExceptionOmitted=hostReviewPipelineRunExceptionFailures(gatedHostMutations.filter((name)=>name!=="host_review_pipeline_run"),{permission:{host_review_pipeline_run:"allow"}})
if (!pipelineExceptionOmitted.includes('ORCHESTRATOR_HOST_REVIEW_PIPELINE_RUN_EXCEPTION_NOT_ALLOW: "allow"')) fail("HOST_REVIEW_PIPELINE_RUN_EXCEPTION_OMITTED_POSITIVE_CONTROL_FAILED")
const pipelineExceptionWrong=hostReviewPipelineRunExceptionFailures(gatedHostMutations,{permission:{host_review_pipeline_run:"ask"}})
if (!pipelineExceptionWrong.includes('ORCHESTRATOR_HOST_REVIEW_PIPELINE_RUN_EXCEPTION_NOT_ALLOW: "ask"')) fail("HOST_REVIEW_PIPELINE_RUN_EXCEPTION_VALUE_POSITIVE_CONTROL_FAILED")
function hostReviewMaterializeExceptionFailures(gated,agent) {
  const failures=[]
  if (!gated.includes("host_review_materialize") || cfgPerm(agent,"host_review_materialize")!=="allow") failures.push(`ORCHESTRATOR_HOST_REVIEW_MATERIALIZE_EXCEPTION_NOT_ALLOW: ${show(cfgPerm(agent,"host_review_materialize"))}`)
  return failures
}
const hostReviewExceptionOmitted=hostReviewMaterializeExceptionFailures(gatedHostMutations.filter((name)=>name!=="host_review_materialize"),{permission:{host_review_materialize:"allow"}})
if (!hostReviewExceptionOmitted.includes('ORCHESTRATOR_HOST_REVIEW_MATERIALIZE_EXCEPTION_NOT_ALLOW: "allow"')) fail("HOST_REVIEW_MATERIALIZE_EXCEPTION_OMITTED_POSITIVE_CONTROL_FAILED")
else console.log("   ok: host_review_materialize exception positive control detected omitted allow-list membership")
const hostReviewExceptionWrong=hostReviewMaterializeExceptionFailures(gatedHostMutations,{permission:{host_review_materialize:"ask"}})
if (!hostReviewExceptionWrong.includes('ORCHESTRATOR_HOST_REVIEW_MATERIALIZE_EXCEPTION_NOT_ALLOW: "ask"')) fail("HOST_REVIEW_MATERIALIZE_EXCEPTION_VALUE_POSITIVE_CONTROL_FAILED")
else console.log("   ok: host_review_materialize exception positive control detected ask instead of allow")
for (const [name,agent] of Object.entries(deployedAgents)) {
  if (coordinatorAgents.includes(name)) continue
  if (cfgPerm(agent,"host_review_materialize")==="allow") fail(`HOST_REVIEW_MATERIALIZE_GRANTED_OUTSIDE_ALLOWLIST: ${name}`)
}
const hostReviewSweepProbe={"synthetic-fourth-agent":{permission:{host_review_materialize:"allow"}}}
const hostReviewSweepProbeFailures=Object.entries(hostReviewSweepProbe).filter(([,agent])=>cfgPerm(agent,"host_review_materialize")==="allow").map(([name])=>`HOST_REVIEW_MATERIALIZE_GRANTED_OUTSIDE_ALLOWLIST: ${name}`)
if (!hostReviewSweepProbeFailures.includes("HOST_REVIEW_MATERIALIZE_GRANTED_OUTSIDE_ALLOWLIST: synthetic-fourth-agent")) fail("HOST_REVIEW_MATERIALIZE_SWEEP_POSITIVE_CONTROL_FAILED")
else console.log("   ok: host_review_materialize negative-sweep positive control detected synthetic-fourth-agent")
function hostReviewNewGrantSweepFailures(agents) {
  const allowed=new Set(coordinatorAgents)
  const failures=[]
  for (const [name,agent] of Object.entries(agents??{})) {
    if (allowed.has(name)) continue
    for (const tool of ["host_review_assess","host_review_diff_read","host_review_pipeline_run","host_review_persist"]) {
      if (agent?.permission && typeof agent.permission==="object" && Object.prototype.hasOwnProperty.call(agent.permission,tool)) failures.push(`HOST_REVIEW_NEW_GRANT_OUTSIDE_ALLOWLIST: ${name}.${tool}`)
    }
  }
  return failures
}
for (const failure of hostReviewNewGrantSweepFailures(deployedAgents)) fail(failure)
for (const tool of ["host_review_pipeline_run","host_review_persist"]) {
  const probe=hostReviewNewGrantSweepFailures({"synthetic-fourth-agent":{permission:{[tool]:tool==="host_review_pipeline_run"?"allow":"ask"}}})
  if (!probe.includes(`HOST_REVIEW_NEW_GRANT_OUTSIDE_ALLOWLIST: synthetic-fourth-agent.${tool}`)) fail(`HOST_REVIEW_NEW_GRANT_SWEEP_POSITIVE_CONTROL_FAILED: ${tool}`)
}
function pmIdentityFailures(agents,handoff) {
  const failures=[]
  const routes={"pm-odd":"workflow-odd-secure","pm-systematic":"workflow-systematic"}
  const needles=["exactly one","Keep one unit per PM session","validate task class and route against the current `WORKFLOW.md`","Stop as `BLOCKED`","resume the same Task `task_id`","A report is a claim, never proof","docs/specs/pm-handoff.md"]
  // Owner correction 2026-10-19: a PM's mid-unit tiny fix dispatches a named
  // DeepSeek-family writer and never the orchestrator-only `general` lane.
  const tinyFixInstruction="Tiny-fix option: mid-unit, for a genuinely tiny fix dispatch `odd-apply` or `gentle-ai-worker` (DeepSeek family), never `general`, and only within the brief's allowed paths."
  const staleTinyFixInstruction="Tiny-fix option: mid-unit, you may dispatch `general` for a genuinely tiny fix only within the brief's allowed paths."
  for (const [name,route] of Object.entries(routes)) {
    const prompt=agents?.[name]?.prompt
    if (typeof prompt!=="string") { failures.push(`PM_IDENTITY_PROMPT_MISSING: ${name}`); continue }
    if (!prompt.includes(`Load \`${route}\` FIRST`)) failures.push(`PM_ROUTE_SKILL_NOT_LOADED_FIRST: ${name}`)
    for (const needle of needles) if (!prompt.includes(needle)) failures.push(`PM_IDENTITY_NEEDLE_MISSING: ${name}: ${needle}`)
    if (!prompt.includes(tinyFixInstruction)) failures.push(`PM_TINYFIX_WRITER_INSTRUCTION_MISSING: ${name}`)
    if (prompt.includes(staleTinyFixInstruction)) failures.push(`PM_TINYFIX_STALE_GENERAL_INSTRUCTION: ${name}`)
  }
  if (typeof handoff!=="string" || !handoff) failures.push("PM_HANDOFF_CONTRACT_UNREADABLE")
  else for (const needle of ["pm-unit-brief/v1","pm-unit-result/v1"]) if (!handoff.includes(needle)) failures.push(`PM_HANDOFF_SCHEMA_MISSING: ${needle}`)
  const orchestratorPrompt=agents?.["gentle-orchestrator"]?.prompt
  if (typeof orchestratorPrompt!=="string" || !orchestratorPrompt.includes("pm-unit-brief/v1") || !orchestratorPrompt.includes("docs/specs/pm-handoff.md")) failures.push("ORCHESTRATOR_BRIEF_CONTRACT_POINTER_MISSING")
  return failures
}
{
  let handoffText=""
  if (!workspaceRootAvailable) fail("PM_HANDOFF_CONTRACT_UNREADABLE: workspace root unavailable")
  else {
    try { handoffText=fs.readFileSync(path.join(workspaceRoot,"docs/specs/pm-handoff.md"),"utf8") }
    catch (error) { fail(`PM_HANDOFF_CONTRACT_UNREADABLE: ${error.message}`) }
  }
  for (const failure of pmIdentityFailures(deployedAgents,handoffText)) fail(failure)
  for (const failure of coordinatorTaskGraphFailures(deployedAgents)) fail(failure)
  for (const failure of promptBudgetFailures(deployedAgents)) fail(failure)
}
function coordinatorTaskGraphFailures(agents) {
  const failures=[]
  const pmRequired={
    "pm-odd":["odd-apply","gentle-ai-worker","gentle-ai-worker-local","gentle-ai-verify","gentle-ai-verify-routine","gentle-ai-verify-astra","explore","planner"],
    "pm-systematic":["gentle-ai-worker","gentle-ai-worker-local","gentle-ai-verify","gentle-ai-verify-routine","gentle-ai-verify-astra","explore","planner"],
  }
  // Strict per-PM MAXIMUM allowlist. A key outside this set is a grant even when
  // its value is "deny"; only the declared named lanes may appear at all.
  const pmMaximum={
    "pm-odd":new Set([
      "*","advisor-design-post","advisor-design-pre","advisor-gemini-post","advisor-gemini-pre",
      "advisor-integration-post","advisor-integration-pre","advisor-maintainability-post",
      "advisor-maintainability-pre","advisor-security-post","advisor-security-pre",
      "advisor-testing-post","advisor-testing-pre","explore","gentle-ai-worker",
      "gentle-ai-worker-local","gentle-ai-verify","gentle-ai-verify-routine","gentle-ai-verify-astra","odd-apply",
      "planner",
    ]),
    "pm-systematic":new Set([
      "*","advisor-design-post","advisor-design-pre","advisor-gemini-post","advisor-gemini-pre",
      "advisor-integration-post","advisor-integration-pre","advisor-maintainability-post",
      "advisor-maintainability-pre","advisor-security-post","advisor-security-pre",
      "advisor-testing-post","advisor-testing-pre","bug-reproduction-validator",
      "correctness-reviewer","explore","frontend-apply","frontend-apply-local","frontend-dev",
      "frontend-dev-premium","gentle-ai-worker","gentle-ai-worker-local","gentle-ai-verify",
      "gentle-ai-verify-routine","gentle-ai-verify-astra","planner","project-standards-reviewer","repo-research-analyst",
      "systematic-implementer","testing-reviewer",
    ]),
  }
  const taskOf=(name)=>agents?.[name]?.permission?.task
  const orchestratorTask=taskOf("gentle-orchestrator")
  if (!orchestratorTask || typeof orchestratorTask!=="object" || Array.isArray(orchestratorTask)) failures.push("ORCHESTRATOR_TASK_MAP_MISSING")
  else for (const pm of pmAgents) if (orchestratorTask[pm]!=="allow") failures.push(`COORDINATOR_PM_NOT_DISPATCHABLE: ${pm}`)
  for (const [name,agent] of Object.entries(agents??{})) {
    const task=agent?.permission?.task
    if (!task || typeof task!=="object" || Array.isArray(task)) continue
    for (const coordinator of coordinatorAgents) {
      if (name==="gentle-orchestrator" && coordinator!=="gentle-orchestrator") continue
      if (task[coordinator]==="allow") failures.push(`COORDINATOR_SELF_OR_DEEP_DISPATCH: ${name}.${coordinator}`)
    }
    // The tiny-fix `general` exception belongs to the orchestrator alone.
    if (task["general"]==="allow" && name!=="gentle-orchestrator") failures.push(`GENERAL_DISPATCH_OUTSIDE_TINY_FIX: ${name}`)
  }
  for (const pm of pmAgents) {
    const task=taskOf(pm)
    if (!task || task["*"]!=="deny") failures.push(`PM_TASK_WILDCARD_NOT_DENIED: ${pm}`)
    const allowed=pmMaximum[pm]
    for (const key of Object.keys(task??{})) if (!allowed.has(key)) failures.push(`PM_TASK_GRANT_UNDECLARED: ${pm}.${key}`)
    for (const required of pmRequired[pm]) if (task?.[required]!=="allow") failures.push(`PM_REQUIRED_DISPATCH_MISSING: ${pm}.${required}`)
  }
  for (const name of ["odd-apply","gentle-ai-worker","gentle-ai-worker-local","gentle-ai-verify","gentle-ai-verify-routine","explore"]) {
    const task=taskOf(name)
    if (task && typeof task==="object" && Object.values(task).some((value)=>value==="allow")) failures.push(`NON_COORDINATOR_TASK_DISPATCH: ${name}`)
  }
  return failures
}
// Q90 T3a2: one canonical raw task-map predicate for review dispatch. The
// orchestrator owns the six relay lanes and denies the six plain lanes. Every
// other agent must not grant a named relay/plain review lane, a partial glob
// that overlaps one of those lanes, an allow wildcard, or a scalar allow. A
// wildcard/scalar ask is also a grant except for the canonical frontend
// coordinator, whose existing wildcard ask is preserved. This is a conservative
// raw-map check, not a runtime permission resolver: cfgPerm does not model
// inherited defaults or glob expansion.
function reviewDispatchFailures(agents, relayReviewAgents, plainProviderReviewAgents) {
  const failures=[]
  const wildcardAskAllowed=(name)=>name==="frontend-dev-premium"
  const protectedReviewLanes=[...relayReviewAgents,...plainProviderReviewAgents]
  const globOverlapsReviewLane=(pattern,lane)=>{
    let source="^"
    for (const char of pattern) {
      if (char==="*") source+=".*"
      else if (char==="?") source+="."
      else source+=char.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")
    }
    return new RegExp(source+"$").test(lane)
  }
  const orchestratorTask=agents?.["gentle-orchestrator"]?.permission?.task
  if (!orchestratorTask || typeof orchestratorTask!=="object" || Array.isArray(orchestratorTask)) {
    failures.push("ORCHESTRATOR_TASK_MAP_MISSING")
  } else {
    for (const name of relayReviewAgents) if (orchestratorTask[name]!=="allow") failures.push(`RELAY_TASK_NOT_ALLOWED: ${name}`)
    for (const name of plainProviderReviewAgents) if (orchestratorTask[name]!=="deny") failures.push(`PLAIN_PROVIDER_REVIEW_TASK_NOT_DENIED: ${name}`)
  }
  for (const [agentName,agent] of Object.entries(agents??{})) {
    if (agentName==="gentle-orchestrator") continue
    const delegated=agent?.permission?.task
    if (delegated===undefined) continue
    if (delegated===null || typeof delegated!=="object" || Array.isArray(delegated)) {
      if (delegated==="allow" || (delegated==="ask" && !wildcardAskAllowed(agentName))) failures.push(`REVIEW_TASK_GRANTED_OUTSIDE_ORCHESTRATOR: ${agentName}="${delegated}"`)
      else if (delegated!=="ask" && delegated!==false && delegated!=="deny") failures.push(`REVIEW_TASK_MAP_INVALID: ${agentName}`)
      continue
    }
    for (const [target,value] of Object.entries(delegated)) {
      if (target==="*") {
        if (value==="allow" || (value==="ask" && !wildcardAskAllowed(agentName))) failures.push(`REVIEW_TASK_GRANTED_OUTSIDE_ORCHESTRATOR: ${agentName}.*="${value}"`)
        else if (value!=="ask" && value!==false && value!=="deny") failures.push(`REVIEW_TASK_MAP_INVALID: ${agentName}.*`)
        continue
      }
      const namedReviewLane=target.startsWith("asi-review-")||target.startsWith("review-")
      if (!namedReviewLane && !protectedReviewLanes.some((lane)=>globOverlapsReviewLane(target,lane))) continue
      if (value!=="deny" && value!==false) failures.push(`REVIEW_TASK_GRANTED_OUTSIDE_ORCHESTRATOR: ${agentName}.${target}="${value}"`)
    }
  }
  return failures
}
function reviewAgentLockdownFailures(name,agent) {
  const failures=[]
  if (!agent?.tools || typeof agent.tools!=="object" || Array.isArray(agent.tools)) {
    failures.push(`REVIEW_AGENT_LOCKDOWN_CONFIG_OBJECT_MISSING: ${name} tools`)
  }
  if (!agent?.permission || typeof agent.permission!=="object" || Array.isArray(agent.permission)) {
    failures.push(`REVIEW_AGENT_LOCKDOWN_CONFIG_OBJECT_MISSING: ${name} permission`)
  }
  for (const tool of Object.keys(agent?.tools??{})) {
    if (cfgTool(agent,tool)!==false) failures.push(`REVIEW_AGENT_TOOL_EXPOSED: ${name} ${tool}`)
  }
  const checkPermissions=(permissions,path="permission")=>{
    for (const [permission,value] of Object.entries(permissions??{})) {
      const permissionPath=`${path}.${permission}`
      if (value && typeof value==="object" && !Array.isArray(value)) checkPermissions(value,permissionPath)
      else if (value!=="deny") failures.push(`REVIEW_AGENT_PERMISSION_NOT_DENIED: ${name} ${permissionPath}`)
    }
  }
  checkPermissions(agent?.permission)
  return failures
}
const reviewAgentProbeFailures=reviewAgentLockdownFailures("positive-control",{
  tools:{"synthetic-enabled-tool":true},
  permission:{"synthetic-permission":"allow"},
})
const expectedReviewAgentProbeFailures=[
  "REVIEW_AGENT_TOOL_EXPOSED: positive-control synthetic-enabled-tool",
  "REVIEW_AGENT_PERMISSION_NOT_DENIED: positive-control permission.synthetic-permission",
]
if (expectedReviewAgentProbeFailures.some((failure)=>!reviewAgentProbeFailures.includes(failure))) {
  fail(`REVIEW_AGENT_LOCKDOWN_POSITIVE_CONTROL_FAILED: ${JSON.stringify(reviewAgentProbeFailures)}`)
} else {
  console.log(`   ok: review-agent lockdown positive control detected ${JSON.stringify(expectedReviewAgentProbeFailures)}`)
}
const omittedReviewAgentProbeFailures=reviewAgentLockdownFailures("positive-control-omitted-objects",{})
const expectedOmittedReviewAgentProbeFailures=[
  "REVIEW_AGENT_LOCKDOWN_CONFIG_OBJECT_MISSING: positive-control-omitted-objects tools",
  "REVIEW_AGENT_LOCKDOWN_CONFIG_OBJECT_MISSING: positive-control-omitted-objects permission",
]
if (expectedOmittedReviewAgentProbeFailures.some((failure)=>!omittedReviewAgentProbeFailures.includes(failure))) {
  fail(`REVIEW_AGENT_LOCKDOWN_OMITTED_OBJECT_POSITIVE_CONTROL_FAILED: ${JSON.stringify(omittedReviewAgentProbeFailures)}`)
} else {
  console.log(`   ok: review-agent lockdown positive control detected ${JSON.stringify(expectedOmittedReviewAgentProbeFailures)}`)
}
function assertCfgWriter(name) {
  const a=deployedAgents[name]; if (!a) { fail(`SANDBOX_WRITER_MISSING: ${name}`); return }
  if (cfgPerm(a,"edit")!=="deny" || cfgPerm(a,"write")!=="deny") fail(`HOST_WRITE_EXPOSED: ${name}`)
  if (cfgPerm(a,"bash")!=="deny") fail(`HOST_BASH_WRITER_NOT_DISABLED: ${name}`)
  if (cfgTool(a,"edit")===true || cfgTool(a,"write")===true || cfgTool(a,"bash")===true) fail(`LEGACY_HOST_TOOL_EXPOSED: ${name}`)
  for (const t of ["sandbox_read","sandbox_list","sandbox_grep","sandbox_diff","sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch"]) {
    if (cfgPerm(a,t)!=="allow" || cfgTool(a,t)===false) fail(`SANDBOX_WRITER_TOOL_MISSING: ${name}.${t}`)
  }
  for (const t of ["sandbox_apply","sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_finish"]) {
    if (cfgPerm(a,t)!=="ask" || cfgTool(a,t)===false) fail(`SANDBOX_BOUNDARY_NOT_GATED: ${name}.${t}`)
  }
  if (cfgTool(a,"*")===false) fail(`CUSTOM_TOOL_SURFACE_DISABLED: ${name}`)
}
for (const name of ["frontend-apply","frontend-apply-local","general","jd-fix-agent","odd-apply","gentle-ai-worker","gentle-ai-worker-local"]) assertCfgWriter(name)

// gentle-ai v4 generic agents: registration + tool shape. The two writers are
// fully covered by assertCfgWriter above; the read-only explorer and the
// read-only verifier that may only run sandbox_bash must expose exactly those
// tools and no mutation surface.
const v4GenericAgents=["gentle-ai-explore","gentle-ai-worker","gentle-ai-worker-local","gentle-ai-verify","gentle-ai-verify-routine"]
for (const name of v4GenericAgents) if (!deployedAgents[name]) fail(`V4_GENERIC_AGENT_TOOL_MISSING: ${name} is not registered`)
const v4ReadTools=["sandbox_read","sandbox_list","sandbox_grep","sandbox_diff"]
const v4MutationTools=["sandbox_edit","sandbox_write","sandbox_apply_patch","sandbox_apply","sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_finish"]
for (const name of v4ReadTools) {
  if (cfgTool(deployedAgents["gentle-ai-explore"],name)!==true) fail(`V4_GENERIC_AGENT_TOOL_MISSING: gentle-ai-explore.${name}`)
  for (const verifier of ["gentle-ai-verify","gentle-ai-verify-routine"]) {
    if (cfgTool(deployedAgents[verifier],name)!==true) fail(`V4_GENERIC_AGENT_TOOL_MISSING: ${verifier}.${name}`)
  }
}
for (const name of ["sandbox_bash",...v4MutationTools]) {
  if (cfgTool(deployedAgents["gentle-ai-explore"],name)!==false) fail(`V4_GENERIC_AGENT_TOOL_MISSING: gentle-ai-explore.${name} must be false`)
}
for (const verifier of ["gentle-ai-verify","gentle-ai-verify-routine"]) {
  if (cfgTool(deployedAgents[verifier],"sandbox_bash")!==true) fail(`V4_GENERIC_AGENT_TOOL_MISSING: ${verifier}.sandbox_bash`)
  for (const name of v4MutationTools) {
    if (cfgTool(deployedAgents[verifier],name)!==false) fail(`V4_GENERIC_AGENT_TOOL_MISSING: ${verifier}.${name} must be false`)
  }
}

const pmAndAgents=[...pmAgents]
const pmNoExecutionTools=["sandbox_write","sandbox_edit","sandbox_apply_patch","sandbox_apply","sandbox_bash","sandbox_finish","sandbox_discard","sandbox_copy_in","sandbox_copy_out","bash","edit","write"]
const pmNoSandboxReadTools=["sandbox_read","sandbox_list","sandbox_grep","sandbox_diff"]
for (const name of pmAndAgents) {
  const pm=deployedAgents[name]
  if (!pm) { fail(`PM_AGENT_MISSING: ${name}`); continue }
  for (const t of pmNoExecutionTools) {
    if (cfgPerm(pm,t)!=="deny" || cfgTool(pm,t)===true) fail(`PM_EXECUTION_TOOL_EXPOSED: ${name}.${t}`)
  }
  for (const t of pmNoSandboxReadTools) {
    if (Object.prototype.hasOwnProperty.call(pm.tools??{},t) || Object.prototype.hasOwnProperty.call(pm.permission??{},t)) {
      fail(`PM_SANDBOX_READ_TOOL_PRESENT: ${name}.${t}`)
    }
  }
}

// gentle-ai v4 retired SDD. No `sdd-*` agent may reappear, no `host_sdd_*`
// read may stay in registeredHostReads, and every `host_sdd_*` permission must
// stay `deny` for the global defaults, the orchestrator and every pm-*
// coordinator. Because those reads are deliberately NOT in registeredHostReads
// (which requires `allow`), this deny assertion is their only authority.
for (const name of registeredHostReads) if (name.startsWith("host_sdd_")) fail(`HOST_SDD_READ_STILL_REGISTERED: ${name}`)
for (const name of Object.keys(deployedAgents)) if (name.startsWith("sdd-")) fail(`SDD_AGENT_REAPPEARED: ${name}`)
for (const name of Object.keys(deployedAgents)) if (name==="pm-sdd") fail(`PM_SDD_REAPPEARED: ${name}`)
const hostSddNames=Object.keys(gp).filter((name)=>name.startsWith("host_sdd_")).sort()
for (const name of hostSddNames) {
  if (gp[name]!=="deny") fail(`HOST_SDD_PERMISSION_NOT_DENY: <global defaults>.${name}=${show(gp[name])}`)
}
for (const scopeName of ["gentle-orchestrator",...pmAgents]) {
  const scopeAgent=deployedAgents[scopeName]
  if (!scopeAgent) { fail(`HOST_SDD_PERMISSION_NOT_DENY: ${scopeName} is not registered`); continue }
  const scopePermission=scopeAgent.permission && typeof scopeAgent.permission==="object" ? scopeAgent.permission : {}
  for (const name of hostSddNames) {
    const value=hasOwn(scopePermission,name) ? scopePermission[name] : gp[name]
    if (value!=="deny") fail(`HOST_SDD_PERMISSION_NOT_DENY: ${scopeName}.${name}=${show(value)}`)
  }
}
const reviewRelayAgents=[
  "review-risk","review-resilience","review-readability","review-reliability","review-refuter","review-validator",
  "asi-review-risk","asi-review-resilience","asi-review-readability","asi-review-reliability","asi-review-refuter","asi-review-validator",
]
for (const name of reviewRelayAgents) {
  const agent=deployedAgents[name]
  if (!agent) { fail(`REVIEW_AGENT_MISSING: ${name}`); continue }
  for (const failure of reviewAgentLockdownFailures(name,agent)) fail(failure)
}
const oddApply=deployedAgents["odd-apply"]
if (!oddApply) fail("SANDBOX_WRITER_MISSING: odd-apply")
else {
  const pmTask=cfgPerm(deployedAgents["pm-odd"],"task")
  const orchestratorTask=cfgPerm(deployedAgents["gentle-orchestrator"],"task")
  if (pmTask?.["odd-apply"]!=="allow") fail(`ODD_APPLY_NOT_ALLOWED_TO_PM: pm-odd.odd-apply=${show(pmTask?.["odd-apply"])}`)
  // Q59 correction: PMs keep only their named DeepSeek writers/verifiers. The
  // orchestrator alone owns the `general` tiny-fix lane, so `general` must NOT
  // be required (or granted) on either PM.
  function pmGeneralDispatchFailures(name,task) {
    return task?.["general"]==="allow" ? [`PM_GENERAL_DISPATCH_NOT_ALLOWED: ${name}`] : []
  }
  for (const pm of ["pm-odd","pm-systematic"]) {
    const task=cfgPerm(deployedAgents[pm],"task")
    for (const key of ["gentle-ai-worker","gentle-ai-worker-local","gentle-ai-verify","gentle-ai-verify-routine","gentle-ai-verify-astra"]) {
      if (task?.[key]!=="allow") fail(`TINY_FIX_AGENT_NOT_ALLOWED_TO_PM: ${pm}.${key}=${show(task?.[key])}`)
    }
    for (const failure of pmGeneralDispatchFailures(pm,task)) fail(failure)
    const probe=pmGeneralDispatchFailures(`${pm}-positive-control`,{general:"allow"})
    if (!probe.includes(`PM_GENERAL_DISPATCH_NOT_ALLOWED: ${pm}-positive-control`)) fail(`PM_GENERAL_DISPATCH_POSITIVE_CONTROL_FAILED: ${pm}`)
  }
  if (orchestratorTask?.["odd-apply"]==="allow") fail("ODD_APPLY_ALLOWED_TO_ORCHESTRATOR")
}

// gemini-advisor-route:begin
// Q76: the Argon advisors may only delegate to the Flash evidence gatherer, which keeps the
// shared sandbox-only advisor surface. Only the orchestrator, the PMs, and the Planner dispatch
// the advisors; no other agent may reach the gatherer. None of them may fall back to another model.
// The coordinator set is passed in so tests can execute this block in isolation.
function geminiAdvisorRouteFailures(agents,fallback,coordinatorAgents) {
  const out=[]
  const advisors=["advisor-gemini-pre","advisor-gemini-post"]
  const evidence="advisor-gemini-evidence"
  const grants=new Set(["allow","ask"])
  const hostRoutes=["edit","write","bash","sandbox_apply","sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_finish"]
  const asMap=(value)=>value && typeof value==="object" && !Array.isArray(value) ? value : {}
  const sameMap=(value,expected)=>{
    const actual=asMap(value)
    return Object.keys(actual).length===Object.keys(expected).length && Object.entries(expected).every(([k,v])=>actual[k]===v)
  }
  for (const name of advisors) {
    const a=agents?.[name]
    if (!a || typeof a!=="object") { out.push(`GEMINI_ADVISOR_MISSING: ${name}`); continue }
    if (a.model!=="google/gemini-4-argon") out.push(`GEMINI_ADVISOR_MODEL_MISMATCH: ${name}=${JSON.stringify(a.model)}`)
    const tools=asMap(a.tools), perms=asMap(a.permission)
    if (tools["*"]!==false || tools.task!==true) out.push(`GEMINI_ADVISOR_TOOL_SURFACE_MISMATCH: ${name}`)
    for (const [t,v] of Object.entries(tools)) if (v===true && t!=="task") out.push(`GEMINI_ADVISOR_TOOL_EXPOSED: ${name}.${t}`)
    for (const [t,v] of Object.entries(perms)) if (t!=="task" && grants.has(v)) out.push(`GEMINI_ADVISOR_TOOL_EXPOSED: ${name}.${t}`)
    if (!sameMap(perms.task,{"*":"deny",[evidence]:"allow"})) out.push(`GEMINI_ADVISOR_TASK_SCOPE_MISMATCH: ${name}=${JSON.stringify(perms.task)}`)
    if (perms.ctx_memory!=="deny") out.push(`GEMINI_ADVISOR_MEMORY_EXPOSED: ${name}`)
  }
  const gatherer=agents?.[evidence]
  if (!gatherer || typeof gatherer!=="object") out.push(`GEMINI_EVIDENCE_MISSING: ${evidence}`)
  else {
    if (gatherer.model!=="google/gemini-3.8-flash") out.push(`GEMINI_EVIDENCE_MODEL_MISMATCH: ${evidence}=${JSON.stringify(gatherer.model)}`)
    const tools=asMap(gatherer.tools), perms=asMap(gatherer.permission)
    for (const t of hostRoutes) if (tools[t]===true || perms[t]!=="deny") out.push(`GEMINI_EVIDENCE_HOST_ROUTE_EXPOSED: ${evidence}.${t}`)
    if (tools.task!==false || !sameMap(perms.task,{"*":"deny"})) out.push(`GEMINI_EVIDENCE_TASK_NOT_DENIED: ${evidence}`)
    if (perms.ctx_memory!=="deny") out.push(`GEMINI_EVIDENCE_MEMORY_EXPOSED: ${evidence}`)
  }
  for (const dispatcher of coordinatorAgents) {
    const task=asMap(asMap(agents?.[dispatcher]?.permission).task)
    for (const name of advisors) if (task[name]!=="allow") out.push(`GEMINI_ADVISOR_NOT_DISPATCHABLE: ${dispatcher}.${name}`)
  }
  for (const [name,a] of Object.entries(asMap(agents))) {
    if (advisors.includes(name)) continue
    const task=a?.permission?.task
    if (!task || typeof task!=="object" || Array.isArray(task)) continue
    if (!coordinatorAgents.includes(name)) {
      for (const advisor of advisors) {
        const effectiveAdvisor=Object.prototype.hasOwnProperty.call(task,advisor) ? task[advisor] : task["*"]
        if (effectiveAdvisor==="allow") out.push(`GEMINI_ADVISOR_DISPATCHABLE: ${name}.${advisor}='allow'`)
      }
    }
    const effective=Object.prototype.hasOwnProperty.call(task,evidence) ? task[evidence] : task["*"]
    if (effective!=="deny") out.push(`GEMINI_EVIDENCE_DISPATCHABLE: ${name}=${JSON.stringify(effective)}`)
  }
  const noFallback=Array.isArray(fallback?.noFallbackAgents) ? fallback.noFallbackAgents : []
  for (const name of [...advisors,evidence]) if (!noFallback.includes(name)) out.push(`GEMINI_ADVISOR_FALLBACK_ALLOWED: ${name}`)
  return out
}
// gemini-advisor-route:end
{
  let geminiFallback
  try { geminiFallback=parseJsonc(fallbackPolicySourcePath) } catch { geminiFallback=undefined }
  for (const failure of geminiAdvisorRouteFailures(deployedAgents,geminiFallback,advisorDispatchAgents)) fail(failure)
  const controlFailures=geminiAdvisorRouteFailures({},{},coordinatorAgents)
  if (!controlFailures.includes("GEMINI_ADVISOR_MISSING: advisor-gemini-pre") || !controlFailures.includes("GEMINI_EVIDENCE_MISSING: advisor-gemini-evidence")) {
    fail(`GEMINI_ADVISOR_ROUTE_POSITIVE_CONTROL_FAILED: ${JSON.stringify(controlFailures)}`)
  } else {
    console.log("   ok: Gemini advisor route shape, dispatch scope and no-fallback policy")
  }
}

// planner-handoff:begin
function plannerHandoffFailures(agents,gp) {
  const failures=[]
  const planner=agents?.["planner"]
  const evidence=agents?.["planner-evidence"]
  const advisors=[
    "advisor-design-pre","advisor-integration-pre","advisor-testing-pre","advisor-security-pre",
    "advisor-maintainability-pre","advisor-design-post","advisor-integration-post",
    "advisor-testing-post","advisor-security-post","advisor-maintainability-post",
    "advisor-gemini-pre","advisor-gemini-post",
  ]
  const writers=["odd-apply","gentle-ai-worker","gentle-ai-worker-local","gentle-ai-verify","gentle-ai-verify-routine","general","frontend-apply","frontend-apply-local","frontend-dev","systematic-implementer"]
  const readTools=["read","codegraph_codegraph_explore","ast_grep_search","aft_outline","aft_zoom","aft_search","aft_callgraph","aft_inspect","sandbox_read","sandbox_list","sandbox_grep","sandbox_diff"]
  const mutationTools=["bash","edit","write","sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch","sandbox_apply","sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_finish","aft_import","aft_safety","ast_grep_replace"]
  const plannerCoordinators=["gentle-orchestrator","pm-odd"]
  plannerCoordinators.push("pm-systematic")
  const sameMap=(value,expected)=>{
    const actual=value && typeof value==="object" && !Array.isArray(value) ? value : {}
    return Object.keys(actual).length===Object.keys(expected).length && Object.entries(expected).every(([key,val])=>actual[key]===val)
  }
  const readSurface=(name,agent)=>{
    for (const tool of readTools) {
      if (cfgTool(agent,tool)!==true) failures.push(`PLANNER_READ_TOOL_MISSING: ${name}.${tool}`)
      if (cfgPerm(agent,tool)!=="allow") failures.push(`PLANNER_READ_PERMISSION_MISSING: ${name}.${tool}`)
    }
  }
  if (!planner || typeof planner!=="object" || Array.isArray(planner)) failures.push("PLANNER_AGENT_MISSING: planner")
  else {
    if (planner.mode!=="subagent") failures.push(`PLANNER_MODE_MISMATCH: ${show(planner.mode)}`)
    if (planner.hidden!==true) failures.push("PLANNER_NOT_HIDDEN")
    if (planner.model!=="openai/gpt-6.1-sol") failures.push(`PLANNER_MODEL_MISMATCH: ${show(planner.model)}`)
    if (planner.variant!=="high") failures.push(`PLANNER_VARIANT_MISMATCH: ${show(planner.variant)}`)
    readSurface("planner",planner)
    if (cfgTool(planner,"task")!==true) failures.push("PLANNER_TASK_TOOL_NOT_ENABLED")
    const task=planner?.permission?.task
    if (!task || typeof task!=="object" || Array.isArray(task)) failures.push("PLANNER_TASK_MAP_MISSING")
    else {
      if (task["*"]!=="deny") failures.push(`PLANNER_TASK_WILDCARD_NOT_DENIED: ${show(task["*"])}`)
      for (const name of advisors) if (task[name]!=="allow") failures.push(`PLANNER_ADVISOR_LANE_MISSING: ${name}`)
      for (const name of ["planner-evidence","explore"]) if (task[name]!=="allow") failures.push(`PLANNER_EVIDENCE_LANE_MISSING: ${name}`)
      for (const name of writers) if (task[name]==="allow") failures.push(`PLANNER_WRITER_DISPATCH_GRANTED: ${name}`)
      for (const [name,value] of Object.entries(task)) {
        if (name==="*" || advisors.includes(name) || name==="planner-evidence" || name==="explore") continue
        failures.push(`PLANNER_TASK_GRANT_UNDECLARED: ${name}=${show(value)}`)
      }
    }
    for (const tool of mutationTools) {
      if (cfgTool(planner,tool)===true) failures.push(`PLANNER_MUTATION_TOOL_EXPOSED: ${tool}`)
      if (cfgPerm(planner,tool)!=="deny") failures.push(`PLANNER_MUTATION_EXPOSED: ${tool}`)
    }
    if (cfgTool(planner,"grep")!==false || cfgPerm(planner,"grep")!=="deny") failures.push("PLANNER_GREP_EXPOSED")
    if (cfgTool(planner,"ctx_memory")!==false || cfgPerm(planner,"ctx_memory")!=="deny") failures.push("PLANNER_MEMORY_EXPOSED")
    if (cfgTool(planner,"host_plan_write")!==true || cfgPerm(planner,"host_plan_write")!=="ask") failures.push(`PLANNER_HOST_PLAN_WRITE_NOT_ASK: ${show(cfgPerm(planner,"host_plan_write"))}`)
    if (cfgTool(planner,"host_gate_verdict")!==true || cfgPerm(planner,"host_gate_verdict")!=="ask") failures.push(`PLANNER_HOST_GATE_VERDICT_NOT_ASK: ${show(cfgPerm(planner,"host_gate_verdict"))}`)
    if (cfgTool(planner,"host_task_mark")===true || cfgPerm(planner,"host_task_mark")!=="deny") failures.push(`PLANNER_HOST_TASK_MARK_NOT_DENY: ${show(cfgPerm(planner,"host_task_mark"))}`)
  }
  if (!evidence || typeof evidence!=="object" || Array.isArray(evidence)) failures.push("PLANNER_EVIDENCE_AGENT_MISSING: planner-evidence")
  else {
    if (evidence.mode!=="subagent") failures.push(`PLANNER_EVIDENCE_MODE_MISMATCH: ${show(evidence.mode)}`)
    if (evidence.hidden!==true) failures.push("PLANNER_EVIDENCE_NOT_HIDDEN")
    if (evidence.model!=="openai/gpt-6-luna") failures.push(`PLANNER_EVIDENCE_MODEL_MISMATCH: ${show(evidence.model)}`)
    if (evidence.variant!=="medium") failures.push(`PLANNER_EVIDENCE_VARIANT_MISMATCH: ${show(evidence.variant)}`)
    readSurface("planner-evidence",evidence)
    if (cfgTool(evidence,"task")!==false || !sameMap(evidence?.permission?.task,{"*":"deny"})) failures.push("PLANNER_EVIDENCE_TASK_EXPOSED")
    for (const tool of mutationTools) {
      if (cfgTool(evidence,tool)===true) failures.push(`PLANNER_EVIDENCE_MUTATION_EXPOSED: ${tool}`)
      if (cfgPerm(evidence,tool)!=="deny") failures.push(`PLANNER_EVIDENCE_MUTATION_EXPOSED: ${tool}`)
    }
    if (cfgTool(evidence,"grep")!==false || cfgPerm(evidence,"grep")!=="deny") failures.push("PLANNER_EVIDENCE_GREP_EXPOSED")
    if (cfgTool(evidence,"ctx_memory")!==false || cfgPerm(evidence,"ctx_memory")!=="deny") failures.push("PLANNER_EVIDENCE_MEMORY_EXPOSED")
    for (const host of ["host_plan_write","host_gate_verdict","host_task_mark"]) {
      if (cfgPerm(evidence,host)!=="deny") failures.push(`PLANNER_EVIDENCE_HOST_EXPOSED: ${host}`)
    }
  }
  for (const name of plannerCoordinators) {
    if (agents?.[name]?.permission?.task?.planner!=="allow") failures.push(`PLANNER_NOT_DISPATCHABLE: ${name}`)
  }
  for (const [name,agent] of Object.entries(agents??{})) {
    if (plannerCoordinators.includes(name)) continue
    if (agent?.permission?.task?.planner==="allow") failures.push(`PLANNER_DISPATCH_GRANT_OUTSIDE_COORDINATORS: ${name}`)
  }
  if (gp?.host_plan_write!=="deny" || gp?.host_gate_verdict!=="deny" || gp?.host_task_mark!=="deny") failures.push("PLANNER_GLOBAL_HOST_DENY_CHANGED")
  return failures
}
// planner-handoff:end
{
  for (const failure of plannerHandoffFailures(deployedAgents,gp)) fail(failure)
  const control=plannerHandoffFailures({}, {})
  if (!control.includes("PLANNER_AGENT_MISSING: planner") || !control.includes("PLANNER_EVIDENCE_AGENT_MISSING: planner-evidence")) {
    fail(`PLANNER_HANDOFF_POSITIVE_CONTROL_FAILED: ${JSON.stringify(control)}`)
  } else {
    console.log("   ok: Planner handoff models, read-only surface, task lanes and gate host acts")
  }
}
const ordinaryMemoryAgents=new Set([
  "explore","frontend-apply","frontend-apply-local","frontend-dev","frontend-dev-premium","general",
  "gentle-ai-explore","gentle-ai-verify","gentle-ai-verify-routine","gentle-ai-worker","gentle-ai-worker-local",
  "gentle-orchestrator","jd-fix-agent","vision","pm-odd","pm-systematic","odd-apply",
])
const isolatedMemoryAgents=new Set([
  "jd-judge-a","jd-judge-b",
  "review-risk","review-readability","review-reliability",
  "review-resilience","review-refuter","review-validator",
  "advisor-design-pre","advisor-integration-pre","advisor-testing-pre",
  "advisor-security-pre","advisor-maintainability-pre",
  "advisor-design-post","advisor-integration-post","advisor-testing-post",
  "advisor-security-post","advisor-maintainability-post",
  "advisor-gemini-pre","advisor-gemini-post","advisor-gemini-evidence",
  "planner","planner-evidence",
  "asi-review-risk","asi-review-resilience","asi-review-readability",
  "asi-review-reliability","asi-review-refuter","asi-review-validator",
])

for (const [name,a] of Object.entries(deployedAgents)) {
  let expected
  if (isolatedMemoryAgents.has(name)) expected="deny"
  else if (name === "explore") expected="deny"
  else if (ordinaryMemoryAgents.has(name)) expected="allow"
  else {
    fail(`MAGIC_CONTEXT_MEMORY_POLICY_UNCLASSIFIED_AGENT: ${name}`)
  }
  if (expected!==undefined) {
    if (cfgPerm(a,"ctx_memory")!==expected) {
      fail(`MAGIC_CONTEXT_MEMORY_POLICY_MISMATCH: ${name}.permission.ctx_memory expected ${expected}, got ${show(cfgPerm(a,"ctx_memory"))}`)
    }
  }
  if (name!=="gentle-orchestrator" && cfgPerm(a,"host_register_project")!==undefined) {
    fail(`HOST_REGISTER_PROJECT_AGENT_OVERRIDE_FORBIDDEN: ${name}=${show(cfgPerm(a,"host_register_project"))}`)
  }
}

for (const name of ["asi-review-risk","asi-review-resilience","asi-review-readability","asi-review-reliability","asi-review-refuter","asi-review-validator"]) {
  const relay=deployedAgents[name]
  if (!relay || relay.mode!=="subagent" || relay.hidden!==true || cfgTool(relay,"*")!==false || cfgPerm(relay,"ctx_memory")!=="deny" || cfgPerm(relay,"task")?.["*"]!=="deny") fail(`RELAY_AGENT_ISOLATION_MISMATCH: ${name}`)
  for (const t of [...registeredHostReads,...gatedHostMutations,"read","bash","edit","write","sandbox_read","sandbox_bash"]) if (cfgTool(relay,t)===true || cfgPerm(relay,t)==="allow" || cfgPerm(relay,t)==="ask") fail(`RELAY_TOOL_EXPOSED: ${name}.${t}`)
}
for (const name of ["review-risk","review-resilience","review-readability","review-reliability"]) {
  const lens=deployedAgents[name]
  if (!lens || lens.mode!=="subagent" || lens.hidden!==true || cfgTool(lens,"*")!==false || cfgPerm(lens,"ctx_memory")!=="deny") fail(`GENTLE_AI_V3_4_PROVIDER_TASK_AGENT_ISOLATION_MISMATCH: ${name}`)
  for (const t of [...registeredHostReads,...gatedHostMutations,"read","bash","edit","write","task","sandbox_read","sandbox_bash"]) if (cfgTool(lens,t)===true || cfgPerm(lens,t)==="allow" || cfgPerm(lens,t)==="ask") fail(`GENTLE_AI_V3_4_PROVIDER_TASK_TOOL_EXPOSED: ${name}.${t}`)
}

const researcher=deployedAgents["explore"]
if (!researcher) fail("RESEARCHER_FALLBACK_MISSING: explore")
else {
  if (cfgPerm(researcher,"bash")!=="deny") fail("RESEARCHER_HOST_BASH_EXPOSED")
  if (cfgPerm(researcher,"edit")!=="deny" || cfgPerm(researcher,"write")!=="deny") fail("RESEARCHER_HOST_WRITE_EXPOSED")
  if (cfgTool(researcher,"bash")===true || cfgTool(researcher,"edit")===true || cfgTool(researcher,"write")===true) fail("RESEARCHER_LEGACY_HOST_TOOL_EXPOSED")
  for (const t of ["sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch","sandbox_apply","sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_finish"]) {
    if (cfgPerm(researcher,t)!=="deny" || cfgTool(researcher,t)===true) fail(`RESEARCHER_MUTATION_EXPOSED: ${t}`)
  }
}

const orch=deployedAgents["gentle-orchestrator"]
if (!orch) fail("ORCHESTRATOR_MISSING")
else {
  const configuredOrchestratorModel=normalizeModel(orch.model)
  const configuredOrchestratorVariant=typeof orch.variant==="string" ? orch.variant : undefined
  if (!configuredOrchestratorModel) fail(`ORCHESTRATOR_MODEL_NOT_EXPLICIT: ${show(orch.model)}`)
  if (!configuredOrchestratorVariant) fail(`ORCHESTRATOR_VARIANT_NOT_EXPLICIT: ${show(orch.variant)}`)
  if (cfgPerm(orch,"edit")!=="deny" || cfgPerm(orch,"write")!=="deny") fail("ORCHESTRATOR_HOST_WRITE_NOT_DENIED")
  if (cfgPerm(orch,"bash")!=="deny") fail("ORCHESTRATOR_HOST_BASH_NOT_DENIED")
  for (const name of gatedHostMutations) if (name!=="host_review_start" && name!=="host_review_materialize" && name!=="host_review_pipeline_run" && name!=="host_review_diff_read" && cfgPerm(orch,name)!=="ask") fail(`ORCHESTRATOR_HOST_TOOL_NOT_ASK: ${name}`)
  if (cfgPerm(orch,"host_review_start")!=="allow") fail(`ORCHESTRATOR_HOST_REVIEW_START_NOT_ALLOW: ${show(cfgPerm(orch,"host_review_start"))}`)
  for (const failure of hostReviewMaterializeExceptionFailures(gatedHostMutations,orch)) fail(failure)
  for (const failure of hostReviewPipelineRunExceptionFailures(gatedHostMutations,orch)) fail(failure)
  for (const name of retiredHostOperations) if (cfgPerm(orch,name)!=="deny") fail(`ORCHESTRATOR_RETIRED_HOST_TOOL_EXPOSED: ${name}`)
  if (cfgPerm(orch,"host_register_project")!=="ask") fail(`ORCHESTRATOR_HOST_REGISTER_PROJECT_NOT_ASK: ${show(cfgPerm(orch,"host_register_project"))}`)
  for (const failure of hostTestRunOrchestratorFailures(orch)) fail(failure)
  for (const failure of hostPlanWriteOrchestratorFailures(orch)) fail(failure)
  const testRunOmitted=hostTestRunOrchestratorFailures({permission:{}})
  if (!testRunOmitted.includes("ORCHESTRATOR_HOST_TEST_RUN_NOT_ALLOW: <inherit/none>")) fail("ORCHESTRATOR_HOST_TEST_RUN_OMITTED_POSITIVE_CONTROL_FAILED")
  const testRunWrong=hostTestRunOrchestratorFailures({permission:{host_test_run:"ask"}})
  if (!testRunWrong.includes('ORCHESTRATOR_HOST_TEST_RUN_NOT_ALLOW: "ask"')) fail("ORCHESTRATOR_HOST_TEST_RUN_VALUE_POSITIVE_CONTROL_FAILED")
  const planWriteOmitted=hostPlanWriteOrchestratorFailures({permission:{}})
  if (!planWriteOmitted.includes("ORCHESTRATOR_HOST_PLAN_WRITE_NOT_ASK: <inherit/none>")) fail("ORCHESTRATOR_HOST_PLAN_WRITE_OMITTED_POSITIVE_CONTROL_FAILED")
  const planWriteWrong=hostPlanWriteOrchestratorFailures({permission:{host_plan_write:"allow"}})
  if (!planWriteWrong.includes('ORCHESTRATOR_HOST_PLAN_WRITE_NOT_ASK: "allow"')) fail("ORCHESTRATOR_HOST_PLAN_WRITE_VALUE_POSITIVE_CONTROL_FAILED")
  if (cfgTool(orch,"bash")===true || cfgTool(orch,"edit")===true || cfgTool(orch,"write")===true) fail("ORCHESTRATOR_LEGACY_HOST_TOOL_EXPOSED")
  for (const t of ["sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch","sandbox_apply","sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_finish"]) {
    if (cfgPerm(orch,t)!=="deny" || cfgTool(orch,t)===true) fail(`ORCHESTRATOR_MUTATION_EXPOSED: ${t}`)
  }
  const task=cfgPerm(orch,"task")
  if (!task || typeof task!=="object" || task["*"]!=="ask") fail("TASK_FALLBACK_NOT_ASK")
  for (const agent of inventory) if (task?.[agent.name]!=="allow") fail(`TASK_AGENT_NOT_ALLOWED: ${agent.name}`)
  for (const name of ["frontend-dev","frontend-dev-premium"]) {
    if (task?.[name]!=="allow") fail(`FRONTEND_LANE_NOT_ALLOWED: ${name}`)
  }
  for (const failure of reviewDispatchFailures(deployedAgents,relayReviewAgents,plainProviderReviewAgents)) fail(failure)
  const reviewDispatchOrchestratorTask={"*":"ask"}
  for (const name of relayReviewAgents) reviewDispatchOrchestratorTask[name]="allow"
  for (const name of plainProviderReviewAgents) reviewDispatchOrchestratorTask[name]="deny"
  const reviewDispatchGrantProbe=reviewDispatchFailures({
    "gentle-orchestrator":{permission:{task:reviewDispatchOrchestratorTask}},
    "pm-odd":{permission:{task:{"*":"deny","asi-review-risk":"allow"}}},
  },relayReviewAgents,plainProviderReviewAgents)
  if (!reviewDispatchGrantProbe.includes('REVIEW_TASK_GRANTED_OUTSIDE_ORCHESTRATOR: pm-odd.asi-review-risk="allow"')) fail("REVIEW_DISPATCH_GRANT_POSITIVE_CONTROL_FAILED")
  const reviewDispatchScalarProbe=reviewDispatchFailures({
    "gentle-orchestrator":{permission:{task:reviewDispatchOrchestratorTask}},
    "pm-odd":{permission:{task:"ask"}},
  },relayReviewAgents,plainProviderReviewAgents)
  if (!reviewDispatchScalarProbe.includes('REVIEW_TASK_GRANTED_OUTSIDE_ORCHESTRATOR: pm-odd="ask"')) fail("REVIEW_DISPATCH_SCALAR_POSITIVE_CONTROL_FAILED")

  const orchPrompt=typeof orch.prompt==="string" ? orch.prompt : ""
  for (const failure of hostToolPromptFailures(orchPrompt)) fail(failure)
  const orchestratorAssemblerRel="global-config/prompts/gentle-orchestrator/assemble-orchestrator-prompt.py"
  if (!workspaceRootAvailable) {
    // WORKSPACE_ROOT_UNAVAILABLE was already reported above; repo-relative
    // resolution is impossible, so never call path.join with an invalid root.
  } else {
    const orchestratorAssemblerPath=path.join(workspaceRoot,orchestratorAssemblerRel)
    if (!fs.existsSync(orchestratorAssemblerPath)) {
      fail(`ORCHESTRATOR_PROMPT_ASSEMBLER_MISSING: ${orchestratorAssemblerRel}`)
    } else {
      let assembledBytes
      try {
        assembledBytes=execFileSync("python3",[orchestratorAssemblerRel],{cwd:workspaceRoot,maxBuffer:16*1024*1024})
      } catch (error) {
        const assemblerErrorLine=String(error&&error.message?error.message:error).split("\n")[0]
        fail(`ORCHESTRATOR_PROMPT_ASSEMBLER_FAILED: command: python3 ${orchestratorAssemblerRel}; ${assemblerErrorLine}`)
      }
      if (assembledBytes) {
        const embeddedDigest=crypto.createHash("sha256").update(Buffer.from(orchPrompt,"utf8")).digest("hex")
        const assembledDigest=crypto.createHash("sha256").update(assembledBytes).digest("hex")
        if (embeddedDigest!==assembledDigest) {
          fail(`ORCHESTRATOR_PROMPT_ASSEMBLER_DRIFT: embedded=${embeddedDigest} assembled=${assembledDigest}; command: python3 ${orchestratorAssemblerRel}`)
        } else {
          console.log(`   ok: embedded orchestrator prompt equals assembler output (sha256 ${embeddedDigest}; command: python3 ${orchestratorAssemblerRel})`)
        }
        const promptTestSource=fs.readFileSync(path.join(workspaceRoot,"tests/test_orchestrator_prompt_source.py"),"utf8")
        const constantMatch=promptTestSource.match(/CURRENT_PROMPT_SHA256 = "([0-9a-f]{64})"/)
        if (!constantMatch) {
          fail("ORCHESTRATOR_PROMPT_TEST_SHA_CONSTANT_MISSING")
        } else if (constantMatch[1]!==assembledDigest) {
          fail(`ORCHESTRATOR_PROMPT_TEST_SHA_DRIFT: constant=${constantMatch[1]} assembled=${assembledDigest}`)
        } else {
          console.log(`   ok: prompt test constant matches assembled sha256 ${assembledDigest}`)
        }
      }
    }
  }
  const forbiddenPromptFragments=[
    "Implementation runs as **direct inline**",
    "Write one mechanical, already-understood file | ✅",
    "Bash for state (`git`, `gh`) | ✅",
    "Keep one mechanical, already-understood file change inline",
    "Direct inline:"
  ]
  for (const fragment of forbiddenPromptFragments) {
    if (orchPrompt.includes(fragment)) fail(`ORCHESTRATOR_PROMPT_INLINE_DRIFT: forbidden managed prompt fragment reappeared: ${JSON.stringify(fragment)}`)
  }
  if (!orchPrompt.includes("### Secure Read-only Orchestrator Boundary") ||
      !orchPrompt.includes("It has no native host Bash, native edit/write/apply-patch, sandbox shell, or sandbox mutation/lifecycle authority.") ||
      !orchPrompt.includes("delegated to a sandbox writer/executor")) {
    fail("ORCHESTRATOR_PROMPT_BOUNDARY_MISSING: dedicated prompt no longer encodes strict read-only/delegated execution")
  }
  const technicalLeadContractRequired=[
    "### Secure Technical-Lead Contract (MANDATORY)",
    "Read-only is an authority boundary, not a reasoning-depth boundary.",
    "must not degrade into blind routing",
    "issue a proportionate implementation contract",
    "Do not reimplement or duplicate a specialist's completed work",
    "Difficult or disputed architecture uses the configured advisor/deliberation route"
  ]
  const missingTechnicalLeadContract=technicalLeadContractRequired.filter((fragment)=>!orchPrompt.includes(fragment))
  if (missingTechnicalLeadContract.length) {
    fail(`ORCHESTRATOR_TECHNICAL_LEAD_CONTRACT_MISSING: missing=${JSON.stringify(missingTechnicalLeadContract)}`)
  }
  const frontendEscalationRequired=[
    "### Frontend / UI Lane and Premium Escalation",
    "use `frontend-dev` as the normal design/verify lane",
    "`frontend-dev-premium`",
    "major redesign",
    "materially ambiguous UX/product decisions",
    "failed to converge after two substantive visual iteration rounds"
  ]
  const missingFrontendEscalation=frontendEscalationRequired.filter((fragment)=>!orchPrompt.includes(fragment))
  if (missingFrontendEscalation.length) {
    fail(`ORCHESTRATOR_FRONTEND_ESCALATION_CONTRACT_MISSING: missing=${JSON.stringify(missingFrontendEscalation)}`)
  }
  const v3Required=[
    "### Secure Route Loading and Task Classification (MANDATORY)",
    "## Implementation Routing",
    "### ODD protocol",
    "Authorize → Explore → Resolve uncertainty → Classify → Track → Implement → Close",
    "ODD_TASKS key=odd/{project}/{feature-name}/tasks",
    "before the first implementation source edit",
    "route: delegated",
    "actual named Task dispatch and result",
    "SEARCH CONTRACT: AFT=navigation; CodeGraph=relationships/impact; AST-grep=structure; sandbox_grep=bounded literal fallback; native grep unavailable; no shell-search bypass.",
    "EXTERNAL_CONTEXT_REQUIRED",
    'skill({name:"workflow-route"})',
    "load it again after compaction",
    "basis: WORKFLOW.md",
    "ROUTE: <class> | intent: <read-only/authorized change>",
    "gentle-ai review mode status",
    "deciding source",
    "#### Secure Native Review Boundary (MANDATORY)",
    "Native RAR owns verification applicability",
    "--base-ref <last reviewed boundary> --committed-only --json",
    "--agent opencode",
    "candidate.consumed",
    "review_due",
    "review_due_reason",
    "next_transition.command",
    "gentle-ai.review-integration.status/v8",
    "provider_task.agent",
    "provider_task.prompt",
    "grouped wave without waiting between launches",
    "correction_context_budget_exceeded",
    "lens_context_budget_exceeded",
    "Map `provider_task.agent` to the relay lane (`review-<lens>` -> `asi-review-<lens>`, `review-refuter` -> `asi-review-refuter`, `review-validator` -> `asi-review-validator`) and copy `provider_task.prompt` unchanged",
    "two transports cannot own one Task",
    "never grant review lanes to implementation workers or isolated reviewers",
    "asi-review-*",
    "#### Secure Advisory Lifecycle (MANDATORY)",
    "### Secure Fixed Host Tools and Review Relay",
    "### Secure Always-Delegate Rules (MANDATORY)",
    "the orchestrator coordinates; specialist agents execute",
    "PR creation, push, and merge require separate user intent",
    "may draft plan documents through the ask-gated `host_plan_write` fixed tool",
    "plan documents only, never code or configuration",
    "narrowly defined, pre-registered tests through the allow-gated `host_test_run` fixed tool",
    "never arbitrary caller argv, pipes, redirects, or shell",
    "a failed or unavailable test run is evidence, never permission to widen authority",
    "`host_test_run` is not implemented in the current surface and remains inert until the host tool ships"
  ]
  for (const fragment of v3Required) if (!orchPrompt.includes(fragment)) fail(`GENTLE_AI_V3_ORCHESTRATOR_CONTRACT_MISSING: ${JSON.stringify(fragment)}`)
  for (const retired of ["### Gentle AI v2.7 workflow compatibility", "### Research and Pre-Proposal Gate — Gentle AI v2.7", "### Native Runtime Attempt Authority", "confirmed preproposal + explore", "400-line budget risk: High"]) if (orchPrompt.includes(retired)) fail(`GENTLE_AI_V3_RETIRED_ORCHESTRATOR_GATE: ${JSON.stringify(retired)}`)
  for (const retired of ["generated negotiated v2.1 lifecycle", "creates or discovers the terminal receipt", "staged_delivery_candidate_required", "must never substitute for a v8 `provider_task.agent`", "copy `provider_task.agent` unchanged as `subagent_type`"]) {
    if (orchPrompt.includes(retired)) fail(`GENTLE_AI_RETIRED_REVIEW_CONTRACT_PRESENT: ${JSON.stringify(retired)}`)
  }
  const retiredSddOrchestratorFragments=[
    "SDD_ARTIFACT key=",
    "### Dependency Graph — Gentle AI 3.5.0",
    "optional research → propose",
    "optional verify → archive",
    "Inside SDD, do not start review",
    "/sdd-new",
    "/sdd-continue",
    "workflow-sdd-secure",
    "artifact-store"
  ]
  for (const fragment of retiredSddOrchestratorFragments) {
    if (orchPrompt.includes(fragment)) fail(`ORCHESTRATOR_PROMPT_RETIRED_SDD_FRAGMENT_PRESENT: ${JSON.stringify(fragment)}`)
  }
  const magicContextContractRequired=[
    "### Secure Magic Context Contract (MANDATORY)",
    "Magic Context is the primary and mandatory project context/memory layer",
    "ctx_search",
    "ctx_expand",
    "ctx_memory",
    "The subagent returns learnings as text; the orchestrator persists only the evidence-backed durable ones via `ctx_memory`",
    "Isolated evaluation actors (review lanes, refuters, validators, judges) remain memory-write denied",
    "### Secure Project Registration",
    "`host_register_project`",
    "only `gentle-orchestrator` receives `host_register_project: ask`",
    "Remote creation"
  ]
  const missingMagicContextContract=magicContextContractRequired.filter((fragment)=>!orchPrompt.includes(fragment))
  if (missingMagicContextContract.length) {
    fail(`MAGIC_CONTEXT_ORCHESTRATOR_CONTRACT_MISSING: missing=${JSON.stringify(missingMagicContextContract)}`)
  }
  // R4-001: the Secure Magic Context Contract section may be followed by a
  // heading of any level, so the scrub lookahead must accept #{1,6}. Scrubbing
  // is a precondition for the legacy-memory drift check, so require that the
  // section is present and that the scrub actually removed it; a silent no-op
  // must never let the drift check pass.
  const magicContextHeadingRe=/### Secure Magic Context Contract \(MANDATORY\)/
  if (!magicContextHeadingRe.test(orchPrompt)) {
    fail("MAGIC_CONTEXT_SECTION_MISSING: orchestrator prompt has no Secure Magic Context Contract section to scrub")
  }
  const scrubbedOrchPrompt=orchPrompt.replace(/### Secure Magic Context Contract \(MANDATORY\)[\s\S]*?(?=\n#{1,6} )/, "")
  if (magicContextHeadingRe.test(orchPrompt) && scrubbedOrchPrompt === orchPrompt) {
    fail("MAGIC_CONTEXT_SECTION_SCRUB_NOOP: Secure Magic Context Contract section was not removed before the legacy-memory drift check")
  }
  const legacyMemoryPatterns=[
    /Search Engram:/,
    /Artifacts:\s*OpenSpec,\s*Engram,\s*Both/,
    /Engram Topic Key Format/,
    /mem_search\s*\(/,
    /mem_get_observation\s*\(/,
    /mem_save\s*\(/,
    /mem_update\s*\(/
  ]
  for (const rx of legacyMemoryPatterns) {
    if (rx.test(scrubbedOrchPrompt)) fail(`LEGACY_ENGRAM_ORCHESTRATOR_DRIFT: ${rx}`)
  }
}

function assertDirectAgentModelMatchesConfig(name) {
  const configured=deployedAgents[name]
  if (!configured || typeof configured!=="object") {
    fail(`DIRECT_MODEL_AGENT_MISSING: ${name}`)
    return
  }
  const actual=readDebug(name)
  if (!actual) return
  const expectedModel=normalizeModel(configured.model)
  const runtimeModel=normalizeModel(actual.model)
  if (!expectedModel) fail(`DIRECT_MODEL_NOT_EXPLICIT: ${name}=${show(configured.model)}`)
  else if (runtimeModel!==expectedModel) {
    fail(`DIRECT_RUNTIME_MODEL_MISMATCH: ${name}: opencode.json=${show(expectedModel)} runtime=${show(runtimeModel)}`)
  } else {
    console.log(`   ok: ${name} runtime model matches opencode.json (${expectedModel})`)
  }
  if (hasOwn(configured,"variant")) {
    const expectedVariant=configured.variant==null?undefined:configured.variant
    const runtimeVariant=typeof actual.variant==="string"?actual.variant:undefined
    if (runtimeVariant!==expectedVariant) {
      fail(`DIRECT_RUNTIME_VARIANT_MISMATCH: ${name}: opencode.json=${show(expectedVariant)} runtime=${show(runtimeVariant)}`)
    } else {
      console.log(`   ok: ${name} runtime variant matches opencode.json (${show(expectedVariant)})`)
    }
  }
}
for (const name of ["frontend-dev","frontend-dev-premium","jd-judge-b","general","gentle-ai-explore","gentle-ai-worker","gentle-ai-worker-local","gentle-ai-verify","gentle-ai-verify-routine"]) {
  assertDirectAgentModelMatchesConfig(name)
}

const orchRuntime=readDebug("gentle-orchestrator")
if (orchRuntime) {
  const configuredOrchestratorModel=normalizeModel(deployedAgents["gentle-orchestrator"]?.model)
  const configuredOrchestratorVariant=typeof deployedAgents["gentle-orchestrator"]?.variant==="string"
    ? deployedAgents["gentle-orchestrator"].variant
    : undefined
  const runtimeOrchestratorModel=normalizeModel(orchRuntime.model)
  const runtimeOrchestratorVariant=typeof orchRuntime.variant==="string" ? orchRuntime.variant : undefined

  if (runtimeOrchestratorModel!==configuredOrchestratorModel) {
    fail(`ORCHESTRATOR_RUNTIME_MODEL_MISMATCH: opencode.json=${show(configuredOrchestratorModel)} runtime=${show(runtimeOrchestratorModel)}`)
  } else {
    console.log(`   ok: orchestrator runtime model matches opencode.json (${configuredOrchestratorModel})`)
  }
  if (runtimeOrchestratorVariant!==configuredOrchestratorVariant) {
    fail(`ORCHESTRATOR_RUNTIME_VARIANT_MISMATCH: opencode.json=${show(configuredOrchestratorVariant)} runtime=${show(runtimeOrchestratorVariant)}`)
  } else {
    console.log(`   ok: orchestrator runtime variant matches opencode.json (${configuredOrchestratorVariant})`)
  }

  assertPermissionFullyDenied(orchRuntime, "edit", "ORCHESTRATOR_HOST_EDIT_NOT_DENIED")
  if (permissionActionForWildcard(orchRuntime,"grep")!=="ask") {
    fail(`ORCHESTRATOR_NATIVE_GREP_NOT_ASK: ${show(permissionActionForWildcard(orchRuntime,"grep"))}`)
  }
  if (tool(orchRuntime,"bash")!==false && permissionActionForWildcard(orchRuntime,"bash")!=="deny") {
    fail("ORCHESTRATOR_HOST_BASH_NOT_DENIED_RUNTIME")
  }
  for (const t of ["sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch","sandbox_apply","sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_finish"]) {
    if (tool(orchRuntime,t)!==false) fail(`ORCHESTRATOR_RUNTIME_TOOL_EXPOSED: ${t}`)
  }
  if (tool(orchRuntime,"task")!==true) fail("ORCHESTRATOR_TASK_RUNTIME_DISABLED")

  // host_register_project is a context-dependent custom host-control tool. A
  // neutral `opencode debug agent` invocation may not register the tool at all,
  // in which case debug.tools.host_register_project is undefined. The resolved
  // permission ruleset is authoritative for who may invoke it when present.
  const hostRegisterOrchPermission=permissionActionForWildcard(orchRuntime,"host_register_project")
  if (hostRegisterOrchPermission!=="ask") {
    fail(`ORCHESTRATOR_HOST_REGISTER_PROJECT_RUNTIME_NOT_ASK: ${show(hostRegisterOrchPermission)}`)
  }
  const hostRegisterOrchTool=tool(orchRuntime,"host_register_project")
  if (hostRegisterOrchTool===false) {
    fail("ORCHESTRATOR_HOST_REGISTER_PROJECT_REGISTERED_BUT_DISABLED")
  } else if (hostRegisterOrchTool===undefined) {
    console.log("   info: host_register_project not registered in neutral orchestrator debug context; resolved permission=ask")
  } else {
    console.log("   ok: host_register_project registered for orchestrator with resolved permission=ask")
  }

  // Keep deterministic runtime checks to local/in-process intelligence tools.
  // Context7 is remote and CodeGraph is project-scoped, so those are validated
  // at configuration/permission level below rather than making startup health
  // depend on network/service availability from the neutral probe cwd.
  for (const t of [
    "aft_inspect","aft_outline","aft_zoom","ast_grep_search",
    "ctx_expand","ctx_search","ctx_memory",
    "systematic_skill",
    "sandbox_read","sandbox_list","sandbox_grep","sandbox_diff"
  ]) {
    if (tool(orchRuntime,t)!==true) fail(`ORCHESTRATOR_READ_TOOL_MISSING: ${t}`)
  }
}
const generalRuntime=readDebug("general")
if (generalRuntime) {
  assertPermissionFullyDenied(generalRuntime, "edit", "GENERAL_HOST_EDIT_NOT_DENIED")
  if (permissionActionForWildcard(generalRuntime,"grep")!=="deny" || tool(generalRuntime,"grep")===true) {
    fail("GENERAL_NATIVE_GREP_EXPOSED")
  }
  if (tool(generalRuntime,"bash")!==false && permissionActionForWildcard(generalRuntime,"bash")!=="deny") {
    fail("GENERAL_HOST_BASH_EXPOSED")
  }
  for (const t of ["sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch"]) {
    if (tool(generalRuntime,t)!==true) fail(`GENERAL_SANDBOX_TOOL_MISSING: ${t}`)
  }
  for (const t of ["ctx_search","ctx_expand","ctx_memory"]) {
    if (tool(generalRuntime,t)!==true) fail(`GENERAL_MAGIC_CONTEXT_TOOL_MISSING: ${t}`)
  }
  const hostRegisterGeneralPermission=permissionActionForWildcard(generalRuntime,"host_register_project")
  if (hostRegisterGeneralPermission!=="deny") {
    fail(`GENERAL_HOST_REGISTER_PROJECT_RUNTIME_NOT_DENY: ${show(hostRegisterGeneralPermission)}`)
  }
  const hostRegisterGeneralTool=tool(generalRuntime,"host_register_project")
  if (hostRegisterGeneralTool===true) {
    fail("GENERAL_HOST_REGISTER_PROJECT_REGISTERED_AND_EXPOSED")
  } else if (hostRegisterGeneralTool===undefined) {
    console.log("   info: host_register_project not registered in neutral general debug context; resolved permission=deny")
  }
}

const researcherRuntime=readDebug("explore")
if (researcherRuntime) {
  assertPermissionFullyDenied(researcherRuntime, "edit", "RESEARCHER_HOST_EDIT_NOT_DENIED")
  if (permissionActionForWildcard(researcherRuntime,"grep")!=="deny" || tool(researcherRuntime,"grep")===true) {
    fail("RESEARCHER_NATIVE_GREP_EXPOSED")
  }
  if (tool(researcherRuntime,"bash")!==false && permissionActionForWildcard(researcherRuntime,"bash")!=="deny") {
    fail("RESEARCHER_HOST_BASH_EXPOSED_RUNTIME")
  }
  for (const t of ["sandbox_bash","sandbox_edit","sandbox_write","sandbox_apply_patch","sandbox_apply","sandbox_copy_in","sandbox_copy_out","sandbox_discard","sandbox_finish"]) {
    if (tool(researcherRuntime,t)!==false) fail(`RESEARCHER_RUNTIME_MUTATION_EXPOSED: ${t}`)
  }
  for (const t of ["aft_inspect","aft_outline","aft_zoom","sandbox_read","sandbox_list","sandbox_grep","sandbox_diff","ctx_search","ctx_expand"]) {
    if (tool(researcherRuntime,t)!==true) fail(`RESEARCHER_READ_OR_MEMORY_TOOL_MISSING: ${t}`)
  }
  if (tool(researcherRuntime,"ctx_memory")!==false) fail("RESEARCHER_MEMORY_TOOL_EXPOSED: ctx_memory")
  const hostRegisterResearchPermission=permissionActionForWildcard(researcherRuntime,"host_register_project")
  if (hostRegisterResearchPermission!=="deny") {
    fail(`RESEARCHER_HOST_REGISTER_PROJECT_RUNTIME_NOT_DENY: ${show(hostRegisterResearchPermission)}`)
  }
  const hostRegisterResearchTool=tool(researcherRuntime,"host_register_project")
  if (hostRegisterResearchTool===true) {
    fail("RESEARCHER_HOST_REGISTER_PROJECT_REGISTERED_AND_EXPOSED")
  } else if (hostRegisterResearchTool===undefined) {
    console.log("   info: host_register_project not registered in neutral researcher debug context; resolved permission=deny")
  }
}

// MCP registration/egress is environment-sensitive. Deterministically verify
// the desired MCP configuration and permission surface here; secure startup
// validation separately proves real Context7 network reachability.
const plugins=Array.isArray(deployed.plugin)?deployed.plugin:[]
const magicPlugins=plugins.filter((ref)=>typeof ref==="string" && ref.includes("opencode-magic-context"))
if (magicPlugins.length!==1) fail(`MAGIC_CONTEXT_PLUGIN_INVALID: expected exactly one opencode-magic-context plugin, found ${magicPlugins.length}`)

const mcp=deployed.mcp && typeof deployed.mcp==="object" ? deployed.mcp : {}
if (mcp.engram?.enabled===true) fail("ENGRAM_UNEXPECTEDLY_ENABLED: normal workflow must not probe Engram")
if (!mcp.context7 || mcp.context7.enabled!==true || mcp.context7.type!=="remote" ||
    typeof mcp.context7.url!=="string" || !mcp.context7.url.startsWith("https://mcp.context7.com/")) {
  fail("CONTEXT7_CONFIG_INVALID: expected enabled remote https://mcp.context7.com/ endpoint")
}
if (!mcp.codegraph || mcp.codegraph.enabled!==true || mcp.codegraph.type!=="local") {
  fail("CODEGRAPH_CONFIG_INVALID: expected enabled local CodeGraph MCP")
}
const github=mcp.github_ro
const reviewedGitHubToolsets="repos,pull_requests,issues"
if (!github || github.enabled!==true || github.type!=="remote" ||
    github.url!=="https://api.githubcopilot.com/mcp/readonly" || github.oauth!==false ||
    github.headers?.Authorization!=="Bearer {env:GITHUB_REVIEW_TOKEN}" ||
    github.headers?.["X-MCP-Readonly"]!=="true" ||
    github.headers?.["X-MCP-Toolsets"]!==reviewedGitHubToolsets ||
    Object.keys(github.headers??{}).some((key)=>!["Authorization","X-MCP-Readonly","X-MCP-Toolsets"].includes(key))) {
  fail("GITHUB_RO_CONFIG_INVALID: expected public-repo PAT placeholder and GitHub server-enforced read-only toolsets")
}
if (Object.keys(mcp).some((name)=>name!=="github_ro" && /^github([_-]|$)/i.test(name))) {
  fail("GITHUB_RO_DUPLICATE_MCP: unreviewed GitHub connection could bypass read-only mode")
}
if (deployed.tools?.["github_ro_*"]!==false) fail("GITHUB_RO_GLOBAL_TOOLS_NOT_DISABLED")
const githubReaders=new Set(["gentle-orchestrator","explore"])
for (const [name,agent] of Object.entries(deployedAgents)) {
  const enabled=agent?.tools?.["github_ro_*"]===true
  if (enabled!==githubReaders.has(name)) fail(`GITHUB_RO_AGENT_TOOLS_SCOPE_MISMATCH: ${name}`)
  if (enabled && agent.permission?.["github_ro_*"]!=="allow") fail(`GITHUB_RO_AGENT_PERMISSION_MISSING: ${name}`)
  if (!enabled && agent.permission?.["github_ro_*"]==="allow") fail(`GITHUB_RO_AGENT_PERMISSION_BYPASS: ${name}`)
}
for (const [name,overlay] of Object.entries(systematic.agents??{})) {
  if (overlay?.tools!==undefined || overlay?.permission?.["github_ro_*"]==="allow") {
    fail(`GITHUB_RO_SYSTEMATIC_AGENT_SCOPE_BYPASS: ${name}`)
  }
}
for (const [name,overlay] of Object.entries(systematic.categories??{})) {
  if (overlay?.tools?.["github_ro_*"]===true || overlay?.permission?.["github_ro_*"]==="allow") {
    fail(`GITHUB_RO_SYSTEMATIC_CATEGORY_SCOPE_BYPASS: ${name}`)
  }
}
const githubReaderNames=["gentle-orchestrator","explore"]
const githubBlockedNames=["general","repo-research-analyst","review-risk","correctness-reviewer"]
const githubCredentialInProbe=Boolean(process.env.GITHUB_REVIEW_TOKEN)
for (const name of [...githubReaderNames,...githubBlockedNames]) {
  const dbg=readDebug(name)
  if (!dbg) continue
  const githubTools=Object.entries(dbg.tools??{}).filter(([id])=>id.startsWith("github_ro_"))
  if (githubReaderNames.includes(name)) {
    // A one-shot opencode debug agent child does not establish the remote MCP
    // connection, so the GitHub tool is normally absent in this neutral probe;
    // absence is not a failure, but present-and-disabled is. The secure-service
    // /mcp probe below owns the authoritative active-connection evidence.
    const readerGithubTool=githubTools.find(([id])=>id==="github_ro_get_file_contents")
    if (readerGithubTool && readerGithubTool[1]===false) {
      fail(`GITHUB_RO_RESEARCH_TOOL_DISABLED: ${name}.github_ro_get_file_contents`)
    }
    for (const [id,enabled] of githubTools) {
      if (enabled===true && /^github_ro_(?:create|add|update|delete|remove|merge|push|fork|set|mark|lock|unlock|request|submit|dismiss|assign|unassign|cancel|rerun|trigger|enable|disable|replace|upsert|edit|close|reopen)(?:_|$)/.test(id)) {
        fail(`GITHUB_RO_MUTATION_TOOL_EXPOSED: ${name}.${id}`)
      }
    }
    if (permissionActionForWildcard(dbg,"github_ro_get_file_contents")!=="allow") {
      fail(`GITHUB_RO_RESEARCH_PERMISSION_MISSING: ${name}`)
    }
  } else if (githubTools.some(([,enabled])=>enabled===true)) {
    fail(`GITHUB_RO_UNAUTHORIZED_AGENT_TOOL_EXPOSED: ${name}`)
  }
}
if (!githubCredentialInProbe) {
  console.log("   info: isolated CLI probe has no GitHub credential; secure-service /mcp and /config probes own active GitHub verification")
} else {
  console.log("   info: neutral CLI debug probe does not materialize remote MCP tools; secure-service /mcp and /config probes own active GitHub verification")
}
for (const t of ["context7_query-docs","context7_resolve-library-id","codegraph_codegraph_explore"]) {
  if (gp[t]!=="allow") fail(`CUSTOM_MCP_PERMISSION_NOT_ALLOW: permission.${t}=${show(gp[t])}`)
}

if (failures) process.exit(1)
console.log(`   ok: all ${inventory.filter((a)=>!expectedFor(systematic,a).disable).length} enabled Systematic agents are registered by the plugin`)
console.log(`   ok: ${controlNames.length} Systematic runtime model/tool controls passed`)
console.log("   ok: GGA primaries, live plugin fallback policy, and sandbox capability boundaries passed")
EOF_RUNTIME_AGENT

