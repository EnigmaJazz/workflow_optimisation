// OpenCode V2 agent-inventory shim (queue Q44).
// V2 has no `agent list` / `debug agent <name>`; `debug agents` prints one JSON array. Read it from stdin and
// write the V1-shaped files the runtime agent checker consumes:
//   argv[2]  listing file, one `name (mode)` line per agent
//   argv[3]  directory with <name>.json (V1 field names), <name>.status (0) and <name>.stderr (empty)
// Plugin chatter before the array is tolerated. Anything that is not an array of agents exits non-zero
// without writing, so the verifier fails closed.
const fs = require("fs")
const path = require("path")

const [listFile, debugDir] = process.argv.slice(2)
if (!listFile || !debugDir) {
  console.error("usage: v2-agents-shim.cjs <listing-file> <debug-dir> < debug-agents-output")
  process.exit(2)
}

function parseAgents(text) {
  const clean = text.replace(/\x1B\[[0-?]*[ -\/]*[@-~]/g, "")
  // The array starts at a line beginning with `[` followed by an object.
  const starts = []
  const re = /(?:^|\n)[\t ]*\[\s*(?=[{\]])/g
  let m
  while ((m = re.exec(clean)) !== null) starts.push(clean.indexOf("[", m.index))
  for (const start of starts) {
    try {
      const value = JSON.parse(clean.slice(start).trim())
      if (Array.isArray(value) && value.every((a) => a && typeof a === "object" && typeof a.id === "string")) return value
    } catch {}
  }
  return undefined
}

// V2 renames the shell permission; V1 (and the checker) call it bash.
const permissionName = (action) => (action === "shell" ? "bash" : action)

// V2 exposes no per-agent tools map, but its permission rules say which tools an agent may use. Derive V1's `tools` shape:
// a tool the rules name with a "*" resource is true when its LAST such rule allows or asks (the tool is usable, possibly after
// a prompt) and false when it denies. A bare "*" action and tools with only narrower resources (read of *.env) are not
// turned into entries: an unnamed tool stays absent, as in V1, so "not configured" is never read as "enabled".
function toolsFromRules(rules) {
  const tools = {}
  for (const r of rules || []) {
    if (!r || typeof r.action !== "string" || r.action === "*" || r.resource !== "*") continue
    if (r.effect !== "allow" && r.effect !== "ask" && r.effect !== "deny") continue
    tools[permissionName(r.action)] = r.effect !== "deny"
  }
  return tools
}

function toV1(agent) {
  const body = (agent.request && agent.request.body) || {}
  const { temperature, topP, ...options } = body
  const out = {
    name: agent.id,
    mode: agent.mode,
    permission: (agent.permissions || []).map((r) => ({
      permission: permissionName(r.action),
      pattern: r.resource,
      action: r.effect,
    })),
    options,
    tools: toolsFromRules(agent.permissions),
  }
  if (agent.description !== undefined) out.description = agent.description
  if (agent.hidden !== undefined) out.hidden = agent.hidden
  if (agent.model) {
    out.model = { providerID: agent.model.providerID, modelID: agent.model.id }
    // The checker reads the variant at the agent's top level (V1's debug shape), not inside model.
    if (agent.model.variant !== undefined) out.variant = agent.model.variant
  }
  if (agent.system !== undefined) out.prompt = agent.system
  if (agent.steps !== undefined) out.steps = agent.steps
  if (temperature !== undefined) out.temperature = temperature
  if (topP !== undefined) out.topP = topP
  return out
}

const agents = parseAgents(fs.readFileSync(0, "utf8"))
if (!agents) {
  console.error("v2-agents-shim: no agent array found in `debug agents` output")
  process.exit(1)
}

// The id becomes a filename, so validate every id (and uniqueness) before writing anything.
const SAFE_ID = /^[A-Za-z0-9][A-Za-z0-9._-]*$/
const seen = new Set()
for (const agent of agents) {
  if (!SAFE_ID.test(agent.id)) {
    console.error(`v2-agents-shim: unsafe agent id ${JSON.stringify(agent.id)}`)
    process.exit(1)
  }
  if (seen.has(agent.id)) {
    console.error(`v2-agents-shim: duplicate agent id ${JSON.stringify(agent.id)}`)
    process.exit(1)
  }
  seen.add(agent.id)
}

try {
  fs.mkdirSync(debugDir, { recursive: true })
  const lines = []
  for (const agent of agents) {
    const v1 = toV1(agent)
    fs.writeFileSync(path.join(debugDir, `${v1.name}.json`), JSON.stringify(v1, null, 2) + "\n")
    fs.writeFileSync(path.join(debugDir, `${v1.name}.status`), "0\n")
    fs.writeFileSync(path.join(debugDir, `${v1.name}.stderr`), "")
    lines.push(`${v1.name} (${v1.mode})`)
  }
  fs.mkdirSync(path.dirname(listFile), { recursive: true })
  // The listing is written last: its absence means the run did not complete.
  fs.writeFileSync(listFile, lines.join("\n") + "\n")
} catch (err) {
  console.error(`v2-agents-shim: cannot write the agent files: ${err.message}`)
  process.exit(1)
}
