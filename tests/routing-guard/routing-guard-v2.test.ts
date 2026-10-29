// V2 adapter acceptance tests for global-config/plugins/systematic-routing-guard.ts (setup()).
// Facts from the B1 probe (OpenCode V2 2.2.0): tool hooks carry a host-supplied `agent`; the shell/
// task tool is `subagent` with input { agent, description, prompt }; its execute.after result is
// { output: { sessionID }, content: [{ text: '<subagent sessionID="ses_..." ...>' }] };
// session.created events carry only data.sessionID (the parent comes from ctx.session.get);
// the `skill` tool takes { id }, `systematic_skill` takes { name }.
//
// Run ONLY via:  HOME="$(mktemp -d)" bun test tests/routing-guard

import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, spyOn, test } from "bun:test"
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { homedir, tmpdir } from "node:os"
import { join } from "node:path"

if (!homedir().startsWith(tmpdir()) && !homedir().startsWith("/tmp")) {
  throw new Error(`refusing to run against a real HOME (${homedir()}): use HOME="$(mktemp -d)" bun test tests/routing-guard`)
}

const GUARD = join(import.meta.dir, "..", "..", "global-config", "plugins", "systematic-routing-guard.ts")
const ODD = "workflow-odd-secure"

let root: string
let warnSpy: ReturnType<typeof spyOn>
let guard: any
let v2: ReturnType<typeof makeV2>
let cleanup: () => Promise<void>

const keyRoot = () => join(root, ".local", "share", "opencode", "routing-keys")
const sessionDir = (sid: string) => join(keyRoot(), sid)
const logFile = () => join(root, ".local", "share", "opencode", "logs", "routing-guard.log")
const logText = () => (existsSync(logFile()) ? readFileSync(logFile(), "utf8") : "")
const logCount = (needle: string) => logText().split("\n").filter((l) => l.includes(needle) && !l.includes("workflow key status=")).length
const hasFile = (sid: string, name: string) => existsSync(join(sessionDir(sid), name))

function seedKey(sid: string, skill: string) {
  mkdirSync(sessionDir(sid), { recursive: true })
  const t = Date.now()
  writeFileSync(join(sessionDir(sid), `${skill}.key`), JSON.stringify({ skill, minted_at: t, last_active: t, specialists: [] }))
}

function makeV2() {
  const hooks: Record<string, (event: any) => any> = {}
  const sessions = new Map<string, any>()
  const queue: any[] = []
  let wake: (() => void) | undefined
  let stopped = false
  let disposed = 0
  const reg = (kind: string) => async (name: string, cb: (event: any) => any) => {
    hooks[`${kind}:${name}`] = cb
    return { dispose: async () => { disposed++ } }
  }
  const ctx = {
    session: { hook: reg("session"), get: async ({ sessionID }: { sessionID: string }) => {
      if (!sessions.has(sessionID)) throw new Error("unknown session")
      return sessions.get(sessionID)
    } },
    tool: { hook: reg("tool") },
    event: { subscribe: () => ({ [Symbol.asyncIterator]() { return {
      next: () => new Promise<any>((resolve) => {
        const go = () => { if (stopped) return resolve({ done: true }); if (queue.length) return resolve({ value: queue.shift(), done: false }); wake = go }
        go()
      }),
      return: async () => { stopped = true; wake?.(); return { done: true } },
    } } }) },
  }
  return {
    ctx, hooks, sessions,
    emit: (event: any) => { queue.push(event); wake?.() },
    disposed: () => disposed,
  }
}

const before = (tool: string, sid: string, input: Record<string, unknown>, agent = "build") =>
  v2.hooks["tool:execute.before"]({ tool, sessionID: sid, agent, id: "c1", messageID: "m1", input })
const after = (tool: string, sid: string, input: Record<string, unknown>, result: unknown, agent = "build") =>
  v2.hooks["tool:execute.after"]({ tool, sessionID: sid, agent, id: "c1", messageID: "m1", input, status: "completed", result })
const subagent = (sid: string, agent: string, description = "do work", extra: Record<string, unknown> = {}) =>
  before("subagent", sid, { agent, description, prompt: "do work", ...extra })
const settle = () => new Promise((r) => setTimeout(r, 60))

beforeAll(() => { warnSpy = spyOn(console, "warn").mockImplementation(() => {}) })
afterAll(() => { warnSpy.mockRestore() })

beforeEach(async () => {
  root = mkdtempSync(join(tmpdir(), "guard-v2-test-"))
  process.env.SYSTEMATIC_ROUTING_GUARD_STATE_ROOT = root
  process.env.SYSTEMATIC_ROUTING_GUARD_MODE = "warn"
  guard = await import(GUARD)
  v2 = makeV2()
  cleanup = await guard.default.setup(v2.ctx)
})

afterEach(async () => {
  await cleanup()
  delete process.env.SYSTEMATIC_ROUTING_GUARD_STATE_ROOT
  delete process.env.SYSTEMATIC_ROUTING_GUARD_MODE
  rmSync(root, { recursive: true, force: true })
})

describe("V2 adapter", () => {
  test("setup registers the prompt, execute.before and execute.after hooks and cleanup disposes them", async () => {
    expect(Object.keys(v2.hooks).sort()).toEqual(["session:prompt", "tool:execute.after", "tool:execute.before"])
    await cleanup()
    expect(v2.disposed()).toBe(3)
    cleanup = async () => {}
  })

  test("a subagent dispatch is gated exactly like a V1 task dispatch (positive control)", async () => {
    seedKey("ses_s1", ODD)
    await subagent("ses_s1", "general")
    expect(logCount(`${ODD} specialist general dispatched before tracker stage artifact exists`)).toBe(1)
    // control: with no key nothing about this specialist is reported
    await subagent("ses_nokey", "general")
    expect(logText()).toContain("ses_s1") // the log is readable, so the absence below is meaningful
    expect(logText()).not.toContain("specialist general dispatched before tracker stage artifact exists (session: ses_nokey")
  })

  test("the host-supplied agent binds the session, so an orchestrator dispatching a writer is reported", async () => {
    seedKey("ses_orch", ODD)
    await subagent("ses_orch", "systematic-implementer")
    // agent defaults to "build": no orchestrator warning
    expect(logCount("orchestrator dispatched writing specialist systematic-implementer")).toBe(0)
    seedKey("ses_orch2", ODD)
    await before("subagent", "ses_orch2", { agent: "systematic-implementer", description: "w", prompt: "w" }, "gentle-orchestrator")
    expect(logCount("orchestrator dispatched writing specialist systematic-implementer")).toBe(1)
    expect(readFileSync(join(sessionDir("ses_orch2"), ".agent"), "utf8")).toContain("gentle-orchestrator")
  })

  test("a qualified Systematic agent name is normalised in place on the V2 input", async () => {
    const input = { agent: "systematic:review:code-reviewer", description: "r", prompt: "r" }
    await before("subagent", "ses_q", input)
    expect(input.agent).toBe("code-reviewer")
  })

  test("the V2 model argument is left alone (V1 stripped it because the V1 task schema had none)", async () => {
    const input = { agent: "general", description: "r", prompt: "r", model: "openai/gpt-5" }
    await before("subagent", "ses_m", input)
    expect(input.model).toBe("openai/gpt-5")
  })

  test("a completed subagent result links the child session to its parent from the structured result", async () => {
    const result = { output: { sessionID: "ses_child1", status: "completed" },
      content: [{ type: "text", text: '<subagent sessionID="ses_child1" state="completed">\nok\n</subagent>' }],
      metadata: { sessionID: "ses_child1" } }
    await after("subagent", "ses_parent", { agent: "general", description: "d", prompt: "p" }, result)
    expect(readFileSync(join(sessionDir("ses_child1"), ".parent"), "utf8")).toBe("ses_parent")
    expect(hasFile("ses_child1", "inherited.key")).toBe(true)
  })

  test("positive control: a result with no session id links nothing", async () => {
    await after("subagent", "ses_parent2", { agent: "general", description: "d", prompt: "p" }, { content: [{ type: "text", text: "no id here" }] })
    expect(existsSync(sessionDir("ses_parent2"))).toBe(false)
    expect(existsSync(sessionDir("ses_child1"))).toBe(false)
  })

  test("a skill load with the V2 { id } input writes the skill marker", async () => {
    await after("skill", "ses_skill", { id: "ce:plan" }, { content: [{ type: "text", text: "plan instructions" }] })
    expect(hasFile("ses_skill", "skill-ce-plan")).toBe(true)
  })

  test("the systematic_skill { name } input is handled the same way", async () => {
    await after("systematic_skill", "ses_skill2", { name: "ce:plan" }, { content: [{ type: "text", text: "plan" }] })
    expect(hasFile("ses_skill2", "skill-ce-plan")).toBe(true)
  })

  test("tiny-fix permit flows through V2 events: dispatch, child session.created, child tool hook with the expected agent", async () => {
    await subagent("ses_tf_parent", "systematic-implementer", "[tiny-fix] adjust a constant")
    v2.sessions.set("ses_tf_child", { id: "ses_tf_child", parentID: "ses_tf_parent", location: { directory: "/p" } })
    v2.emit({ type: "session.created", data: { sessionID: "ses_tf_child" } })
    await settle()
    await before("sandbox_write", "ses_tf_child", { path: "a.txt", content: "x" }, "systematic-implementer")
    expect(logCount("tiny-fix permit extended to child session ses_tf_child (parent: ses_tf_parent)")).toBe(1)
  })

  test("positive control: a child whose agent differs from the dispatched writer gets no permit", async () => {
    await subagent("ses_tf_parent2", "systematic-implementer", "[tiny-fix] adjust a constant")
    v2.sessions.set("ses_tf_child2", { id: "ses_tf_child2", parentID: "ses_tf_parent2" })
    v2.emit({ type: "session.created", data: { sessionID: "ses_tf_child2" } })
    await settle()
    await before("sandbox_write", "ses_tf_child2", { path: "a.txt", content: "x" }, "some-other-agent")
    expect(logCount("tiny-fix permit extended to child session ses_tf_child2")).toBe(0)
  })

  test("session.deleted is accepted and an unknown session in session.created does not break the stream", async () => {
    v2.emit({ type: "session.created", data: { sessionID: "ses_unknown" } })
    v2.emit({ type: "session.deleted", data: { sessionID: "ses_unknown" } })
    await settle()
    await expect(subagent("ses_after_events", "general")).resolves.toBeUndefined()
  })

  test("the prompt hook starts a new routing turn without clearing the persisted agent binding", async () => {
    await before("subagent", "ses_turn", { agent: "general", description: "d", prompt: "p" }, "pm-odd")
    v2.hooks["session:prompt"]({ sessionID: "ses_turn", prompt: { parts: [] } })
    expect(readFileSync(join(sessionDir("ses_turn"), ".agent"), "utf8")).toContain("pm-odd")
  })
})

describe("V2 agent-observation log", () => {
  test("a V2 observation is labelled with the V2 hook, and V1 keeps its own label", async () => {
    process.env.SYSTEMATIC_ROUTING_GUARD_OBSERVE_AGENT_HOOKS = "1"
    try {
      const other = makeV2()
      const stop = await guard.default.setup(other.ctx)
      await other.hooks["tool:execute.before"]({ tool: "read", sessionID: "ses_label", agent: "pm-odd", input: {} })
      await stop()
      const v1 = await guard.default.server({})
      await v1["chat.message"]({ sessionID: "ses_label_v1", agent: "pm-odd" })
    } finally {
      delete process.env.SYSTEMATIC_ROUTING_GUARD_OBSERVE_AGENT_HOOKS
    }
    const lines = logText().split("\n").filter((l) => l.includes("TEMP agent-hook"))
    expect(lines.some((l) => l.includes("hook=tool.execute.before") && l.includes("session=ses_label "))).toBe(true)
    expect(lines.some((l) => l.includes("hook=chat.message") && l.includes("session=ses_label_v1 "))).toBe(true)
    expect(lines.some((l) => l.includes("hook=chat.message") && l.includes("session=ses_label "))).toBe(false)
  })
})
