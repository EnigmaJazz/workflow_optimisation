/**
 * systematic-routing-guard
 *
 * Runtime guard for the user's Gentle AI + Systematic OpenCode workflow.
 *
 * Why this exists:
 *   - Systematic v3 registers bundled OpenCode agents under bare names such as
 *     `systematic-implementer`, `correctness-reviewer`, etc.
 *   - `systematic.jsonc` owns their per-agent/per-category model overlays.
 *   - Gentle's generic delegated-direct routing can otherwise choose OpenCode's
 *     native `general` / `explore` workers while a Systematic workflow is
 *     active, silently bypassing those specialist model overlays.
 *
 * This plugin is deliberately a guardrail, not a second router:
 *   1. It strips a legacy unsupported `model` argument from task() calls.
 *   2. It normalizes an ACTUAL task subagent_type from
 *      `systematic:<category>:<name>` to the bare OpenCode agent name.
 *      Qualified Systematic IDs remain valid/canonical in ordinary prose and
 *      skill content; this plugin does not rewrite or flag those references.
 *   3. It tracks guarded Systematic workflows per OpenCode session/turn.
 *   4. It blocks a generic task() dispatch only when that dispatch appears to
 *      replace specialist implementation/review/research work prescribed by
 *      the active Systematic workflow.
 *   5. Bounded utility workers (tests/build/lint/typecheck/git-state checks)
 *      remain allowed.
 *
 * The plugin never chooses a specialist on the model's behalf. When a generic
 * dispatch is blocked, the caller must re-dispatch using the specialist named
 * by the active Systematic skill. This avoids silently rewriting `general` to
 * the wrong specialist when a workflow has several possible personas.
 *
 * Optional troubleshooting mode:
 *   SYSTEMATIC_ROUTING_GUARD_MODE=warn   # log violations but allow them
 *   SYSTEMATIC_ROUTING_GUARD_MODE=off    # disable the guard entirely
 * Default: block
 *
 * Persistence: place this file in ~/.config/opencode/plugins/. OpenCode loads
 * local plugins from that directory automatically.
 */

import { appendFile, mkdir } from "node:fs/promises"
import { existsSync } from "node:fs"
import { homedir } from "node:os"
import { join } from "node:path"
import type { Plugin } from "@opencode-ai/plugin"

type WorkKind = "implementation" | "review" | "research" | "utility" | "unknown"
type GuardMode = "block" | "warn" | "off"

interface WorkflowProfile {
  /** Kinds of work this workflow intentionally routes to Systematic specialists. */
  specialistKinds: ReadonlySet<Exclude<WorkKind, "utility" | "unknown">>
  /** Known stable targets used only as diagnostic hints / fallback evidence. */
  fallbackTargets: readonly string[]
  /** For these workflows, an unclassifiable `general` task is suspicious too. */
  strictGeneral?: boolean
}

interface ActiveWorkflow {
  skillName: string
  source: "systematic_skill" | "skill" | "command"
  specialistKinds: Set<Exclude<WorkKind, "utility" | "unknown">>
  targets: Set<string>
  activatedAt: number
}

/**
 * Only workflow skills whose semantics include specialist dispatch are guarded.
 * This prevents documentation/meta skills such as `using-systematic` from
 * accidentally disabling generic workers merely because they contain examples.
 */
const WORKFLOW_PROFILES = new Map<string, WorkflowProfile>([
  [
    "ce:work",
    {
      specialistKinds: new Set(["implementation"]),
      fallbackTargets: ["systematic-implementer"],
      strictGeneral: true,
    },
  ],
  [
    "ce:review",
    {
      specialistKinds: new Set(["review", "research"]),
      fallbackTargets: [
        "correctness-reviewer",
        "testing-reviewer",
        "maintainability-reviewer",
        "project-standards-reviewer",
        "agent-native-reviewer",
        "learnings-researcher",
      ],
      strictGeneral: true,
    },
  ],
  [
    "document-review",
    {
      specialistKinds: new Set(["review"]),
      fallbackTargets: [
        "coherence-reviewer",
        "feasibility-reviewer",
        "scope-guardian-reviewer",
        "design-lens-reviewer",
        "product-lens-reviewer",
        "security-lens-reviewer",
        "adversarial-document-reviewer",
      ],
      strictGeneral: true,
    },
  ],
  [
    "ce:plan",
    {
      specialistKinds: new Set(["research", "review"]),
      fallbackTargets: [
        "repo-research-analyst",
        "git-history-analyzer",
        "best-practices-researcher",
        "framework-docs-researcher",
      ],
    },
  ],
  [
    "ce:compound",
    {
      specialistKinds: new Set(["research"]),
      fallbackTargets: ["repo-research-analyst", "learnings-researcher"],
    },
  ],
  [
    "reproduce-bug",
    {
      specialistKinds: new Set(["research", "review"]),
      fallbackTargets: ["bug-reproduction-validator"],
      strictGeneral: true,
    },
  ],
  [
    "deepen-plan",
    {
      specialistKinds: new Set(["research", "review"]),
      fallbackTargets: [
        "architecture-strategist",
        "repo-research-analyst",
        "best-practices-researcher",
      ],
    },
  ],
])

/** Actual OpenCode dispatch: qualified Systematic persona -> bare agent stem. */
const QUALIFIED_SUBAGENT = /^systematic:[a-z0-9-]+:([a-z0-9-]+)$/i

/** Strong dispatch syntax we can safely mine from a loaded workflow body. */
const EXPLICIT_SUBAGENT = /subagent_type\s*:\s*["'`]([a-z0-9-]+)["'`]/gi
const EXPLICIT_QUALIFIED_DISPATCH =
  /\b(?:dispatch|delegate|spawn|launch)\b[^\n]{0,180}`systematic:[a-z0-9-]+:([a-z0-9-]+)`/gi
const EXPLICIT_BARE_DISPATCH =
  /\b(?:dispatch|delegate|spawn|launch)\b[^\n]{0,180}`([a-z0-9-]+)`\s+(?:subagent|agent|persona)\b/gi

const MUTATION_RE =
  /\b(?:implement|fix|patch|edit|modify|rewrite|refactor|create|add|remove|delete|migrate|change|update|write)\b/i
const REVIEW_RE =
  /\b(?:review|audit|critique|correctness|security|reliability|maintainability|performance|coverage|find(?:ing|ings)?|regression|validate\s+(?:the\s+)?(?:diff|change|implementation))\b/i
const RESEARCH_RE =
  /\b(?:research|investigate|explore|map|trace|analy[sz]e|understand|architecture|prior\s+art|history|find\s+patterns?|codebase\s+structure)\b/i
const UTILITY_RE =
  /(?:\b(?:run|execute|check)\b.{0,80}\b(?:tests?|test\s+suite|build|compile|lint|typecheck|type-check|formatter|format\s+check|install)\b|\bgit\s+(?:status|diff|log|show)\b)/i

const TARGET_KIND_PATTERNS: ReadonlyArray<[
  Exclude<WorkKind, "utility" | "unknown">,
  RegExp,
]> = [
  [
    "implementation",
    /(?:systematic-implementer|pr-comment-resolver|design-iterator|fix-agent|resolver)/i,
  ],
  [
    "review",
    /(?:reviewer|validator|verification|correctness|testing|reliability|security|performance|maintainability|coherence|feasibility|scope-guardian|architecture-strategist)/i,
  ],
  [
    "research",
    /(?:research|analyst|analyzer|history|learnings|issue-intelligence|pattern-recognition|spec-flow)/i,
  ],
]

const ACTIVE_TTL_MS = 30 * 60 * 1000

function guardMode(): GuardMode {
  const raw = (process.env.SYSTEMATIC_ROUTING_GUARD_MODE ?? "block").toLowerCase()
  if (raw === "off" || raw === "warn") return raw
  return "block"
}

const ROUTING_GATE_TOOLS = new Set([
  "task",
  "host_git_commit",
  "host_git_push",
  "host_gh_issue_create",
  "host_plan_append",
  "host_register_project",
])
const ROUTING_GATE_OFF_FILE = join(homedir(), ".config/opencode/routing-guard-off")
const ROUTING_GATE_LOG_FILE = join(homedir(), ".local/share/opencode/logs/routing-guard.log")

function isRoutingGateTool(tool: string): boolean {
  return (
    ROUTING_GATE_TOOLS.has(tool) ||
    tool.startsWith("host_review_") ||
    tool.startsWith("host_sdd_")
  )
}

function isRoutingGateDisabled(): boolean {
  try {
    return existsSync(ROUTING_GATE_OFF_FILE)
  } catch {
    return false
  }
}

async function logInactiveWorkflowWarning(tool: string, sessionID: string): Promise<void> {
  const message = `routing gate: ${tool} with no active workflow for this change; load the workflow-route skill (or the selected adapter skill) before dispatching`
  const line = `[systematic-routing-guard] ${message} (session: ${sessionID})`
  console.warn(line)

  try {
    await mkdir(join(homedir(), ".local/share/opencode/logs"), { recursive: true })
    await appendFile(ROUTING_GATE_LOG_FILE, `${line}\n`, "utf8")
  } catch {
    // Logging must never block or fail the tool call.
  }
}

function canonicalSkillName(raw: unknown): string | null {
  if (typeof raw !== "string") return null
  let name = raw.trim().replace(/^\/+/, "")
  if (!name) return null

  // systematic_skill commonly accepts names prefixed with `systematic:`.
  if (name.startsWith("systematic:")) name = name.slice("systematic:".length)

  const aliases: Record<string, string> = {
    "ce-work": "ce:work",
    "ce-review": "ce:review",
    "ce-plan": "ce:plan",
    "ce-brainstorm": "ce:brainstorm",
    "ce-compound": "ce:compound",
  }
  return aliases[name] ?? name
}

function extractTextParts(parts: unknown): string {
  if (!Array.isArray(parts)) return ""
  const text: string[] = []
  for (const part of parts) {
    if (!part || typeof part !== "object") continue
    const candidate = part as { type?: unknown; text?: unknown }
    if (candidate.type === "text" && typeof candidate.text === "string") {
      text.push(candidate.text)
    }
  }
  return text.join("\n")
}

function collectMatches(content: string, regex: RegExp, targets: Set<string>): void {
  regex.lastIndex = 0
  for (let match = regex.exec(content); match; match = regex.exec(content)) {
    if (match[1]) targets.add(match[1])
  }
}

/**
 * Extract only dispatch-shaped references. We intentionally do NOT scan every
 * `systematic:<category>:<name>` occurrence because qualified persona IDs are
 * valid canonical references in current Systematic prose/catalogs.
 */
function extractExplicitTargets(content: string): Set<string> {
  const targets = new Set<string>()
  collectMatches(content, EXPLICIT_SUBAGENT, targets)
  collectMatches(content, EXPLICIT_QUALIFIED_DISPATCH, targets)
  collectMatches(content, EXPLICIT_BARE_DISPATCH, targets)
  return targets
}

function kindsFromTargets(targets: Iterable<string>): Set<Exclude<WorkKind, "utility" | "unknown">> {
  const kinds = new Set<Exclude<WorkKind, "utility" | "unknown">>()
  for (const target of targets) {
    for (const [kind, pattern] of TARGET_KIND_PATTERNS) {
      if (pattern.test(target)) kinds.add(kind)
    }
  }
  return kinds
}

function classifyTask(args: Record<string, unknown>): WorkKind {
  const text = [args.description, args.prompt]
    .filter((value): value is string => typeof value === "string")
    .join("\n")

  // A utility task is allowed only when it does not also ask the worker to
  // mutate, review, or research. "Run tests and fix failures" is implementation.
  const mutates = MUTATION_RE.test(text)
  const reviews = REVIEW_RE.test(text)
  const researches = RESEARCH_RE.test(text)
  const utility = UTILITY_RE.test(text)

  if (mutates) return "implementation"
  if (reviews) return "review"
  if (researches) return "research"
  if (utility) return "utility"
  return "unknown"
}

function activateWorkflow(
  active: Map<string, ActiveWorkflow>,
  sessionID: string,
  rawSkillName: unknown,
  source: ActiveWorkflow["source"],
  content = "",
): void {
  const skillName = canonicalSkillName(rawSkillName)
  if (!skillName) return
  const profile = WORKFLOW_PROFILES.get(skillName)
  if (!profile) return

  const targets = new Set<string>(profile.fallbackTargets)
  for (const target of extractExplicitTargets(content)) targets.add(target)

  const specialistKinds = new Set(profile.specialistKinds)
  for (const kind of kindsFromTargets(targets)) specialistKinds.add(kind)

  active.set(sessionID, {
    skillName,
    source,
    specialistKinds,
    targets,
    activatedAt: Date.now(),
  })
}

function getActiveWorkflow(
  active: Map<string, ActiveWorkflow>,
  sessionID: string,
): ActiveWorkflow | null {
  const state = active.get(sessionID)
  if (!state) return null
  if (Date.now() - state.activatedAt > ACTIVE_TTL_MS) {
    active.delete(sessionID)
    return null
  }
  return state
}

function shouldBlockGeneric(
  subagentType: "general" | "explore",
  kind: WorkKind,
  state: ActiveWorkflow,
): boolean {
  if (kind === "utility") return false

  const profile = WORKFLOW_PROFILES.get(state.skillName)
  if (!profile) return false

  if (kind === "implementation" || kind === "review" || kind === "research") {
    return state.specialistKinds.has(kind)
  }

  // Unknown work is blocked only for `general` in workflows where a generic
  // worker is especially likely to be an accidental replacement. `explore`
  // remains available for genuinely generic bounded mapping unless the task
  // text itself classified as research/review above.
  return subagentType === "general" && profile.strictGeneral === true
}

function formatTargets(targets: Set<string>): string {
  const visible = [...targets].slice(0, 8)
  if (visible.length === 0) return ""
  const suffix = targets.size > visible.length ? ", …" : ""
  return ` Candidate specialists from the active workflow include: ${visible.join(", ")}${suffix}.`
}

function routingViolationMessage(
  subagentType: "general" | "explore",
  kind: WorkKind,
  state: ActiveWorkflow,
): string {
  return [
    `[systematic-routing-guard] blocked generic \`${subagentType}\` delegation while \`${state.skillName}\` is active.`,
    `The requested task looks like ${kind === "unknown" ? "non-utility" : kind} work and would bypass the Systematic specialist routing/model overlays.`,
    `Re-dispatch using the specialist explicitly prescribed by the active Systematic skill; do not guess a replacement specialist.`,
    `Generic workers remain allowed for bounded utility-only tasks such as running tests, builds, lint/typecheck, installs, or read-only git state checks.`,
    formatTargets(state.targets),
  ]
    .filter(Boolean)
    .join(" ")
}

export const SystematicRoutingGuardPlugin: Plugin = async () => {
  const mode = guardMode()
  const activeBySession = new Map<string, ActiveWorkflow>()
  let warnedModelStrip = false
  let warnedQualifiedRewrite = false
  const warnedInactiveWorkflow = new Set<string>()

  return {
    /**
     * A new user message starts a new routing turn. State is kept per session,
     * so subagent sessions cannot clear or contaminate their parent's state.
     */
    "chat.message": async (input) => {
      activeBySession.delete(input.sessionID)
    },

    "tool.execute.before": async (input, output) => {
      if (mode !== "off" && isRoutingGateTool(input.tool) && !isRoutingGateDisabled()) {
        const activeWorkflow = getActiveWorkflow(activeBySession, input.sessionID)
        const warningKey = `${input.sessionID}\u0000${input.tool}`
        if (!activeWorkflow && !warnedInactiveWorkflow.has(warningKey)) {
          warnedInactiveWorkflow.add(warningKey)
          await logInactiveWorkflowWarning(input.tool, input.sessionID)
          // Future block behavior could throw here; this rollout is warning-only.
        }
      }

      if (input.tool !== "task") return
      const args = output.args as Record<string, unknown> | undefined
      if (!args) return

      // OpenCode's current task schema has no `model` argument. Preserve the
      // historical defensive normalization so a stale Systematic/Gentle prompt
      // cannot defeat the configured agent model through an invalid field.
      if ("model" in args) {
        if (!warnedModelStrip) {
          warnedModelStrip = true
          console.warn(
            "[systematic-routing-guard] stripped unsupported `model` arg from task(); the selected agent's configured model applies instead.",
          )
        }
        delete args.model
      }

      // Qualified Systematic IDs are correct in prose, but OpenCode task()
      // dispatch expects the bare registered agent stem.
      if (typeof args.subagent_type === "string") {
        const match = QUALIFIED_SUBAGENT.exec(args.subagent_type)
        if (match) {
          if (!warnedQualifiedRewrite) {
            warnedQualifiedRewrite = true
            console.warn(
              "[systematic-routing-guard] normalized a qualified Systematic subagent_type to its bare OpenCode agent name.",
            )
          }
          args.subagent_type = match[1]
        }
      }

      if (mode === "off") return
      if (args.subagent_type !== "general" && args.subagent_type !== "explore") return

      const state = getActiveWorkflow(activeBySession, input.sessionID)
      if (!state) return

      const kind = classifyTask(args)
      if (!shouldBlockGeneric(args.subagent_type, kind, state)) return

      const message = routingViolationMessage(args.subagent_type, kind, state)
      if (mode === "warn") {
        console.warn(message)
        return
      }

      // Fail the tool call instead of silently rewriting to a guessed persona.
      // The model receives the diagnostic and can retry with the exact
      // specialist required by the active Systematic workflow.
      throw new Error(message)
    },

    /**
     * Loading a guarded Systematic workflow through systematic_skill (or the
     * generic skill tool) activates the session-local guard. We inspect only
     * dispatch-shaped syntax for extra target hints; ordinary qualified persona
     * references are left untouched.
     */
    "tool.execute.after": async (input, output) => {
      if (input.tool !== "systematic_skill" && input.tool !== "skill") return
      const args = input.args as Record<string, unknown> | undefined
      const rawName = args?.name
      const content = typeof output.output === "string" ? output.output : ""
      activateWorkflow(
        activeBySession,
        input.sessionID,
        rawName,
        input.tool === "systematic_skill" ? "systematic_skill" : "skill",
        content,
      )
    },

    /**
     * Slash-command execution may bypass an explicit systematic_skill() tool
     * call, so activate the same guard from the rendered command body.
     */
    "command.execute.before": async (input, output) => {
      const content = extractTextParts(output.parts)
      activateWorkflow(activeBySession, input.sessionID, input.command, "command", content)
    },
  }
}

export default SystematicRoutingGuardPlugin
