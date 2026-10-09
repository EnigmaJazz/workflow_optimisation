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

import { appendFile, copyFile, mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises"
import { constants, existsSync } from "node:fs"
import { homedir } from "node:os"
import { join, resolve } from "node:path"
import type { Plugin } from "@opencode-ai/plugin"
import {
  ROUTE_STAGES,
  READ_ONLY_SPECIALIST_PATTERNS,
  isCoordinator,
  pmRequiredRouteSkill,
  stageMarkerNames,
  taskWriteFile,
  type RouteStage,
} from "./lib/routing-guard-helpers"

let reportedRegistration = false

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
  "sandbox_write",
  "sandbox_edit",
  "sandbox_apply",
  "sandbox_apply_patch",
  "sandbox_bash",
  "sandbox_copy_in",
  "sandbox_copy_out",
  "sandbox_finish",
  "host_git_commit",
  "host_git_push",
  "host_gh_issue_create",
  "host_plan_append",
  "host_register_project",
  "host_sandbox_result_install",
  "host_sdd_archive_compose",
])

/** Host mutations additionally require a PM's own route adapter key. */
const HOST_MUTATION_GATE_TOOLS = new Set(
  [...ROUTING_GATE_TOOLS].filter((tool) => tool.startsWith("host_")),
)
// State root is read at each use (never fixed at import) so tests can redirect it.
const stateRoot = (): string => process.env.SYSTEMATIC_ROUTING_GUARD_STATE_ROOT ?? homedir()
const reportedFileLogFailures = new Set<string>()
const reportedBindingWriteFailures = new Set<string>()
const routingGateOffFile = (): string => join(stateRoot(), ".config/opencode/routing-guard-off")
const routingGateLogDir = (): string => join(stateRoot(), ".local/share/opencode/logs")
const routingGateLogFile = (): string => join(routingGateLogDir(), "routing-guard.log")
const routingKeyRoot = (): string => join(stateRoot(), ".local/share/opencode/routing-keys")

async function appendRoutingLog(line: string): Promise<void> {
  try {
    await mkdir(routingGateLogDir(), { recursive: true })
    await appendFile(routingGateLogFile(), `${new Date().toISOString()} ${line}\n`, "utf8")
  } catch (error) {
    const logPath = resolve(routingGateLogFile())
    const code = error && typeof error === "object" && "code" in error
      ? String((error as NodeJS.ErrnoException).code)
      : "unknown"
    const signature = `${logPath}\u0000${code}`
    if (!reportedFileLogFailures.has(signature)) {
      reportedFileLogFailures.add(signature)
      try {
        console.warn(
          `[systematic-routing-guard] file log append failed at ${logPath} (${code}): ${error instanceof Error ? error.message : String(error)}`,
        )
      } catch {
        // Reporting a logging failure must never fail the tool call.
      }
    }
  }
}

async function logObservedLine(line: string): Promise<void> {
  try {
    console.warn(line)
  } catch {
    // Observability must never affect plugin loading or a tool call.
  }
  await appendRoutingLog(line)
}

void logObservedLine("[systematic-routing-guard] module imported").catch(() => undefined)
// Override only for bounded timeout tests; clamp invalid or unsafe-small values to 10 ms.
const writeTimeoutMs = (): number => {
  const configured = Number(process.env.SYSTEMATIC_ROUTING_GUARD_WRITE_TIMEOUT_MS ?? 2000)
  return Number.isFinite(configured) ? Math.max(10, configured) : 2000
}
const MAX_INHERITANCE_HOPS = 3
const ROUTING_KEY_REFRESH_INTERVAL_MS = 60 * 1000
const ADAPTER_WORKFLOW_SKILLS = new Set([
  "workflow-odd-secure",
  "workflow-sdd-secure",
  "workflow-systematic",
])
const isReadOnlySpecialist = (name: string): boolean =>
  READ_ONLY_SPECIALIST_PATTERNS.some((pattern) => pattern.test(name))

/** Strip a leading `systematic:` qualifier, then sanitise, so qualified and bare names agree. */
function skillMarkerName(raw: string): string {
  const bare = raw.trim().replace(/^systematic:/, "")
  return bare.replace(/[^a-zA-Z0-9_-]/g, "-")
}

/** Await a write chain for at most WRITE_TIMEOUT_MS; errors are swallowed. */
async function boxed(work: Promise<unknown>): Promise<void> {
  let timer: ReturnType<typeof setTimeout> | undefined
  await Promise.race([
    work.catch(() => undefined),
    new Promise<void>((resolve) => { timer = setTimeout(resolve, writeTimeoutMs()) }),
  ])
  if (timer) clearTimeout(timer)
}

// sandbox_bash remains unable to be path-gated because its argv can execute arbitrary commands.
const FILE_MUTATING_TOOLS = new Set([
  "sandbox_write",
  "sandbox_edit",
  "sandbox_apply",
  "sandbox_apply_patch",
  "sandbox_copy_in",
  "sandbox_copy_out",
])

type WorkflowKeyStatus = "valid" | "missing" | "expired"

function routingKeySessionDirectory(sessionID: string): string | null {
  if (!/^[a-zA-Z0-9_-]+$/.test(sessionID)) return null
  return join(routingKeyRoot(), sessionID)
}

function routingKeyFile(sessionID: string, skillName: string): string | null {
  const directory = routingKeySessionDirectory(sessionID)
  if (!directory || !/^workflow-[a-zA-Z0-9_-]+$/.test(skillName)) return null
  return join(directory, `${skillName}.key`)
}

/**
 * Persist the most recently observed `chat.message` agent for a session.
 *
 * LIMITATION: `chat.message` reports the agent of one message and that value can vary per
 * message; this stores the latest observed value, not an authenticated or immutable session
 * identity. It is a guardrail input only, never an authorization fact. A missing or non-string
 * agent overwrites the previous value so a stale PM binding is not silently retained.
 */
async function persistLatestMessageAgent(sessionID: string, agent: unknown): Promise<void> {
  try {
    const directory = routingKeySessionDirectory(sessionID)
    if (!directory) return
    await mkdir(directory, { recursive: true })
    await writeFile(join(directory, ".agent"), typeof agent === "string" ? agent.trim() : "", "utf8")
  } catch (error) {
    const failureCode = error && typeof error === "object" && "code" in error
      ? String((error as NodeJS.ErrnoException).code)
      : "unknown"
    const failureKey = `${sessionID}\u0000${failureCode}`
    if (!reportedBindingWriteFailures.has(failureKey)) {
      reportedBindingWriteFailures.add(failureKey)
      try {
        console.warn(
          `[systematic-routing-guard] message-agent binding write failed (session: ${sessionID}, ${failureCode}): ${error instanceof Error ? error.message : String(error)}`,
        )
      } catch {
        // Reporting a binding failure must never fail a chat message.
      }
    }
  }
}

/** Read the last persisted message agent; a missing, unreadable or empty value yields null. */
async function readLatestMessageAgent(sessionID: string): Promise<string | null> {
  try {
    const directory = routingKeySessionDirectory(sessionID)
    if (!directory) return null
    const raw = (await readFile(join(directory, ".agent"), "utf8")).trim()
    return raw || null
  } catch {
    return null
  }
}

async function hasRouteStageArtifactInAncestorChain(
  sessionID: string,
  route: string,
  stage: RouteStage,
): Promise<boolean> {
  const visited = new Set<string>()
  let currentSessionID: string | null = sessionID
  const markerNames = [
    ...stageMarkerNames(route, stage.id, ROUTE_STAGES),
    ...(stage.skillMarkers ?? []).map((skillName) => `skill-${skillName}`),
  ]

  for (let depth = 0; currentSessionID && depth <= 3; depth++) {
    if (visited.has(currentSessionID)) return false
    visited.add(currentSessionID)

    const directory = routingKeySessionDirectory(currentSessionID)
    if (!directory) return false
    try {
      if (markerNames.some((markerName) => existsSync(join(directory, markerName)))) return true
    } catch {
      // Marker inspection must never block or fail a tool call.
    }

    if (depth === 3) return false
    try {
      const parentSessionID = (await readFile(join(directory, ".parent"), "utf8")).trim()
      if (!parentSessionID) return false
      currentSessionID = parentSessionID
    } catch {
      // A missing or unreadable parent marker ends the bounded ancestor walk.
      return false
    }
  }

  return false
}

async function deleteWorkflowKeyDirectory(sessionID: string): Promise<void> {
  try {
    const directory = routingKeySessionDirectory(sessionID)
    if (directory) await rm(directory, { recursive: true, force: true })
  } catch {
    // Key cleanup must never block or fail a tool call.
  }
}

async function refreshWorkflowKeyActivity(
  sessionID: string,
  lastRefreshBySession: Map<string, number>,
): Promise<void> {
  const now = Date.now()
  if (now - (lastRefreshBySession.get(sessionID) ?? 0) < ROUTING_KEY_REFRESH_INTERVAL_MS) return
  lastRefreshBySession.set(sessionID, now)

  try {
    // Refresh only the VALID key the inheritance walk finds; an expired key is never revived.
    const { valid } = await walkWorkflowKeys(sessionID)
    for (const { path, key } of valid) {
      try {
        await writeFile(path, JSON.stringify({ ...key, last_active: now }), "utf8")
      } catch {
        // Ignore unwritable key files.
      }
    }
  } catch {
    // Key activity refresh must never block or fail a tool call.
  }
}


async function mintWorkflowKey(
  sessionID: string,
  skillName: string,
  specialists: string[],
): Promise<void> {
  try {
    const directory = routingKeySessionDirectory(sessionID)
    const file = routingKeyFile(sessionID, skillName)
    if (!directory || !file) return
    await mkdir(directory, { recursive: true })
    const mintedAt = Date.now()
    let parentSessionID = ""
    let hasParentMarker = false
    try {
      parentSessionID = (await readFile(join(directory, ".parent"), "utf8")).trim()
      hasParentMarker = true
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") return
    }
    if (hasParentMarker) {
      const boundAgent = await readLatestMessageAgent(sessionID)
      const requiredSkill = boundAgent ? pmRequiredRouteSkill(boundAgent) : null
      if (requiredSkill === skillName) {
        // A bound PM must own its adapter key even when a .parent marker exists, otherwise its
        // own-session key requirement is unsatisfiable after a resume. The binding is the latest
        // observed message agent, not a session identity.
        await writeFile(
          file,
          JSON.stringify({ skill: skillName, minted_at: mintedAt, last_active: mintedAt, specialists }),
          "utf8",
        )
        return
      }
      await writeFile(
        join(directory, "inherited.key"),
        JSON.stringify({ inherited_from: parentSessionID, minted_at: mintedAt, last_active: mintedAt }),
        "utf8",
      )
      return
    }
    await writeFile(
      file,
      JSON.stringify({ skill: skillName, minted_at: mintedAt, last_active: mintedAt, specialists }),
      "utf8",
    )
  } catch {
    // Key persistence must never block or fail a tool call.
  }
}

/**
 * Walk the session and up to three inherited ancestors (visited set; a cycle stops the walk).
 * The first session holding a valid key wins; its valid key files are returned for refresh.
 */
async function walkWorkflowKeys(
  sessionID: string,
  requiredSkill?: string,
): Promise<{ status: WorkflowKeyStatus; valid: Array<{ path: string; key: Record<string, unknown> }> }> {
  const visited = new Set<string>()
  let foundExpired = false
  let current: string | null = sessionID
  try {
    for (let hop = 0; current && hop <= MAX_INHERITANCE_HOPS; hop++) {
      if (visited.has(current)) break
      visited.add(current)
      const directory = routingKeySessionDirectory(current)
      if (!directory) break
      let files: string[]
      try {
        files = await readdir(directory)
      } catch {
        break
      }
      const valid: Array<{ path: string; key: Record<string, unknown> }> = []
      let inheritedFrom: string | null = null
      for (const file of files) {
        if (file === "inherited.key") {
          try {
            const inherited = JSON.parse(await readFile(join(directory, file), "utf8")) as { inherited_from?: unknown }
            if (typeof inherited.inherited_from === "string") inheritedFrom = inherited.inherited_from
          } catch {
            // Ignore unreadable or malformed inherited keys.
          }
          continue
        }
        if (!/^workflow-[a-zA-Z0-9_-]+\.key$/.test(file)) continue
        try {
          const path = join(directory, file)
          const key = JSON.parse(await readFile(path, "utf8")) as Record<string, unknown>
          if (
            typeof key.skill !== "string" ||
            (requiredSkill ? key.skill !== requiredSkill : !ADAPTER_WORKFLOW_SKILLS.has(key.skill))
          ) continue
          if (typeof key.minted_at !== "number") continue
          const lastActive = typeof key.last_active === "number" ? key.last_active : key.minted_at
          if (Date.now() - lastActive <= ACTIVE_TTL_MS) valid.push({ path, key })
          else foundExpired = true
        } catch {
          // Ignore unreadable or malformed key files.
        }
      }
      if (valid.length > 0) return { status: "valid", valid }
      current = inheritedFrom
    }
  } catch {
    // Key inspection must never block or fail a tool call.
  }
  return { status: foundExpired ? "expired" : "missing", valid: [] }
}

async function getWorkflowKeyStatus(
  sessionID: string,
  requiredSkill?: string,
): Promise<WorkflowKeyStatus> {
  return (await walkWorkflowKeys(sessionID, requiredSkill)).status
}

/**
 * Own-directory key status only: unlike `walkWorkflowKeys`, no ancestor is consulted, so an
 * inherited or unrelated adapter key can never satisfy a PM's own-route requirement. An
 * expired key is reported as expired and is never revived by the refresh pass.
 */
async function getOwnWorkflowKeyStatus(
  sessionID: string,
  requiredSkill: string,
): Promise<WorkflowKeyStatus> {
  const file = routingKeyFile(sessionID, requiredSkill)
  if (!file) return "missing"
  try {
    const key = JSON.parse(await readFile(file, "utf8")) as Record<string, unknown>
    if (key.skill !== requiredSkill || typeof key.minted_at !== "number") return "missing"
    const lastActive = typeof key.last_active === "number" ? key.last_active : key.minted_at
    return Date.now() - lastActive <= ACTIVE_TTL_MS ? "valid" : "expired"
  } catch {
    return "missing"
  }
}

function isRoutingGateTool(tool: string): boolean {
  return (
    ROUTING_GATE_TOOLS.has(tool) ||
    tool.startsWith("host_review_") ||
    tool.startsWith("host_sdd_")
  )
}

function isRoutingGateDisabled(): boolean {
  try {
    return existsSync(routingGateOffFile())
  } catch {
    return false
  }
}

async function logInactiveWorkflowWarning(
  tool: string,
  sessionID: string,
  failure: string,
  warnConsole: boolean,
): Promise<void> {
  const message = `routing gate: ${tool} is not authorized for this change (${failure}); load the workflow-route skill (or the selected adapter skill) before dispatching`
  const line = `[systematic-routing-guard] ${message} (session: ${sessionID})`
  if (warnConsole) console.warn(line)

  await appendRoutingLog(line)
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

/** Paths a tool call writes; null when the path cannot be known (sandbox_apply, sandbox_bash). */
function writtenPaths(tool: string, args: Record<string, unknown> | undefined): string[] | null {
  if (!args) return null
  switch (tool) {
    case "sandbox_write":
    case "sandbox_edit":
      return typeof args.path === "string" ? [args.path] : null
    case "sandbox_copy_in":
      return typeof args.workerPath === "string" ? [args.workerPath] : null
    case "sandbox_copy_out":
      return typeof args.hostTarget === "string" ? [args.hostTarget] : null
    case "sandbox_apply_patch": {
      if (typeof args.patch !== "string") return null
      const paths: string[] = []
      for (const line of args.patch.split("\n")) {
        const match = /^\+\+\+ (.+?)\s*$/.exec(line.replace(/\r$/, ""))
        if (!match) continue
        const target = match[1].split("\t")[0].trim()
        if (!target || target === "/dev/null") continue
        paths.push(target.replace(/^b\//, ""))
      }
      return paths
    }
    default:
      return null
  }
}

export const SystematicRoutingGuardPlugin: Plugin = async () => {
  console.warn("[systematic-routing-guard] factory entered")
  const mode = guardMode()
  if (!reportedRegistration) {
    reportedRegistration = true
    await logObservedLine(`[systematic-routing-guard] plugin registered mode=${mode} stateRoot=${resolve(stateRoot())}`)
  }
  const activeBySession = new Map<string, ActiveWorkflow>()
  const lastKeyRefreshBySession = new Map<string, number>()
  let warnedModelStrip = false
  let warnedQualifiedRewrite = false
  // One de-dup set for every console warning: sessionID + tool + failure text.
  const warnedConsole = new Set<string>()
  const reportedKeyStatuses = new Set<string>()

  const warn = async (tool: string, sessionID: string, failure: string): Promise<void> => {
    const warningKey = `${sessionID}\u0000${tool}\u0000${failure}`
    const toConsole = !warnedConsole.has(warningKey)
    if (toConsole) warnedConsole.add(warningKey)
    await logInactiveWorkflowWarning(tool, sessionID, failure, toConsole)
  }

  return {
    /**
     * A new user message starts a new routing turn. State is kept per session,
     * so subagent sessions cannot clear or contaminate their parent's state.
     */
    "chat.message": async (input) => {
      activeBySession.delete(input.sessionID)
      lastKeyRefreshBySession.delete(input.sessionID)
      // The guard observes the message agent here; it is the latest observed value, not an
      // authenticated session identity.
      await boxed(persistLatestMessageAgent(input.sessionID, input.agent))
    },

    "tool.execute.before": async (input, output) => {
      // Refresh before the status check: it must see the refreshed key.
      await boxed(refreshWorkflowKeyActivity(input.sessionID, lastKeyRefreshBySession))
      const args = output.args as Record<string, unknown> | undefined
      const paths = writtenPaths(input.tool, args)
      const stagesWritten: Array<{ route: string; stage: RouteStage }> = []
      for (const [route, stages] of Object.entries(ROUTE_STAGES)) {
        for (const stage of stages) {
          if (paths?.some((path) => stage.artifactPattern?.test(path))) stagesWritten.push({ route, stage })
        }
      }
      if (stagesWritten.length > 0) {
        const directory = routingKeySessionDirectory(input.sessionID)
        if (directory) {
          await boxed(
            mkdir(directory, { recursive: true }).then(() => Promise.all(stagesWritten.map(({ route, stage }) =>
              writeFile(join(directory, `artifact-${route}-${stage.id}`), new Date().toISOString(), "utf8"),
            ))),
          )
        }
      }
      if (mode !== "off" && isRoutingGateTool(input.tool) && !isRoutingGateDisabled()) {
        const activeWorkflow = getActiveWorkflow(activeBySession, input.sessionID)
        const keyStatus = await getWorkflowKeyStatus(input.sessionID)
        const keyStatusLogKey = `${input.sessionID}\u0000${keyStatus}`
        if (!reportedKeyStatuses.has(keyStatusLogKey)) {
          reportedKeyStatuses.add(keyStatusLogKey)
          try {
            await logObservedLine(`[systematic-routing-guard] workflow key status=${keyStatus} (session: ${input.sessionID})`)
          } catch {
            // Key-status observability must never affect a tool call.
          }
        }
        if (keyStatus !== "valid") {
          const failures = [
            keyStatus === "missing"
              ? "workflow key status: missing (no valid adapter workflow key exists)"
              : "workflow key status: expired (workflow key expired)",
            activeWorkflow ? "in-memory activation present (context only)" : "in-memory activation absent (context only)",
          ]
          await warn(input.tool, input.sessionID, failures.join("; "))
          // Future block behavior could throw here; this rollout is warning-only.
        }

        // A PM must hold its own route adapter key before gated host mutations and every
        // host_review_* call. The binding is the persisted latest observed message agent, never
        // input.agent/output.agent. Own-directory validation only: an inherited or unrelated
        // adapter key does not satisfy it. Warning-only, exactly like the key gate above.
        const boundAgent = await readLatestMessageAgent(input.sessionID)
        const requiredPmSkill = boundAgent ? pmRequiredRouteSkill(boundAgent) : null
        if (
          requiredPmSkill &&
          (HOST_MUTATION_GATE_TOOLS.has(input.tool) || input.tool.startsWith("host_review_"))
        ) {
          const ownStatus = await getOwnWorkflowKeyStatus(input.sessionID, requiredPmSkill)
          if (ownStatus !== "valid") {
            await warn(
              input.tool,
              input.sessionID,
              `${boundAgent} requires its own ${requiredPmSkill} route key before ${input.tool} (PM session key status: ${ownStatus})`,
            )
          }
        }

        if (input.tool === "host_review_start") {
          try {
            if ((await getWorkflowKeyStatus(input.sessionID, "workflow-systematic")) === "valid") {
              const reviewStage = ROUTE_STAGES["workflow-systematic"].find((stage) => stage.id === "review")
              if (
                reviewStage &&
                !(await hasRouteStageArtifactInAncestorChain(input.sessionID, "workflow-systematic", reviewStage))
              ) {
                await warn(
                  input.tool,
                  input.sessionID,
                  `workflow-systematic review started before ${reviewStage.id} stage artifact exists`,
                )
              }
            }
          } catch {
            // Review-stage observation must never block or fail a tool call.
          }
        }

        // The guard is project-blind: in a multi-project session, a marker cannot satisfy a stage for the other project. A true fix needs a verified session-project source.
        if (FILE_MUTATING_TOOLS.has(input.tool) && paths && paths.length > 0) {
          for (const [routeSkill, stages] of Object.entries(ROUTE_STAGES)) {
            if (routeSkill !== "workflow-odd-secure") continue
            if ((await getWorkflowKeyStatus(input.sessionID, routeSkill)) !== "valid") continue
            for (const stage of stages) {
              // A call that writes the stage artifact itself counts as writing it.
              if (paths.some((path) => stage.artifactPattern?.test(path))) continue
              if (await hasRouteStageArtifactInAncestorChain(input.sessionID, routeSkill, stage)) continue
              await warn(
                input.tool,
                input.sessionID,
                `${routeSkill} bootstrap: write to ${paths.join(", ")} before ${stage.id} stage artifact exists`,
              )
            }
          }
        }
      }

      if (input.tool !== "task" || !args) return

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

      const dispatchedType = typeof args.subagent_type === "string" ? args.subagent_type : null
      if (mode !== "off" && dispatchedType && !isCoordinator(dispatchedType) && !isReadOnlySpecialist(dispatchedType)) {
        try {
          for (const [routeSkill, stages] of Object.entries(ROUTE_STAGES)) {
            if ((await getWorkflowKeyStatus(input.sessionID, routeSkill)) !== "valid") continue
            for (const stage of stages) {
              if (!stage.allowsSpecialists) continue
              if (!(await hasRouteStageArtifactInAncestorChain(input.sessionID, routeSkill, stage))) {
                await warn(
                  "task",
                  input.sessionID,
                  `${routeSkill} specialist ${dispatchedType} dispatched before ${stage.id} stage artifact exists`,
                )
              } else if (!stage.allowsSpecialists.includes(dispatchedType)) {
                await warn(
                  "task",
                  input.sessionID,
                  `${routeSkill} specialist ${dispatchedType} is not allowed at ${stage.id} stage`,
                )
              }
            }
          }
        } catch {
          // Specialist-stage observation must never block or fail a tool call.
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
      if (input.tool === "task") {
        try {
          const result = typeof output.output === "string" ? output.output : JSON.stringify(output.output ?? "")
          const childSessionID = result.match(/id="(ses_[A-Za-z0-9]+)"/)?.[1]
          if (!childSessionID || childSessionID === input.sessionID) return
          const directory = routingKeySessionDirectory(childSessionID)
          if (!directory) return
          await boxed((async () => {
            await mkdir(directory, { recursive: true })
            await taskWriteFile(join(directory, ".parent"), input.sessionID, "utf8")
            try {
              const parentDirectory = routingKeySessionDirectory(input.sessionID)
              if (parentDirectory) {
                await mkdir(parentDirectory, { recursive: true })
                const childEntries = await readdir(directory, { withFileTypes: true })
                const observedMarkers = childEntries
                  .filter((entry) => entry.isFile() && /^(artifact-|skill-)/.test(entry.name))
                  .slice(0, 64)
                await Promise.all(observedMarkers.map(async (entry) => {
                  try {
                    await copyFile(
                      join(directory, entry.name),
                      join(parentDirectory, entry.name),
                      constants.COPYFILE_EXCL,
                    )
                  } catch {
                    // Marker merge must not overwrite parent state or fail the task result hook.
                  }
                }))
              }
            } catch {
              // Marker enumeration and merge are best-effort and never affect key inheritance.
            }
            const files = await readdir(directory)
            await Promise.all(
              files
                .filter((file) => /^workflow-[a-zA-Z0-9_-]+\.key$/.test(file))
                .map((file) => rm(join(directory, file), { force: true })),
            )
            const mintedAt = Date.now()
            await taskWriteFile(
              join(directory, "inherited.key"),
              JSON.stringify({ inherited_from: input.sessionID, minted_at: mintedAt, last_active: mintedAt }),
              "utf8",
            )
          })())
        } catch {
          // Malformed task results must never block or fail a tool call.
        }
        return
      }
      if (input.tool !== "systematic_skill" && input.tool !== "skill") return
      const args = ((output.args ?? input.args) as Record<string, unknown> | undefined)
      const rawName = args?.name
      if (typeof rawName === "string") {
        const sanitizedName = skillMarkerName(rawName)
        const canonicalName = canonicalSkillName(rawName)
        if (
          !ADAPTER_WORKFLOW_SKILLS.has(canonicalName ?? "") &&
          !/(?:research|analyst)/i.test(sanitizedName)
        ) {
          try {
            for (const [routeSkill, stages] of Object.entries(ROUTE_STAGES)) {
              if ((await getWorkflowKeyStatus(input.sessionID, routeSkill)) !== "valid") continue
              for (const stage of stages) {
                if (!stage.gatesSkillLoads?.includes(sanitizedName)) continue
                if (await hasRouteStageArtifactInAncestorChain(input.sessionID, routeSkill, stage)) continue
                await warn(
                  input.tool,
                  input.sessionID,
                  `${routeSkill} skill ${sanitizedName} loaded before ${stage.id} stage artifact exists`,
                )
              }
            }
          } catch {
            // Skill-stage observation must never block or fail a tool call.
          }
        }
        const directory = routingKeySessionDirectory(input.sessionID)
        if (directory) {
          await boxed(
            mkdir(directory, { recursive: true })
              .then(() => writeFile(join(directory, `skill-${sanitizedName}`), new Date().toISOString(), "utf8")),
          )
        }
      }
      const content = typeof output.output === "string" ? output.output : ""
      activateWorkflow(
        activeBySession,
        input.sessionID,
        rawName,
        input.tool === "systematic_skill" ? "systematic_skill" : "skill",
        content,
      )
      const loadedSkillName = canonicalSkillName(rawName)
      const activeWorkflow = getActiveWorkflow(activeBySession, input.sessionID)
      if (loadedSkillName?.startsWith("workflow-")) {
        await boxed(mintWorkflowKey(input.sessionID, loadedSkillName, activeWorkflow ? [...activeWorkflow.targets] : []))
      }
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
void logObservedLine("[systematic-routing-guard] module evaluated").catch(() => undefined)
