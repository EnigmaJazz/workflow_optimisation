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
//
// V2 differences that shape this adapter (all observed on 2.2.0):
//  - the editor inside ctx.agent.transform holds only built-in agents; agents defined in config are
//    layered on afterwards, so the full list comes from ctx.agent.list() ({ location, data });
//  - editor.update(id, fn) on an unknown id creates the agent, and ctx.agent.reload() re-runs the
//    transform;
//  - a plugin cannot amend a config-defined agent's permissions, so the orchestrator's right to
//    dispatch the aliases is a static rule in config: { action: "subagent", resource: "*-astra",
//    effect: "allow" } (queue Q43), not something this plugin adds.
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
  update: (id: string, update: (agent: AgentV2) => void) => void
}

type AgentDomainV2 = {
  transform: (callback: (editor: AgentEditorV2) => void) => Promise<{ dispose: () => Promise<void> | void }>
  list: () => Promise<{ data: readonly AgentV2[] }>
  reload: () => Promise<void>
}

type EventDomainV2 = {
  subscribe: () => AsyncIterable<{ type: string }>
}

// Pure: the aliases to create for a fully resolved agent list, plus problems worth reporting.
function planAliasesV2(agents: readonly AgentV2[]): { aliases: AgentV2[]; problems: string[] } {
  if (!agents.some((agent) => agent.id === "gentle-orchestrator")) {
    return { aliases: [], problems: ["astra-sol-upgrade: gentle-orchestrator is missing"] }
  }
  const byId = new Map(agents.map((agent) => [agent.id, agent]))
  const [astraProvider, ...astraModelParts] = ASTRA_MODEL.split("/")
  const aliases: AgentV2[] = []
  const problems: string[] = []

  for (const source of agents) {
    if (
      source.id.endsWith(ASTRA_SUFFIX) ||
      source.mode === "primary" ||
      normalizeModel(source.model) !== SOL_MODEL ||
      isImplementationRoute(source.id) ||
      isReviewActor(source.id)
    ) {
      continue
    }
    const aliasId = `${source.id}${ASTRA_SUFFIX}`
    const existing = byId.get(aliasId)
    if (existing) {
      // Ours from an earlier pass (already on the Astra model) is fine; anything else is not ours to replace.
      if (normalizeModel(existing.model) !== ASTRA_MODEL) {
        problems.push(`astra-sol-upgrade: refusing to overwrite agent ${aliasId}`)
      }
      continue
    }
    const copy = JSON.parse(JSON.stringify(source)) as AgentV2
    aliases.push(
      Object.assign(copy, {
        id: aliasId,
        name: `${source.name ?? source.id} (Astra)`,
        description: `${source.description ?? source.id} — selectable Astra upgrade`,
        hidden: true,
        model: { providerID: astraProvider, id: astraModelParts.join("/"), variant: ASTRA_VARIANT },
      }),
    )
  }
  return { aliases, problems }
}

async function setupV2(ctx: { agent: AgentDomainV2; event: EventDomainV2 }) {
  let pending: AgentV2[] = []
  let stopped = false
  const reported = new Set<string>()

  const registration = await ctx.agent.transform((editor) => {
    for (const alias of pending) {
      editor.update(alias.id, (target) => {
        Object.assign(target, JSON.parse(JSON.stringify(alias)))
      })
    }
  })

  // The full agent list only exists after config is layered on, so wait for the host's
  // agent.updated event, plan from the API list, then reload once. The reload raises the event
  // again; by then the aliases exist, the plan is empty and the loop settles.
  const iterator = ctx.event.subscribe()[Symbol.asyncIterator]()
  const loop = (async () => {
    try {
      for (let step = await iterator.next(); !step.done && !stopped; step = await iterator.next()) {
        if (step.value.type !== "agent.updated") continue
        const listed = await ctx.agent.list()
        const { aliases, problems } = planAliasesV2(listed.data)
        for (const problem of problems) {
          if (reported.has(problem)) continue
          reported.add(problem)
          console.error(problem)
        }
        if (aliases.length === 0) continue
        // Each pass replaces the plan. That is safe because aliases created earlier already exist in the
        // host: a later plan only contains aliases that are still missing, and a later transform pass
        // re-applies just those.
        pending = aliases
        await ctx.agent.reload()
      }
    } catch (error) {
      console.error("astra-sol-upgrade: alias refresh failed:", error)
    }
  })()

  return async () => {
    stopped = true
    await iterator.return?.()
    await registration.dispose()
    await loop
  }
}

// Dual-mode default export (the shape proven on V2 2.2.0 by the B1 probe). Do not add named
// function exports: OpenCode V1 would treat each one as a second plugin.
export default {
  id: "astra-sol-upgrade",
  setup: setupV2,
  server: serverV1,
}
