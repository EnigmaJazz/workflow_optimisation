cat > "$SYSTEMATIC_CHECKER" <<'EOF_NODE'
const fs = require("fs")
const path = require("path")

const nodeModules = process.env.SYSTEMATIC_NODE_MODULES
if (!nodeModules) {
  console.error("missing SYSTEMATIC_NODE_MODULES")
  process.exit(2)
}

let jsonc
try {
  jsonc = require(path.join(nodeModules, "jsonc-parser"))
} catch (error) {
  console.error(`cannot load jsonc-parser from ${nodeModules}: ${error.message}`)
  process.exit(2)
}

const [configPath, agentsRoot, resolvedConfigPath, openCodeConfigPath] = process.argv.slice(2)
const hasOwn = (obj, key) => Object.prototype.hasOwnProperty.call(obj ?? {}, key)

function parseJsonc(file) {
  const text = fs.readFileSync(file, "utf8")
  const errors = []
  const value = jsonc.parse(text, errors, {
    allowTrailingComma: true,
    disallowComments: false,
  })
  if (errors.length > 0) {
    const detail = errors
      .map((e) => `${jsonc.printParseErrorCode(e.error)}@${e.offset}`)
      .join(", ")
    throw new Error(`${file}: JSONC parse errors: ${detail}`)
  }
  return value
}

function isDiscoverableMarkdown(fileName) {
  // Mirror Systematic's own discovery contract: README.md is directory
  // documentation, never a dispatchable bundled agent.
  return fileName.endsWith(".md") && fileName.toLowerCase() !== "readme.md"
}

function declaredToolsFromAgentMarkdown(file) {
  let text
  try {
    text = fs.readFileSync(file, "utf8")
  } catch {
    return []
  }
  const fm = text.match(/^---\s*\n([\s\S]*?)\n---/)
  if (!fm) return []
  const match = fm[1].match(/^tools:\s*(.+)$/mi)
  if (!match) return []
  return match[1]
    .split(",")
    .map((value) => value.trim().toLowerCase())
    .filter(Boolean)
}

function walkMarkdown(root, current = root, out = [], depth = 0, maxDepth = 2) {
  if (!fs.existsSync(current) || depth > maxDepth) return out
  for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
    const full = path.join(current, entry.name)
    if (entry.isDirectory()) {
      walkMarkdown(root, full, out, depth + 1, maxDepth)
    } else if (entry.isFile() && isDiscoverableMarkdown(entry.name)) {
      const rel = path.relative(root, full)
      const parts = rel.split(path.sep)
      const name = path.basename(entry.name, ".md")
      const category = parts.length > 1 ? parts[0] : ""
      const declaredTools = declaredToolsFromAgentMarkdown(full)
      const declaresMutation = declaredTools.includes("edit") || declaredTools.includes("write")
      out.push({ name, category, rel, declaredTools, declaresMutation })
    }
  }
  return out
}

function exactOverlayFor(config, agent) {
  const overlays = config.agents && typeof config.agents === "object" ? config.agents : {}
  const candidates = []
  if (hasOwn(overlays, agent.name)) candidates.push([agent.name, overlays[agent.name]])
  const qualified = agent.category ? `${agent.category}/${agent.name}` : agent.name
  if (qualified !== agent.name && hasOwn(overlays, qualified)) {
    candidates.push([qualified, overlays[qualified]])
  }
  return candidates
}

function applyOverlay(state, overlay) {
  if (!overlay || typeof overlay !== "object" || Array.isArray(overlay)) return

  // Mirrors current Systematic overlay semantics: setting a model without a
  // variant clears any lower-precedence variant. model:null restores inheritance.
  if (hasOwn(overlay, "model")) {
    if (!hasOwn(overlay, "variant")) state.variant = undefined
    state.model = overlay.model === null ? undefined : overlay.model
  }
  if (hasOwn(overlay, "variant")) {
    state.variant = overlay.variant == null ? undefined : overlay.variant
  }
  if (hasOwn(overlay, "disable")) state.disable = overlay.disable === true
}

function applyOpenCodeOverlay(state, overlay) {
  // v3.16 precedence within one layer: harness-specific values override flat.
  applyOverlay(state, overlay)
  applyOverlay(state, overlay?.opencode)
}

function expectedFor(config, agent, exactOverlay) {
  const state = { model: undefined, variant: undefined, disable: false }
  const categories = config.categories && typeof config.categories === "object" ? config.categories : {}
  if (agent.category && hasOwn(categories, agent.category)) {
    applyOpenCodeOverlay(state, categories[agent.category])
  }
  applyOpenCodeOverlay(state, exactOverlay)

  // Systematic 3.16 named profiles are sparse overlays on the base config.
  // Apply a reviewed active profile after the base category/agent layers.
  const activeProfile = typeof config.profile === "string" ? config.profiles?.[config.profile] : undefined
  if (activeProfile && typeof activeProfile === "object" && !Array.isArray(activeProfile)) {
    if (agent.category && hasOwn(activeProfile.categories, agent.category)) {
      applyOpenCodeOverlay(state, activeProfile.categories[agent.category])
    }
    const profileMatches = exactOverlayFor(activeProfile, agent)
    if (profileMatches.length === 1) applyOpenCodeOverlay(state, profileMatches[0][1])
  }

  const disabled = Array.isArray(config.disabled_agents) ? config.disabled_agents : []
  if (disabled.includes(agent.name) || (agent.category && disabled.includes(`${agent.category}/${agent.name}`))) {
    state.disable = true
  }
  return state
}

function normalizeResolvedModel(value) {
  if (typeof value === "string") return value
  if (value && typeof value === "object") {
    const providerID = value.providerID ?? value.providerId
    const modelID = value.modelID ?? value.modelId
    if (typeof providerID === "string" && typeof modelID === "string") {
      return `${providerID}/${modelID}`
    }
  }
  return undefined
}

function show(value) {
  return value === undefined ? "<inherit/none>" : JSON.stringify(value)
}

let config
try {
  config = parseJsonc(configPath)
} catch (error) {
  console.error(`   !! ${error.message}`)
  process.exit(1)
}

const inventory = walkMarkdown(agentsRoot).sort((a, b) => a.name.localeCompare(b.name))
if (inventory.length === 0) {
  console.error(`   !! no bundled Systematic agents found under ${agentsRoot}`)
  process.exit(1)
}

const inventoryByName = new Map()
for (const agent of inventory) {
  if (inventoryByName.has(agent.name)) {
    console.error(`   !! duplicate bundled agent stem: ${agent.name}`)
    process.exit(1)
  }
  inventoryByName.set(agent.name, agent)
}

const categoriesInBundle = new Set(inventory.map((a) => a.category).filter(Boolean))
const configuredCategories = config.categories && typeof config.categories === "object"
  ? Object.keys(config.categories)
  : []
const configuredAgents = config.agents && typeof config.agents === "object"
  ? Object.keys(config.agents)
  : []

let failed = false

for (const [name,overlay] of Object.entries(config.agents??{})) {
  if (overlay && typeof overlay==="object" && Object.hasOwn(overlay,"tools")) {
    console.error(`   !! SYSTEMATIC_UNSUPPORTED_AGENT_TOOLS: ${name}; Systematic rejects tools under agents`)
    failed=true
  }
}

for (const category of configuredCategories) {
  if (!categoriesInBundle.has(category)) {
    console.error(`   !! stale/unknown Systematic category in config: ${category}`)
    failed = true
  }
}

const consumedAgentKeys = new Set()
const expectations = []

for (const agent of inventory) {
  const matches = exactOverlayFor(config, agent)
  if (matches.length === 0) {
    console.error(`   !! bundled Systematic agent has no explicit agents.* overlay: ${agent.name} (${agent.category || "uncategorized"})`)
    failed = true
    continue
  }
  if (matches.length > 1) {
    console.error(`   !! duplicate overlays target ${agent.name}: ${matches.map(([key]) => key).join(", ")}`)
    failed = true
    continue
  }

  const [key, exact] = matches[0]
  consumedAgentKeys.add(key)
  expectations.push({ agent, expected: expectedFor(config, agent, exact) })
}

for (const key of configuredAgents) {
  if (!consumedAgentKeys.has(key)) {
    console.error(`   !! stale/unknown Systematic agent overlay in config: ${key}`)
    failed = true
  }
}

const profiles = config.profiles && typeof config.profiles === "object" && !Array.isArray(config.profiles)
  ? config.profiles
  : {}
if (hasOwn(profiles, "astra-critical")) {
  console.error("   !! retired global Systematic profile remains: astra-critical; use per-session Sol-role Astra aliases")
  failed = true
}
if (hasOwn(config, "profile") && (typeof config.profile !== "string" || !hasOwn(profiles, config.profile))) {
  console.error(`   !! active Systematic profile is missing or unknown: ${show(config.profile)}`)
  failed = true
}
for (const [profileName, profile] of Object.entries(profiles)) {
  if (!profile || typeof profile !== "object" || Array.isArray(profile)) {
    console.error(`   !! Systematic profile ${profileName} must be an object`)
    failed = true
    continue
  }
  const profileAgents = profile.agents && typeof profile.agents === "object" && !Array.isArray(profile.agents)
    ? profile.agents
    : {}
  for (const key of Object.keys(profileAgents)) {
    const plain = key.includes("/") ? key.slice(key.lastIndexOf("/") + 1) : key
    if (!inventoryByName.has(plain)) {
      console.error(`   !! stale/unknown Systematic agent in profile ${profileName}: ${key}`)
      failed = true
    }
    if (profileAgents[key]?.permission !== undefined) {
      console.error(`   !! Systematic profile ${profileName}.${key} must not override security permissions`)
      failed = true
    }
  }
  if (profile.categories && Object.values(profile.categories).some((value) => value?.permission !== undefined)) {
    console.error(`   !! Systematic profile ${profileName} must not override category security permissions`)
    failed = true
  }
}

const systematicText = JSON.stringify(config)
for (const retiredModel of [
  "muse-spark-1.2-contributor",
  "deepseek-v4-pro",
  "deepseek-v4-flash-vision-exp",
]) {
  if (systematicText.includes(retiredModel)) {
    console.error(`   !! retired Muse/DeepSeek model remains in systematic.jsonc: ${retiredModel}`)
    failed = true
  }
}

// User-owned Systematic security policy belongs in systematic.jsonc, not in
// same-name opencode.json agent stubs (which suppress bundled agent emission).
// Every category fails closed for mutation; exact mutator overlays may then
// opt into worker-local sandbox capabilities.
const categoryMutationDenies = [
  "edit", "write", "sandbox_bash", "sandbox_edit", "sandbox_write",
  "sandbox_apply_patch", "sandbox_apply", "sandbox_copy_in",
  "sandbox_copy_out", "sandbox_discard", "sandbox_finish",
]
for (const category of categoriesInBundle) {
  const overlay = config.categories?.[category]
  const permission = overlay && typeof overlay === "object" ? overlay.permission : undefined
  if (!permission || typeof permission !== "object" || Array.isArray(permission)) {
    console.error(`   !! Systematic category ${category} lacks a permission overlay`)
    failed = true
    continue
  }
  for (const tool of categoryMutationDenies) {
    if (permission[tool] !== "deny") {
      console.error(`   !! Systematic category ${category}.permission.${tool} must be deny`)
      failed = true
    }
  }
}

const systematicMemoryPolicy = {
  workflow: "allow",
  research: "deny",
  design: "deny",
  review: "deny",
  "document-review": "deny",
}
for (const category of categoriesInBundle) {
  const expected = systematicMemoryPolicy[category]
  if (!expected) {
    console.error(`   !! Systematic memory policy has no classification for category ${category}`)
    failed = true
    continue
  }
  const permission = config.categories?.[category]?.permission
  if (!permission || permission.ctx_memory !== expected) {
    console.error(`   !! Systematic category ${category}.permission.ctx_memory must be ${expected}`)
    failed = true
  }
}

const systematicMutators = inventory.filter((agent) => agent.declaresMutation)
const writerAllows = [
  "sandbox_read", "sandbox_list", "sandbox_grep", "sandbox_diff",
  "sandbox_bash", "sandbox_edit", "sandbox_write", "sandbox_apply_patch",
]
const writerBoundaryAsk = [
  "sandbox_apply", "sandbox_copy_in", "sandbox_copy_out",
  "sandbox_discard", "sandbox_finish",
]
for (const agent of systematicMutators) {
  const matches = exactOverlayFor(config, agent)
  if (matches.length !== 1) continue
  const permission = matches[0][1]?.permission
  if (!permission || typeof permission !== "object" || Array.isArray(permission)) {
    console.error(`   !! Systematic mutator ${agent.name} lacks an exact permission overlay`)
    failed = true
    continue
  }
  for (const tool of ["edit", "write", "bash"]) {
    if (permission[tool] !== "deny") {
      console.error(`   !! Systematic mutator ${agent.name}.permission.${tool} must be deny`)
      failed = true
    }
  }
  for (const tool of writerAllows) {
    if (permission[tool] !== "allow") {
      console.error(`   !! Systematic mutator ${agent.name}.permission.${tool} must be allow`)
      failed = true
    }
  }
  for (const tool of writerBoundaryAsk) {
    if (permission[tool] !== "ask") {
      console.error(`   !! Systematic mutator ${agent.name}.permission.${tool} must be ask`)
      failed = true
    }
  }
}

for (const item of expectations) {
  if (!item.expected.disable && typeof item.expected.model !== "string") {
    console.error(`   !! Systematic agent ${item.agent.name} has no effective explicit model assignment`)
    failed = true
  }
}

if (failed) process.exit(1)

console.log(`   ok: ${inventory.length}/${inventory.length} bundled agents have explicit model overlays; no stale agent/category entries`)
console.log(`   ok: ${systematicMutators.length} bundled Edit/Write personas are sandbox-routed by systematic.jsonc permission overlays`)
process.exit(0)


EOF_NODE

