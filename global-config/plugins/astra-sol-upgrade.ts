/**
 * astra-sol-upgrade
 *
 * Creates hidden, per-dispatch Astra aliases for every non-implementation
 * subagent whose fully resolved OpenCode model is GPT-6 Sol. Because this
 * local plugin loads after configured npm plugins, aliases inherit the live
 * Gentle AI/Systematic prompt, tools, permissions, and mode rather than copying
 * plugin-owned agent definitions.
 */

import type { Plugin } from "@opencode-ai/plugin"

const SOL_MODEL = "openai/gpt-6-sol"
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
  const modelID = model.modelID ?? model.modelId
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

export const AstraSolUpgradePlugin: Plugin = async () => ({
  config: async (config) => {
    const agents = config.agent as Record<string, AgentConfig> | undefined
    if (!agents) return

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
        !isImplementationRoute(name),
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
  },
})
