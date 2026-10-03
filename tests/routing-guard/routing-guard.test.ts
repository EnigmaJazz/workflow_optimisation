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
    const roots = [root, mkdtempSync(join(tmpdir(), "guard-log-failure-"))]
    for (const failureRoot of roots) {
      mkdirSync(join(failureRoot, ".local/share/opencode"), { recursive: true })
      rmSync(join(failureRoot, ".local/share/opencode/logs"), { recursive: true, force: true })
      writeFileSync(join(failureRoot, ".local/share/opencode/logs"), "not a directory")
      root = failureRoot
      process.env.SYSTEMATIC_ROUTING_GUARD_STATE_ROOT = failureRoot
      await before("host_git_commit", `ses_log_failure_${roots.indexOf(failureRoot)}`, {})
      await before("host_git_commit", `ses_log_failure_${roots.indexOf(failureRoot)}`, {})
    }

    expect(consoleCount("file log append failed")).toBe(2)
    for (const failureRoot of roots) rmSync(failureRoot, { recursive: true, force: true })
  })

  test("a failed append cannot reject the logging hook", async () => {
    const logs = join(root, ".local/share/opencode/logs")
    rmSync(logs, { recursive: true, force: true })
    mkdirSync(join(root, ".local/share/opencode"), { recursive: true })
    writeFileSync(logs, "not a directory")

    await expect(before("host_git_commit", "ses_log_rejection", {})).resolves.toBeUndefined()
  })
})

describe("7. exported stage table", () => {
  test("ROUTE_STAGES is exported and well formed", () => {
    const stages = guard.ROUTE_STAGES as Record<string, Array<Record<string, unknown>>>
    expect(Object.keys(stages).sort()).toEqual([ODD, SYS])
    for (const [route, list] of Object.entries(stages)) {
      const ids = list.map((s) => s.id)
      expect(new Set(ids).size).toBe(ids.length)
      for (const s of list) {
        expect(s.artifactPattern !== undefined || (Array.isArray(s.skillMarkers) && s.skillMarkers.length > 0)).toBe(true)
      }
      expect(route.startsWith("workflow-")).toBe(true)
    }
    expect(stages[ODD].map((s) => s.id)).toEqual(["tracker"])
    expect(stages[SYS].map((s) => s.id)).toEqual(["requirements", "plan", "review"])
  })

  test("READ_ONLY_SPECIALIST_PATTERNS is exported", () => {
    expect(Array.isArray(guard.READ_ONLY_SPECIALIST_PATTERNS)).toBe(true)
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

  test("listed writer after the tracker exists does not warn", async () => {
    seedKey("ses_s4", ODD)
    marker("ses_s4", `artifact-${ODD}-tracker`)
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
      "asi-review-risk", "asi-review-validator", "advisor-design", "jd-judge-a", "jd-judge-b"]) {
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

describe("2. route-namespaced stage markers", () => {
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
    const sys = guard.stageMarkerNames("workflow-systematic", "plan", table)
    expect(sys).toContain("artifact-workflow-systematic-plan")
    expect(sys).not.toContain("artifact-plan")
    expect(sys).not.toContain("artifact-odd-plan")
    const odd = guard.stageMarkerNames("workflow-odd-secure", "tracker", table)
    expect(odd).toEqual(expect.arrayContaining(["artifact-workflow-odd-secure-tracker", "artifact-tracker", "artifact-odd-tracker"]))
    const review = guard.stageMarkerNames("workflow-systematic", "review", table)
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
    guard.setTaskWriteFileForTests(() => new Promise(() => {}))
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
      guard.setTaskWriteFileForTests(null)
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
    await dispatch("ses_d5", "general")
    await dispatch("ses_d5", "mystery-writer")
    expect(consoleCount("specialist general")).toBe(1)
    expect(consoleCount("specialist mystery-writer")).toBe(1)
  })
})
