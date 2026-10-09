// Acceptance tests for global-config/plugins/systematic-routing-guard.ts
// Design: docs/specs/routing-guard-q03.md. Queue Q03.
//
// Run ONLY via:  HOME="$(mktemp -d)" bun test tests/routing-guard
// Two isolation layers: a throwaway HOME for the process (bun's homedir() reads HOME at start),
// and SYSTEMATIC_ROUTING_GUARD_STATE_ROOT per test (design section 0).

import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, spyOn, test } from "bun:test"
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { homedir, tmpdir } from "node:os"
import { join } from "node:path"
import {
  pmRequiredRouteSkill,
  READ_ONLY_SPECIALIST_PATTERNS,
  ROUTE_STAGES,
  setTaskWriteFileForTests,
  stageMarkerNames,
} from "../../global-config/plugins/lib/routing-guard-helpers"

if (!homedir().startsWith(tmpdir()) && !homedir().startsWith("/tmp")) {
  throw new Error(`refusing to run against a real HOME (${homedir()}): use HOME="$(mktemp -d)" bun test tests/routing-guard`)
}

const GUARD = join(import.meta.dir, "..", "..", "global-config", "plugins", "systematic-routing-guard.ts")
const ODD = "workflow-odd-secure"
const SYS = "workflow-systematic"

let root: string
let warnSpy: ReturnType<typeof spyOn>
let guard: any
let hooks: any

const keyRoot = () => join(root, ".local", "share", "opencode", "routing-keys")
const sessionDir = (sid: string) => join(keyRoot(), sid)
const logFile = () => join(root, ".local", "share", "opencode", "logs", "routing-guard.log")

function seedKey(sid: string, skill: string, ageMinutes = 0) {
  mkdirSync(sessionDir(sid), { recursive: true })
  const t = Date.now() - ageMinutes * 60_000
  writeFileSync(join(sessionDir(sid), `${skill}.key`),
    JSON.stringify({ skill, minted_at: t, last_active: t, specialists: [] }))
}
function seedInherited(child: string, parent: string) {
  mkdirSync(sessionDir(child), { recursive: true })
  writeFileSync(join(sessionDir(child), ".parent"), parent)
  writeFileSync(join(sessionDir(child), "inherited.key"),
    JSON.stringify({ inherited_from: parent, minted_at: Date.now(), last_active: Date.now() }))
}
function marker(sid: string, name: string) {
  mkdirSync(sessionDir(sid), { recursive: true })
  writeFileSync(join(sessionDir(sid), name), "x")
}
const markAdvice = (sid: string, route = ODD) => marker(sid, `artifact-${route}-advice`)
const hasFile = (sid: string, name: string) => existsSync(join(sessionDir(sid), name))
const logText = () => (existsSync(logFile()) ? readFileSync(logFile(), "utf8") : "")
const logCount = (needle: string) => logText().split("\n").filter((l) =>
  l.includes(needle) && !l.includes("workflow key status="),
).length
const consoleCount = (needle: string) =>
  warnSpy.mock.calls.filter((c: unknown[]) =>
    String(c[0]).includes(needle) && !String(c[0]).includes("workflow key status="),
  ).length

const before = (tool: string, sid: string, args: Record<string, unknown>) =>
  hooks["tool.execute.before"]({ tool, sessionID: sid, callID: "c1" }, { args })
const after = (tool: string, sid: string, args: Record<string, unknown>, output: unknown = "") =>
  hooks["tool.execute.after"]({ tool, sessionID: sid, callID: "c1", args }, { args, output, title: "", metadata: {} })
const dispatch = (sid: string, subagent: string) =>
  before("task", sid, { subagent_type: subagent, description: "do work", prompt: "do work" })
const message = (sid: string, agent: string) => hooks["chat.message"]({ sessionID: sid, agent })

// Positive control for absence assertions: proves this test's guard output really lands under the
// per-test state root, so "no warning" / "no marker" cannot pass vacuously.
async function probe() {
  await before("host_git_commit", "ses_probe", {})
  expect(logCount("ses_probe")).toBeGreaterThan(0)
}

beforeAll(() => {
  warnSpy = spyOn(console, "warn").mockImplementation(() => {})
})

afterAll(() => {
  warnSpy.mockRestore()
})

beforeEach(async () => {
  warnSpy.mockClear()
  root = mkdtempSync(join(tmpdir(), "guard-test-"))
  process.env.SYSTEMATIC_ROUTING_GUARD_STATE_ROOT = root
  process.env.SYSTEMATIC_ROUTING_GUARD_MODE = "warn"
  guard = await import(GUARD)
  hooks = await guard.default({} as any)
})

afterEach(() => {
  delete process.env.SYSTEMATIC_ROUTING_GUARD_STATE_ROOT
  delete process.env.SYSTEMATIC_ROUTING_GUARD_MODE
  rmSync(root, { recursive: true, force: true })
})

describe("0. state-root seam", () => {
  test("all guard state lands under SYSTEMATIC_ROUTING_GUARD_STATE_ROOT", async () => {
    await before("host_git_commit", "ses_seam", { message: "x" })
    expect(existsSync(logFile())).toBe(true)
    expect(logCount("ses_seam")).toBe(1)
  })

  test("de-duplicates failed file-log warnings by path and error code", async () => {
    const originalRoot = root
    const roots = [originalRoot, mkdtempSync(join(tmpdir(), "guard-log-failure-"))]
    try {
      for (const [index, failureRoot] of roots.entries()) {
        mkdirSync(join(failureRoot, ".local/share/opencode"), { recursive: true })
        rmSync(join(failureRoot, ".local/share/opencode/logs"), { recursive: true, force: true })
        writeFileSync(join(failureRoot, ".local/share/opencode/logs"), "not a directory")
        process.env.SYSTEMATIC_ROUTING_GUARD_STATE_ROOT = failureRoot
        await before("host_git_commit", `ses_log_failure_${index}`, {})
        await before("host_git_commit", `ses_log_failure_${index}`, {})
      }

      expect(consoleCount("file log append failed")).toBe(2)
    } finally {
      root = originalRoot
      process.env.SYSTEMATIC_ROUTING_GUARD_STATE_ROOT = originalRoot
      for (const failureRoot of roots.slice(1)) rmSync(failureRoot, { recursive: true, force: true })
    }
  })

  test("a failed append cannot reject the logging hook", async () => {
    const logs = join(root, ".local/share/opencode/logs")
    rmSync(logs, { recursive: true, force: true })
    mkdirSync(join(root, ".local/share/opencode"), { recursive: true })
    writeFileSync(logs, "not a directory")

    await expect(before("host_git_commit", "ses_log_rejection", {})).resolves.toBeUndefined()
  })

  test("failed message-agent binding writes report one best-effort breadcrumb", async () => {
    const validSession = "ses_binding_write_control"
    await expect(message(validSession, "pm-odd")).resolves.toBeUndefined()
    expect(readFileSync(join(sessionDir(validSession), ".agent"), "utf8")).toContain("pm-odd")
    expect(consoleCount("message-agent binding write failed")).toBe(0)

    const failedSession = "ses_binding_write_failure"
    mkdirSync(keyRoot(), { recursive: true })
    writeFileSync(sessionDir(failedSession), "not a directory")
    await expect(message(failedSession, "pm-odd")).resolves.toBeUndefined()
    await expect(message(failedSession, "pm-odd")).resolves.toBeUndefined()
    expect(consoleCount(`message-agent binding write failed (session: ${failedSession},`)).toBe(1)
  })
})

describe("7. exported stage table", () => {
  test("plugin exports only its factory functions", () => {
    const functionExports = Object.entries(guard)
      .filter(([, value]) => typeof value === "function")
      .map(([name]) => name)
      .sort()
    expect(functionExports).toEqual(["SystematicRoutingGuardPlugin", "default"])
  })

  test("plugin factory returns its recognized hooks", () => {
    const recognizedHooks = Object.keys(hooks).sort()
    expect(recognizedHooks).toEqual([
      "chat.message",
      "command.execute.before",
      "tool.execute.after",
      "tool.execute.before",
    ])
    console.log(`[plugin factory hooks] ${recognizedHooks.join(", ")}`)
  })

  test("ROUTE_STAGES is exported and well formed", () => {
    const stages = ROUTE_STAGES as Record<string, Array<Record<string, unknown>>>
    expect(Object.keys(stages).sort()).toEqual([ODD, SYS])
    for (const [route, list] of Object.entries(stages)) {
      const ids = list.map((s) => s.id)
      expect(new Set(ids).size).toBe(ids.length)
      for (const s of list) {
        expect(s.artifactPattern !== undefined || (Array.isArray(s.skillMarkers) && s.skillMarkers.length > 0)).toBe(true)
      }
      expect(route.startsWith("workflow-")).toBe(true)
    }
    expect(stages[ODD].map((s) => s.id)).toEqual(["advice", "tracker"])
    expect(stages[SYS].map((s) => s.id)).toEqual(["requirements", "advice", "plan", "review"])
  })

  test("READ_ONLY_SPECIALIST_PATTERNS is exported", () => {
    expect(Array.isArray(READ_ONLY_SPECIALIST_PATTERNS)).toBe(true)
  })
})

describe("1. specialist rule: deny by default", () => {
  test("listed writer before the tracker exists warns", async () => {
    seedKey("ses_s1", ODD)
    await dispatch("ses_s1", "general")
    expect(logCount(`${ODD} specialist general dispatched before tracker stage artifact exists`)).toBe(1)
  })

  test("UNLISTED writer before the tracker exists also warns", async () => {
    seedKey("ses_s2", ODD)
    await dispatch("ses_s2", "frontend-apply")
    expect(logCount(`${ODD} specialist frontend-apply dispatched before tracker stage artifact exists`)).toBe(1)
  })

  test("unknown agent names are treated as writers", async () => {
    seedKey("ses_s3", ODD)
    await dispatch("ses_s3", "mystery-writer")
    expect(logCount("specialist mystery-writer dispatched before tracker")).toBe(1)
  })

  test("a PM coordinator dispatched by the orchestrator is not treated as a writer", async () => {
    seedKey("ses_pm_orchestrator", ODD)
    marker("ses_pm_orchestrator", `artifact-${ODD}-tracker`)
    await dispatch("ses_pm_orchestrator", "pm-odd")
    expect(logCount("specialist pm-odd")).toBe(0)
    await probe()
  })

  test("unknown pm-* names remain coordinators, not writers", async () => {
    seedKey("ses_pm_unknown", ODD)
    await dispatch("ses_pm_unknown", "pm-not-registered")
    expect(logCount("specialist pm-not-registered")).toBe(0)
    await probe()
  })

  test("PM dispatch does not require writer-stage evidence", async () => {
    seedKey("ses_pm_no_stage", ODD)
    await dispatch("ses_pm_no_stage", "pm-odd")
    expect(logCount("specialist pm-odd dispatched before tracker")).toBe(0)
    await probe()
  })

  test("odd-apply is admitted at the ODD tracker stage", async () => {
    seedKey("ses_odd_apply", ODD)
    marker("ses_odd_apply", `artifact-${ODD}-tracker`)
    markAdvice("ses_odd_apply")
    await dispatch("ses_odd_apply", "odd-apply")
    expect(logCount("specialist odd-apply")).toBe(0)
    await probe()
  })

  test("odd-apply is not admitted at the Systematic plan stage", async () => {
    seedKey("ses_odd_apply_sys", SYS)
    marker("ses_odd_apply_sys", `artifact-${SYS}-plan`)
    await dispatch("ses_odd_apply_sys", "odd-apply")
    expect(logCount(`${SYS} specialist odd-apply is not allowed at plan stage`)).toBe(1)
  })

  test("listed writer after the tracker exists does not warn", async () => {
    seedKey("ses_s4", ODD)
    marker("ses_s4", `artifact-${ODD}-tracker`)
    markAdvice("ses_s4")
    await dispatch("ses_s4", "general")
    expect(logCount("specialist general")).toBe(0)
    await probe()
  })

  test("undeclared writer after the tracker exists warns 'not allowed'", async () => {
    seedKey("ses_s5", ODD)
    marker("ses_s5", `artifact-${ODD}-tracker`)
    await dispatch("ses_s5", "mystery-writer")
    expect(logCount(`${ODD} specialist mystery-writer is not allowed at tracker stage`)).toBe(1)
  })

  test("every declared writer is allowed once the tracker exists", async () => {
    seedKey("ses_s5b", ODD)
    marker("ses_s5b", `artifact-${ODD}-tracker`)
    markAdvice("ses_s5b")
    for (const name of ["general", "systematic-implementer", "frontend-dev", "frontend-dev-premium",
      "frontend-apply", "frontend-apply-local", "jd-fix-agent", "pr-comment-resolver",
      "bug-reproduction-validator", "design-iterator", "sdd-apply", "sdd-apply-local",
      "gentle-ai-worker", "gentle-ai-worker-local"]) {
      await dispatch("ses_s5b", name)
    }
    expect(logCount("specialist")).toBe(0)
    await probe()
  })

  test("real writers are NOT exempt: they warn before the tracker exists", async () => {
    seedKey("ses_s5c", ODD)
    for (const name of ["pr-comment-resolver", "bug-reproduction-validator", "sdd-apply", "design-iterator"]) {
      await dispatch("ses_s5c", name)
      expect(logCount(`specialist ${name} dispatched before tracker`)).toBe(1)
    }
  })

  test("read-only specialists are exempt", async () => {
    seedKey("ses_s6", ODD)
    for (const name of ["explore", "gentle-ai-explore", "gentle-ai-verify", "sdd-explore", "sdd-verify",
      "sdd-research", "vision", "architecture-strategist", "spec-flow-analyzer", "git-history-analyzer",
      "issue-intelligence-analyst", "pattern-recognition-specialist", "deployment-verification-agent",
      "repo-research-analyst", "best-practices-researcher", "framework-docs-researcher",
      "learnings-researcher", "correctness-reviewer", "review-refuter", "review-risk",
      "asi-review-risk", "asi-review-validator", "advisor-design-pre", "jd-judge-a", "jd-judge-b"]) {
      await dispatch("ses_s6", name)
    }
    expect(logCount("specialist")).toBe(0)
    await probe()
  })

  test("no valid route key means no specialist gating", async () => {
    await dispatch("ses_s7", "frontend-apply")
    expect(logCount("specialist")).toBe(0)
    await probe()
  })
})

describe("1b. orchestrator writer dispatch warning", () => {
  test("warns when the orchestrator dispatches a writer despite completed route setup", async () => {
    const sid = "ses_orchestrator_writer"
    await message(sid, "gentle-orchestrator")
    seedKey(sid, ODD)
    marker(sid, `artifact-${ODD}-tracker`)

    await expect(dispatch(sid, "systematic-implementer")).resolves.toBeUndefined()

    expect(logCount("orchestrator dispatched writing specialist systematic-implementer")).toBe(1)
    expect(logText()).toContain("orchestrator must delegate through the route coordinator")
  })

  test("does not warn when the orchestrator dispatches a coordinator", async () => {
    const sid = "ses_orchestrator_coordinator"
    await message(sid, "gentle-orchestrator")
    seedKey(sid, ODD)
    await dispatch(sid, "pm-odd")
    expect(logCount("orchestrator dispatched writing specialist")).toBe(0)
    await probe()
  })

  test("does not warn when the orchestrator dispatches a read-only specialist", async () => {
    const sid = "ses_orchestrator_readonly"
    await message(sid, "gentle-orchestrator")
    seedKey(sid, ODD)
    await dispatch(sid, "advisor-design-pre")
    expect(logCount("orchestrator dispatched writing specialist")).toBe(0)
    await probe()
  })

  test("does not warn when a non-orchestrator worker dispatches a writer", async () => {
    const sid = "ses_worker_writer"
    await message(sid, "systematic-implementer")
    seedKey(sid, ODD)
    marker(sid, `artifact-${ODD}-tracker`)
    await dispatch(sid, "frontend-apply")
    expect(logCount("orchestrator dispatched writing specialist")).toBe(0)
    await probe()
  })

  test("does not apply the orchestrator writer warning without a valid route key", async () => {
    const sid = "ses_orchestrator_no_key"
    await message(sid, "gentle-orchestrator")
    await dispatch(sid, "systematic-implementer")
    expect(logCount("orchestrator dispatched writing specialist")).toBe(0)
    await probe()
  })
})

describe("2. route-namespaced stage markers", () => {
  test("writing an ODD advice record writes namespaced advice markers before the hook returns", async () => {
    await before("sandbox_write", "ses_advice_marker", { path: "odd/advice/feature-x.md", content: "advice" })
    expect(hasFile("ses_advice_marker", `artifact-${ODD}-advice`)).toBe(true)
    expect(hasFile("ses_advice_marker", `artifact-${SYS}-advice`)).toBe(true)
  })

  test("writing the tracker writes the namespaced marker before the hook returns", async () => {
    seedKey("ses_m1", ODD)
    await before("sandbox_write", "ses_m1", { path: "odd/tasks/feature.md", content: "x" })
    expect(hasFile("ses_m1", `artifact-${ODD}-tracker`)).toBe(true)
  })

  test("writing a plan writes the systematic namespaced marker", async () => {
    await before("sandbox_write", "ses_m2", { path: "docs/plans/p-plan.md", content: "x" })
    expect(hasFile("ses_m2", `artifact-${SYS}-plan`)).toBe(true)
  })

  test("legacy ODD markers still satisfy the ODD tracker stage", async () => {
    for (const [sid, legacy] of [["ses_m3", "artifact-tracker"], ["ses_m4", "artifact-odd-tracker"]]) {
      seedKey(sid, ODD)
      marker(sid, legacy)
      markAdvice(sid)
      await dispatch(sid, "general")
      expect(logCount(`specialist general dispatched before tracker`)).toBe(0)
    }
    await probe()
  })

  test("an artifact-odd-* marker never satisfies another route's stage", async () => {
    seedKey("ses_m5", SYS)
    marker("ses_m5", "artifact-odd-plan")
    await dispatch("ses_m5", "general")
    expect(logCount(`${SYS} specialist general dispatched before plan stage artifact exists`)).toBe(1)
  })

  test("a legacy unnamespaced marker counts while its stage id is unique across routes", async () => {
    seedKey("ses_m5b", SYS)
    marker("ses_m5b", "artifact-plan")
    await dispatch("ses_m5b", "general")
    expect(logCount(`${SYS} specialist general dispatched before plan`)).toBe(0)
    await probe()
  })

  test("stageMarkerNames drops the legacy name once two routes share a stage id", () => {
    const table = {
      "workflow-odd-secure": [{ id: "tracker" }, { id: "plan" }],
      "workflow-systematic": [{ id: "plan" }, { id: "review" }],
    }
    const sys = stageMarkerNames("workflow-systematic", "plan", table)
    expect(sys).toContain("artifact-workflow-systematic-plan")
    expect(sys).not.toContain("artifact-plan")
    expect(sys).not.toContain("artifact-odd-plan")
    const odd = stageMarkerNames("workflow-odd-secure", "tracker", table)
    expect(odd).toEqual(expect.arrayContaining(["artifact-workflow-odd-secure-tracker", "artifact-tracker", "artifact-odd-tracker"]))
    const review = stageMarkerNames("workflow-systematic", "review", table)
    expect(review).toContain("artifact-review")
  })

  test("a skill marker satisfies its stage (skills are route-agnostic)", async () => {
    seedKey("ses_m6", SYS)
    marker("ses_m6", "skill-ce-plan")
    await dispatch("ses_m6", "general")
    expect(logCount(`${SYS} specialist general dispatched before plan`)).toBe(0)
    await probe()
  })

  test("child namespaced markers merge into the parent", async () => {
    marker("ses_child1", `artifact-${ODD}-tracker`)
    await after("task", "ses_parent1", { subagent_type: "general" }, 'task id="ses_child1" completed')
    expect(hasFile("ses_parent1", `artifact-${ODD}-tracker`)).toBe(true)
  })
})

describe("1c. pre-code advice stage", () => {
  test("a writer dispatch without an advice record warns and still resolves", async () => {
    const sid = "ses_advice_missing"
    seedKey(sid, ODD)
    marker(sid, `artifact-${ODD}-tracker`)

    await expect(dispatch(sid, "systematic-implementer")).resolves.toBeUndefined()

    expect(logCount(`${ODD} specialist systematic-implementer dispatched before advice record`)).toBe(1)
  })

  test("a Systematic writer dispatch also requires the shared advice record", async () => {
    const sid = "ses_systematic_advice_missing"
    seedKey(sid, SYS)
    marker(sid, `artifact-${SYS}-plan`)

    await expect(dispatch(sid, "systematic-implementer")).resolves.toBeUndefined()

    expect(logCount(`${SYS} specialist systematic-implementer dispatched before advice record`)).toBe(1)
  })

  test("a writer dispatch after the advice record exists does not warn", async () => {
    const sid = "ses_advice_present"
    seedKey(sid, ODD)
    marker(sid, `artifact-${ODD}-tracker`)
    await before("sandbox_write", sid, { path: "odd/advice/feature-x.md", content: "advice" })

    await dispatch(sid, "systematic-implementer")

    expect(logCount(`${ODD} specialist systematic-implementer dispatched before advice record`)).toBe(0)
    await probe()
  })

  test("a coordinator dispatch does not warn for missing advice", async () => {
    const sid = "ses_advice_coordinator"
    seedKey(sid, ODD)
    marker(sid, `artifact-${ODD}-tracker`)

    await dispatch(sid, "pm-odd")

    expect(logCount("dispatched before advice record")).toBe(0)
    await probe()
  })

  test("a read-only specialist dispatch does not warn for missing advice", async () => {
    const sid = "ses_advice_readonly"
    seedKey(sid, ODD)
    marker(sid, `artifact-${ODD}-tracker`)

    await dispatch(sid, "repo-research-analyst")

    expect(logCount("dispatched before advice record")).toBe(0)
    await probe()
  })
})

describe("3. written-path extraction", () => {
  test("sandbox_copy_out uses hostTarget, never the workerPath source", async () => {
    await before("sandbox_copy_out", "ses_p1", { workerPath: "odd/tasks/x.md", hostTarget: "/elsewhere/out.md" })
    expect(hasFile("ses_p1", `artifact-${ODD}-tracker`)).toBe(false)
    await probe()
  })

  test("sandbox_copy_in uses workerPath, the destination", async () => {
    await before("sandbox_copy_in", "ses_p2", { hostSource: "/elsewhere/in.md", workerPath: "odd/tasks/x.md" })
    expect(hasFile("ses_p2", `artifact-${ODD}-tracker`)).toBe(true)
  })

  test("apply_patch extracts every +++ b/ path", async () => {
    const patch = [
      "diff --git a/docs/plans/q-plan.md b/docs/plans/q-plan.md",
      "--- /dev/null",
      "+++ b/docs/plans/q-plan.md\t2026-10-02 10:00:00",
      "@@ -0,0 +1 @@",
      "+plan",
      "diff --git a/odd/tasks/t.md b/odd/tasks/t.md",
      "--- a/odd/tasks/t.md",
      "+++ b/odd/tasks/t.md",
      "@@ -1 +1 @@",
      "-old",
      "+new",
      "",
    ].join("\n")
    await before("sandbox_apply_patch", "ses_p3", { patch })
    expect(hasFile("ses_p3", `artifact-${SYS}-plan`)).toBe(true)
    expect(hasFile("ses_p3", `artifact-${ODD}-tracker`)).toBe(true)
  })

  test("a deletion (+++ /dev/null) is not a write", async () => {
    const patch = "diff --git a/odd/tasks/t.md b/odd/tasks/t.md\n--- a/odd/tasks/t.md\n+++ /dev/null\n@@ -1 +0,0 @@\n-old\n"
    await before("sandbox_apply_patch", "ses_p4", { patch })
    expect(hasFile("ses_p4", `artifact-${ODD}-tracker`)).toBe(false)
    await probe()
  })

  test("bootstrap: a patch to a source file before the tracker warns", async () => {
    seedKey("ses_p5", ODD)
    const patch = "diff --git a/src/a.ts b/src/a.ts\n--- a/src/a.ts\n+++ b/src/a.ts\n@@ -1 +1 @@\n-a\n+b\n"
    await before("sandbox_apply_patch", "ses_p5", { patch })
    expect(logCount(`${ODD} bootstrap: write to src/a.ts before tracker stage artifact exists`)).toBe(1)
  })

  test("bootstrap: a multi-file patch warns once, listing the non-tracker paths in order", async () => {
    seedKey("ses_p5m", ODD)
    const patch = [
      "diff --git a/src/a.ts b/src/a.ts", "--- a/src/a.ts", "+++ b/src/a.ts", "@@ -1 +1 @@", "-a", "+b",
      "diff --git a/src/b.ts b/src/b.ts", "--- a/src/b.ts", "+++ b/src/b.ts", "@@ -1 +1 @@", "-a", "+b", "",
    ].join("\n")
    await before("sandbox_apply_patch", "ses_p5m", { patch })
    expect(logCount(`${ODD} bootstrap: write to src/a.ts, src/b.ts before tracker stage artifact exists`)).toBe(1)
    expect(logCount("bootstrap")).toBe(1)
  })

  test("bootstrap: a patch that writes the tracker does not warn", async () => {
    seedKey("ses_p6", ODD)
    const patch = "diff --git a/odd/tasks/t.md b/odd/tasks/t.md\n--- /dev/null\n+++ b/odd/tasks/t.md\n@@ -0,0 +1 @@\n+t\n"
    await before("sandbox_apply_patch", "ses_p6", { patch })
    expect(logCount("bootstrap")).toBe(0)
    await probe()
  })

  test("bootstrap: a sandbox_write to a source file before the tracker warns, to the tracker does not", async () => {
    seedKey("ses_p7", ODD)
    await before("sandbox_write", "ses_p7", { path: "odd/tasks/t.md", content: "t" })
    expect(logCount("bootstrap")).toBe(0)
    seedKey("ses_p8", ODD)
    await before("sandbox_write", "ses_p8", { path: "src/x.ts", content: "x" })
    expect(logCount(`${ODD} bootstrap: write to src/x.ts before tracker stage artifact exists`)).toBe(1)
    await probe()
  })
})

describe("4. awaited writes", () => {
  test("loading an adapter skill mints its key before the hook returns", async () => {
    await after("skill", "ses_w1", { name: ODD }, "loaded")
    expect(hasFile("ses_w1", `${ODD}.key`)).toBe(true)
  })

  test("loading a Systematic skill writes its skill marker before the hook returns", async () => {
    await after("skill", "ses_w2", { name: "ce:plan" }, "loaded")
    expect(hasFile("ses_w2", "skill-ce-plan")).toBe(true)
  })

  test("a qualified skill name is canonicalised to the same marker", async () => {
    await after("skill", "ses_w2q", { name: "systematic:ce:plan" }, "loaded")
    expect(hasFile("ses_w2q", "skill-ce-plan")).toBe(true)
    expect(hasFile("ses_w2q", "skill-systematic-ce-plan")).toBe(false)
  })

  test("task completion links the child before the hook returns", async () => {
    await after("task", "ses_w3", { subagent_type: "general" }, 'task id="ses_w3child" done')
    expect(readFileSync(join(sessionDir("ses_w3child"), ".parent"), "utf8")).toBe("ses_w3")
    expect(JSON.parse(readFileSync(join(sessionDir("ses_w3child"), "inherited.key"), "utf8")).inherited_from).toBe("ses_w3")
  })

  test("task-result hook times out a hung write chain", async () => {
    const originalTimeout = process.env.SYSTEMATIC_ROUTING_GUARD_WRITE_TIMEOUT_MS
    process.env.SYSTEMATIC_ROUTING_GUARD_WRITE_TIMEOUT_MS = "20"
    setTaskWriteFileForTests(() => new Promise(() => {}))
    let watchdog: ReturnType<typeof setTimeout> | undefined
    try {
      await Promise.race([
        after("task", "ses_timeout", { subagent_type: "general" }, 'task id="ses_timeoutchild" done'),
        new Promise<never>((_resolve, reject) => {
          watchdog = setTimeout(() => reject(new Error("task-result hook hung past watchdog")), 2000)
        }),
      ])
      expect(hasFile("ses_timeoutchild", ".parent")).toBe(false)
      expect(hasFile("ses_timeoutchild", "inherited.key")).toBe(false)
    } finally {
      if (watchdog) clearTimeout(watchdog)
      setTaskWriteFileForTests(null)
      if (originalTimeout === undefined) delete process.env.SYSTEMATIC_ROUTING_GUARD_WRITE_TIMEOUT_MS
      else process.env.SYSTEMATIC_ROUTING_GUARD_WRITE_TIMEOUT_MS = originalTimeout
    }
  })
})

describe("5. key inheritance (up to three ancestors)", () => {
  test("own fresh key is valid, own 31-minute-old key is expired", async () => {
    seedKey("ses_k1", ODD, 0)
    await before("host_git_commit", "ses_k1", {})
    expect(logCount("ses_k1")).toBe(0)
    seedKey("ses_k2", ODD, 31)
    await before("host_git_commit", "ses_k2", {})
    expect(logCount("workflow key status: expired")).toBe(1)
    await probe()
  })

  test("logs valid key status once per session and status", async () => {
    seedKey("ses_k_valid_status", ODD)
    await before("host_git_commit", "ses_k_valid_status", {})
    await before("host_git_commit", "ses_k_valid_status", {})
    expect(warnSpy.mock.calls.filter((call: unknown[]) =>
      String(call[0]).includes("workflow key status=valid (session: ses_k_valid_status)"),
    )).toHaveLength(1)
    expect(logText()).toContain("workflow key status=valid (session: ses_k_valid_status)")
  })

  test("a grandchild inherits the root key through two hops", async () => {
    seedKey("ses_root", ODD)
    seedInherited("ses_kid", "ses_root")
    seedInherited("ses_grand", "ses_kid")
    await before("host_git_commit", "ses_grand", {})
    expect(logCount("ses_grand")).toBe(0)
    await probe()
  })

  test("three hops is the limit; a fourth ancestor is not consulted", async () => {
    seedKey("ses_a0", ODD)
    seedInherited("ses_a1", "ses_a0")
    seedInherited("ses_a2", "ses_a1")
    seedInherited("ses_a3", "ses_a2")
    seedInherited("ses_a4", "ses_a3")
    await before("host_git_commit", "ses_a3", {})
    expect(logCount("ses_a3")).toBe(0)
    await before("host_git_commit", "ses_a4", {})
    expect(logCount("workflow key status: missing")).toBe(1)
    await probe()
  })

  test("an expired root key makes the grandchild expired", async () => {
    seedKey("ses_old", ODD, 31)
    seedInherited("ses_old1", "ses_old")
    seedInherited("ses_old2", "ses_old1")
    await before("host_git_commit", "ses_old2", {})
    expect(logCount("workflow key status: expired")).toBe(1)
  })

  test("an inheritance cycle terminates as missing", async () => {
    seedInherited("ses_c1", "ses_c2")
    seedInherited("ses_c2", "ses_c1")
    await before("host_git_commit", "ses_c1", {})
    expect(logCount("workflow key status: missing")).toBe(1)
  })

  test("activity in a grandchild refreshes the root key", async () => {
    seedKey("ses_r0", ODD, 29)
    seedInherited("ses_r1", "ses_r0")
    seedInherited("ses_r2", "ses_r1")
    const beforeTs = JSON.parse(readFileSync(join(sessionDir("ses_r0"), `${ODD}.key`), "utf8")).last_active
    await before("host_git_commit", "ses_r2", {})
    const afterTs = JSON.parse(readFileSync(join(sessionDir("ses_r0"), `${ODD}.key`), "utf8")).last_active
    expect(afterTs).toBeGreaterThan(beforeTs + 60_000)
  })
})

describe("6. warning de-duplication", () => {
  test("repeated identical warnings reach the console once and the log every time", async () => {
    await before("host_git_commit", "ses_d1", {})
    await before("host_git_commit", "ses_d1", {})
    expect(consoleCount("ses_d1")).toBe(1)
    expect(logCount("ses_d1")).toBe(2)
  })

  test("specialist warnings are de-duplicated", async () => {
    seedKey("ses_d2", ODD)
    markAdvice("ses_d2")
    await dispatch("ses_d2", "general")
    await dispatch("ses_d2", "general")
    expect(consoleCount("specialist general")).toBe(1)
    expect(logCount("specialist general")).toBe(2)
  })

  test("skill-load gate warnings are de-duplicated", async () => {
    seedKey("ses_d3", SYS)
    await after("skill", "ses_d3", { name: "ce:work" }, "loaded")
    await after("skill", "ses_d3", { name: "ce:work" }, "loaded")
    expect(consoleCount("ce-work")).toBe(1)
    expect(logCount("ce-work")).toBe(2)
  })

  test("host_review_start warnings are de-duplicated", async () => {
    seedKey("ses_d4", SYS)
    await before("host_review_start", "ses_d4", {})
    await before("host_review_start", "ses_d4", {})
    expect(consoleCount("ses_d4")).toBe(1)
    expect(logCount("ses_d4")).toBe(2)
  })

  test("different failures for the same tool are not suppressed by each other", async () => {
    seedKey("ses_d5", ODD)
    markAdvice("ses_d5")
    await dispatch("ses_d5", "general")
    await dispatch("ses_d5", "mystery-writer")
    expect(consoleCount("specialist general")).toBe(1)
    expect(consoleCount("specialist mystery-writer")).toBe(1)
  })
})

// Q58/T6: the guard binds the most recently seen message agent per session and, for a PM
// session, requires the PM's own route-directory adapter key before host mutations and the
// review lifecycle. Warning-only: the binding is the latest observed message agent, not an
// authenticated session identity, and a missing key never blocks the call.
describe("8. PM own-route key binding", () => {
  const pmWarning = (pm: string, route: string, tool: string, status = "missing") =>
    `${pm} requires its own ${route} route key before ${tool} (PM session key status: ${status})`

  test("binds the latest message agent under the state root", async () => {
    await message("ses_pm_bind", "pm-odd")
    expect(hasFile("ses_pm_bind", ".agent")).toBe(true)
    expect(readFileSync(join(sessionDir("ses_pm_bind"), ".agent"), "utf8")).toContain("pm-odd")
  })

  test("a PM host mutation without its own key warns and still resolves", async () => {
    await message("ses_pm_commit", "pm-odd")
    await expect(before("host_git_commit", "ses_pm_commit", {})).resolves.toBeUndefined()
    expect(logText()).toContain(pmWarning("pm-odd", ODD, "host_git_commit"))
    expect(logCount("pm-odd requires its own")).toBe(1)
  })

  test("a PM review start without its own key warns and still resolves", async () => {
    await message("ses_pm_review_start", "pm-systematic")
    await expect(before("host_review_start", "ses_pm_review_start", {})).resolves.toBeUndefined()
    expect(logText()).toContain(pmWarning("pm-systematic", SYS, "host_review_start"))
    expect(logCount("pm-systematic requires its own")).toBe(1)
  })

  test("maps each PM to its own route adapter key", async () => {
    for (const [pm, route] of [
      ["pm-odd", ODD],
      ["pm-systematic", SYS],
      ["pm-sdd", "workflow-sdd-secure"],
    ]) {
      const sid = `ses_pm_map_${pm.replace(/-/g, "_")}`
      await message(sid, pm)
      await before("host_git_commit", sid, {})
      expect(logText()).toContain(pmWarning(pm, route, "host_git_commit"))
    }
    await probe()
  })

  test("own fresh route key means silence", async () => {
    await message("ses_pm_ok", "pm-odd")
    seedKey("ses_pm_ok", ODD)
    await before("host_git_commit", "ses_pm_ok", {})
    expect(logCount("ses_pm_ok")).toBe(0)
    expect(logCount("requires its own")).toBe(0)
    await probe()
  })

  test("a wrong-route own key cannot satisfy the PM requirement", async () => {
    await message("ses_pm_wrong", "pm-odd")
    seedKey("ses_pm_wrong", SYS)
    await before("host_git_commit", "ses_pm_wrong", {})
    expect(logCount(pmWarning("pm-odd", ODD, "host_git_commit"))).toBe(1)
  })

  test("an inherited route key cannot satisfy the PM requirement", async () => {
    seedKey("ses_pm_inh_parent", ODD)
    seedInherited("ses_pm_inh_child", "ses_pm_inh_parent")
    await message("ses_pm_inh_child", "pm-odd")
    await before("host_git_commit", "ses_pm_inh_child", {})
    expect(logCount(pmWarning("pm-odd", ODD, "host_git_commit"))).toBe(1)
  })

  test("an unrelated ancestor key cannot mask the missing own key", async () => {
    seedKey("ses_pm_anc_parent", SYS)
    seedInherited("ses_pm_anc_child", "ses_pm_anc_parent")
    await message("ses_pm_anc_child", "pm-odd")
    await before("host_git_commit", "ses_pm_anc_child", {})
    expect(logCount(pmWarning("pm-odd", ODD, "host_git_commit"))).toBe(1)
  })

  test("an expired own key warns as expired and is not revived by refresh", async () => {
    await message("ses_pm_expired", "pm-odd")
    seedKey("ses_pm_expired", ODD, 31)
    const keyPath = join(sessionDir("ses_pm_expired"), `${ODD}.key`)
    const beforeTs = JSON.parse(readFileSync(keyPath, "utf8")).last_active
    await before("host_git_commit", "ses_pm_expired", {})
    const afterTs = JSON.parse(readFileSync(keyPath, "utf8")).last_active
    expect(afterTs).toBe(beforeTs)
    expect(logCount(pmWarning("pm-odd", ODD, "host_git_commit", "expired"))).toBe(1)
  })

  test("a parent-linked PM mints its own key when it loads its adapter skill", async () => {
    seedInherited("ses_pm_mint", "ses_pm_mint_parent")
    await message("ses_pm_mint", "pm-odd")
    await after("skill", "ses_pm_mint", { name: ODD }, "loaded")
    expect(hasFile("ses_pm_mint", `${ODD}.key`)).toBe(true)
    await before("host_git_commit", "ses_pm_mint", {})
    expect(logCount("requires its own")).toBe(0)
    await probe()
  })

  test("a non-PM parent-linked session keeps inherited-key minting", async () => {
    seedInherited("ses_nonpm_mint", "ses_nonpm_mint_parent")
    await message("ses_nonpm_mint", "gentle-orchestrator")
    await after("skill", "ses_nonpm_mint", { name: ODD }, "loaded")
    expect(hasFile("ses_nonpm_mint", `${ODD}.key`)).toBe(false)
    expect(hasFile("ses_nonpm_mint", "inherited.key")).toBe(true)
  })

  test("a newer message agent replaces the previous binding", async () => {
    await message("ses_pm_latest", "pm-odd")
    await message("ses_pm_latest", "pm-systematic")
    await before("host_git_commit", "ses_pm_latest", {})
    expect(logCount(pmWarning("pm-systematic", SYS, "host_git_commit"))).toBe(1)
    expect(logCount("pm-odd requires")).toBe(0)
  })

  test("a non-PM message agent clears the PM requirement", async () => {
    await message("ses_pm_clear", "pm-odd")
    await message("ses_pm_clear", "gentle-orchestrator")
    await before("host_git_commit", "ses_pm_clear", {})
    expect(logCount("requires its own")).toBe(0)
    await probe()
  })

  test("tool.execute.before uses the persisted binding, not input.agent or output.agent", async () => {
    await message("ses_pm_input", "pm-odd")
    await hooks["tool.execute.before"](
      { tool: "host_git_commit", sessionID: "ses_pm_input", callID: "c1", agent: "pm-sdd" },
      { args: {}, agent: "pm-systematic" },
    )
    expect(logText()).toContain(pmWarning("pm-odd", ODD, "host_git_commit"))
    expect(logCount("pm-sdd requires")).toBe(0)
    expect(logCount("pm-systematic requires")).toBe(0)
  })

  test("every host_review_* lifecycle call requires the PM own key", async () => {
    const tools = [
      "host_review_start",
      "host_review_capture_result",
      "host_review_capture_refuter",
      "host_review_capture_validation",
      "host_review_capture_correction_plan",
      "host_review_capture_unachievable",
      "host_review_acknowledge_approved",
      "host_review_recover",
      "host_review_validate",
    ]
    await message("ses_pm_lifecycle", "pm-odd")
    for (const tool of tools) {
      await expect(before(tool, "ses_pm_lifecycle", {})).resolves.toBeUndefined()
      expect(logCount(pmWarning("pm-odd", ODD, tool))).toBe(1)
    }
  })

  test("every gated host mutation requires the PM own key", async () => {
    const tools = [
      "host_git_commit",
      "host_git_push",
      "host_gh_issue_create",
      "host_plan_append",
      "host_register_project",
      "host_sandbox_result_install",
      "host_sdd_archive_compose",
    ]
    await message("ses_pm_hosts", "pm-odd")
    for (const tool of tools) {
      await before(tool, "ses_pm_hosts", {})
      expect(logCount(pmWarning("pm-odd", ODD, tool))).toBe(1)
      expect(logText()).toContain(`workflow key status=missing (session: ses_pm_hosts)`)
    }
  })

  test("host mutation PM gates are derived from the routing gate set", async () => {
    const tools = ["host_sandbox_result_install", "host_sdd_archive_compose"]
    await message("ses_pm_derived_hosts", "pm-sdd")
    for (const tool of tools) {
      await before(tool, "ses_pm_derived_hosts", {})
      expect(logCount(pmWarning("pm-sdd", "workflow-sdd-secure", tool))).toBe(1)
      expect(logText()).toContain(`workflow key status=missing (session: ses_pm_derived_hosts)`)
    }
  })

  test("the PM rule does not gate sandbox writes or task dispatch", async () => {
    await message("ses_pm_scope", "pm-odd")
    await before("sandbox_write", "ses_pm_scope", { path: "src/x.ts", content: "x" })
    await dispatch("ses_pm_scope", "pm-odd")
    expect(logCount("requires its own")).toBe(0)
    await probe()
  })

  test("the binding persists for a new plugin factory in the same session", async () => {
    await message("ses_pm_resume", "pm-odd")
    hooks = await guard.default({} as any)
    await before("host_git_commit", "ses_pm_resume", {})
    expect(logCount(pmWarning("pm-odd", ODD, "host_git_commit"))).toBe(1)
  })

  test("an invalid session id cannot persist a binding or warn as a PM", async () => {
    await expect(message("ses_bad/id", "pm-odd")).resolves.toBeUndefined()
    await expect(before("host_git_commit", "ses_bad/id", {})).resolves.toBeUndefined()
    expect(logCount("requires its own")).toBe(0)
  })

  test("a message without an agent clears the previous PM binding", async () => {
    await message("ses_pm_no_agent", "pm-odd")
    await hooks["chat.message"]({ sessionID: "ses_pm_no_agent" })
    await before("host_git_commit", "ses_pm_no_agent", {})
    expect(logCount("requires its own")).toBe(0)
    await message("ses_pm_no_agent", "pm-odd")
    await before("host_git_commit", "ses_pm_no_agent", {})
    expect(logCount(pmWarning("pm-odd", ODD, "host_git_commit"))).toBe(1)
  })

  test("a malformed persisted binding is treated as no binding", async () => {
    await message("ses_pm_malformed", "pm-odd")
    mkdirSync(sessionDir("ses_pm_malformed"), { recursive: true })
    writeFileSync(join(sessionDir("ses_pm_malformed"), ".agent"), "{not-json", "utf8")
    await expect(before("host_git_commit", "ses_pm_malformed", {})).resolves.toBeUndefined()
    expect(logCount("requires its own")).toBe(0)
    await message("ses_pm_malformed", "pm-odd")
    await before("host_git_commit", "ses_pm_malformed", {})
    expect(logCount(pmWarning("pm-odd", ODD, "host_git_commit"))).toBe(1)
  })
})

// Q58/T6 correction: the adapter map must be an own-property-only identity lookup. A plain
// object literal inherits Object.prototype members, so `constructor`, `toString` and `__proto__`
// would otherwise resolve to inherited members and masquerade as PM route requirements.
describe("9. PM adapter map own-property lookup", () => {
  test("resolves each configured PM identity to its adapter skill", () => {
    expect(pmRequiredRouteSkill("pm-odd")).toBe("workflow-odd-secure")
    expect(pmRequiredRouteSkill("pm-systematic")).toBe("workflow-systematic")
    expect(pmRequiredRouteSkill("pm-sdd")).toBe("workflow-sdd-secure")
  })

  test("constructor is not a PM identity", () => {
    expect(pmRequiredRouteSkill("constructor")).toBeNull()
  })

  test("toString is not a PM identity", () => {
    expect(pmRequiredRouteSkill("toString")).toBeNull()
  })

  test("__proto__ is not a PM identity", () => {
    expect(pmRequiredRouteSkill("__proto__")).toBeNull()
  })

  test("an unknown pm- name is not a PM identity", () => {
    expect(pmRequiredRouteSkill("pm-unknown")).toBeNull()
  })

  test("a prototype-member message agent does not trip the PM warning", async () => {
    await message("ses_pm_proto_name", "constructor")
    await before("host_git_commit", "ses_pm_proto_name", {})
    expect(logCount("requires its own")).toBe(0)
    // Positive control: the same run still warns for a configured PM, so the zero above is a
    // real absence, not a broken log.
    await message("ses_pm_proto_ctl", "pm-odd")
    await before("host_git_commit", "ses_pm_proto_ctl", {})
    expect(logCount(`pm-odd requires its own ${ODD} route key before host_git_commit`)).toBe(1)
  })
})
