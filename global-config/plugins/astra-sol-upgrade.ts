/**
 * astra-sol-upgrade
 *
 * Creates hidden, per-dispatch Astra aliases for every non-implementation
 * subagent whose fully resolved OpenCode model is GPT-6 Sol. Because this
 * local plugin loads after configured npm plugins, aliases inherit the live
 * Gentle AI/Systematic prompt, tools, permissions, and mode rather than copying
 * plugin-owned agent definitions.
 */

const SOL_MODEL = "openai/gpt-6.1-sol"
const ASTRA_MODEL = "openai/gpt-6-astra"
const ASTRA_VARIANT = "xhigh"
const ASTRA_SUFFIX = "-astra"

type AgentConfig = Record<string, unknown> & {
  description?: string
  hidden?: boolean
  mode?: string
  model?: unknown
  permission?: Record<string, unknown>
  variant?: string
}

function normalizeModel(value: unknown): string | undefined {
  if (typeof value === "string") return value
  if (!value || typeof value !== "object" || Array.isArray(value)) return undefined

  const model = value as Record<string, unknown>
  const providerID = model.providerID ?? model.providerId
  // V1 spells it modelID; the V2 agent model is { providerID, id, variant? }.
  const modelID = model.modelID ?? model.modelId ?? model.id
  return typeof providerID === "string" && typeof modelID === "string"
    ? `${providerID}/${modelID}`
    : undefined
}

function isImplementationRoute(name: string): boolean {
  return (
    name === "general" ||
    name === "jd-fix-agent" ||
    name === "design-iterator" ||
    name === "bug-reproduction-validator" ||
    name === "pr-comment-resolver" ||
    name === "systematic-implementer" ||
    /(^|-)apply($|-)/.test(name) ||
    /(^|-)implement(er|ation)?($|-)/.test(name)
  )
}

// Native review actors are read-only relay lanes; an Astra upgrade of one is never wanted.
function isReviewActor(name: string): boolean {
  return /^(asi-)?review-(risk|resilience|readability|reliability|refuter|validator)$/.test(name)
}

function taskPermission(agent: AgentConfig): Record<string, unknown> {
  const permission = agent.permission
  const task = permission?.task
  if (!task || typeof task !== "object" || Array.isArray(task)) {
    throw new Error(
      "astra-sol-upgrade: gentle-orchestrator.permission.task must be an object",
    )
  }
  return task as Record<string, unknown>
}

// The V1 config hook: mutates the plain agent record (agent.* and permission.task).
async function serverV1() {
  return {
    config: async (config: { agent?: unknown }) => {
      const agents = config.agent as Record<string, AgentConfig> | undefined
      if (!agents) return
      addAliasesV1(agents)
    },
  }
}

function addAliasesV1(agents: Record<string, AgentConfig>): void {
  const orchestrator = agents["gentle-orchestrator"]
  if (!orchestrator) {
    throw new Error("astra-sol-upgrade: gentle-orchestrator is missing")
  }
  const orchestratorTasks = taskPermission(orchestrator)

  const solAgents = Object.entries(agents).filter(
    ([name, agent]) =>
      !name.endsWith(ASTRA_SUFFIX) &&
      agent.mode !== "primary" &&
      normalizeModel(agent.model) === SOL_MODEL &&
      !isImplementationRoute(name) &&
      !isReviewActor(name),
  )

  for (const [name, agent] of solAgents) {
    const alias = `${name}${ASTRA_SUFFIX}`
    if (Object.prototype.hasOwnProperty.call(agents, alias)) {
      throw new Error(`astra-sol-upgrade: refusing to overwrite agent ${alias}`)
    }

    agents[alias] = {
      ...agent,
      description: `${agent.description ?? name} — selectable Astra upgrade`,
      hidden: true,
      model: ASTRA_MODEL,
      variant: ASTRA_VARIANT,
    }
    orchestratorTasks[alias] = "allow"
  }
}

// V2 agent shape (B1 probe, OpenCode 2.2.0): { id, name, model?: { providerID, id, variant? },
// mode, hidden, description?, permissions: [{ action, resource, effect }] } with ordered rules.
type AgentV2 = {
  id: string
  name?: string
  mode?: string
  hidden?: boolean
  description?: string
  model?: unknown
  permissions: Array<{ action: string; resource: string; effect: string }>
  [key: string]: unknown
}

type AgentEditorV2 = {
  list: () => readonly AgentV2[]
  update: (id: string, update: (agent: AgentV2) => void) => void
}

function addAliasesV2(editor: AgentEditorV2): void {
  const agents = editor.list()
  const orchestrator = agents.find((agent) => agent.id === "gentle-orchestrator")
  if (!orchestrator) {
    throw new Error("astra-sol-upgrade: gentle-orchestrator is missing")
  }
  const existing = new Set(agents.map((agent) => agent.id))
  const [astraProvider, ...astraModelParts] = ASTRA_MODEL.split("/")

  const solAgents = agents.filter(
    (agent) =>
      !agent.id.endsWith(ASTRA_SUFFIX) &&
      agent.mode !== "primary" &&
      normalizeModel(agent.model) === SOL_MODEL &&
      !isImplementationRoute(agent.id) &&
      !isReviewActor(agent.id),
  )

  for (const source of solAgents) {
    const alias = `${source.id}${ASTRA_SUFFIX}`
    if (existing.has(alias)) {
      throw new Error(`astra-sol-upgrade: refusing to overwrite agent ${alias}`)
    }
    const copy = JSON.parse(JSON.stringify(source)) as AgentV2
    editor.update(alias, (target) => {
      Object.assign(target, copy, {
        id: alias,
        name: `${source.name ?? source.id} (Astra)`,
        description: `${source.description ?? source.id} — selectable Astra upgrade`,
        hidden: true,
        model: { providerID: astraProvider, id: astraModelParts.join("/"), variant: ASTRA_VARIANT },
      })
    })
    // Rules are ordered and the last match wins, so the allow goes at the end.
    editor.update("gentle-orchestrator", (target) => {
      target.permissions.push({ action: "subagent", resource: alias, effect: "allow" })
    })
  }
}

async function setupV2(ctx: {
  agent: { transform: (callback: (editor: AgentEditorV2) => void) => Promise<{ dispose: () => Promise<void> | void }> }
}) {
  const registration = await ctx.agent.transform(addAliasesV2)
  return async () => {
    await registration.dispose()
  }
}

// Dual-mode default export (the shape proven on V2 2.2.0 by the B1 probe). Do not add named
// function exports: OpenCode V1 would treat each one as a second plugin.
export default {
  id: "astra-sol-upgrade",
  setup: setupV2,
  server: serverV1,
}
