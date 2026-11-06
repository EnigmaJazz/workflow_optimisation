// The user-owned plugin lives outside this repository (~/.config/opencode/plugins). These tests load that file, so a
// missing or broken deployment fails them instead of passing vacuously.
import { describe, expect, test } from "bun:test"
import { homedir } from "node:os"
import { join } from "node:path"

const PLUGINS = join(homedir(), ".config", "opencode", "plugins")
const plugin = await import(join(PLUGINS, "use-grep-tool.ts"))
const { checkBashCommand, SYSTEM_RULE } = await import(join(PLUGINS, "lib", "use-grep-check.ts"))

const BLOCKED = [
  "rg foo src",
  "grep -rn foo .",
  "grep foo src/a.ts",
  "git grep needle",
  "find . -name '*.ts'",
  "find . -exec grep foo {} +",
  "ag foo",
]
const ALLOWED = ["ps aux | grep node", "go test ./... | grep fail", "grep foo", "git log --grep fix", "ls -la", "cat a.ts | rg x"]

describe("checkBashCommand", () => {
  for (const command of BLOCKED) {
    test(`blocks: ${command}`, () => expect(checkBashCommand(command).blocked).toBe(true))
  }
  for (const command of ALLOWED) {
    test(`allows: ${command}`, () => expect(checkBashCommand(command).blocked).toBe(false))
  }
  test("a non-string or empty command is not blocked", () => {
    expect(checkBashCommand("").blocked).toBe(false)
    expect(checkBashCommand(undefined as unknown as string).blocked).toBe(false)
  })
})

describe("entry point", () => {
  test("the default export is dual-mode and is the only value export", () => {
    const dflt = plugin.default as { id: string; setup: unknown; server: unknown }
    expect(dflt.id).toBe("use-grep-tool")
    expect(typeof dflt.setup).toBe("function")
    expect(typeof dflt.server).toBe("function")
    expect(Object.keys(plugin)).toEqual(["default"])
  })
})

describe("V1 server hooks", () => {
  async function hooks() {
    return (await (plugin.default as { server: () => Promise<Record<string, Function>> }).server())
  }
  test("blocks a bash code search with the instructive error", async () => {
    const h = await hooks()
    await expect(h["tool.execute.before"]!({ tool: "bash" }, { args: { command: "rg foo" } })).rejects.toThrow(/BLOCKED by use-grep-tool plugin/)
  })
  test("lets a filter, another tool and a missing command through", async () => {
    const h = await hooks()
    await h["tool.execute.before"]!({ tool: "bash" }, { args: { command: "ps aux | grep node" } })
    await h["tool.execute.before"]!({ tool: "read" }, { args: { command: "rg foo" } })
    await h["tool.execute.before"]!({ tool: "bash" }, { args: {} })
  })
  test("adds the rule to the system prompt", async () => {
    const h = await hooks()
    const output = { system: [] as string[] }
    await h["experimental.chat.system.transform"]!({}, output)
    expect(output.system).toEqual([SYSTEM_RULE])
  })
})

describe("V2 setup hooks", () => {
  async function setup() {
    const handlers: Record<string, Function> = {}
    const ctx = {
      tool: { hook: async (name: string, fn: Function) => void (handlers[`tool.${name}`] = fn) },
      session: { hook: async (name: string, fn: Function) => void (handlers[`session.${name}`] = fn) },
    }
    await (plugin.default as { setup: (c: unknown) => Promise<void> }).setup(ctx)
    return handlers
  }
  test("registers the two hooks", async () => {
    expect(Object.keys(await setup()).sort()).toEqual(["session.context", "tool.execute.before"])
  })
  test("blocks a shell code search (V2 tool id is shell, input key command)", async () => {
    const h = await setup()
    expect(() => h["tool.execute.before"]!({ tool: "shell", input: { command: "rg foo src" } })).toThrow(/BLOCKED by use-grep-tool plugin/)
  })
  test("lets a filter, another tool and a missing command through", async () => {
    const h = await setup()
    h["tool.execute.before"]!({ tool: "shell", input: { command: "ps aux | grep node" } })
    h["tool.execute.before"]!({ tool: "read", input: { command: "rg foo" } })
    h["tool.execute.before"]!({ tool: "shell", input: {} })
    h["tool.execute.before"]!({ tool: "shell" })
  })
  test("adds the rule as a text entry of the session context", async () => {
    const h = await setup()
    const event = { system: [] as unknown[] }
    h["session.context"]!(event)
    expect(event.system).toEqual([{ type: "text", text: SYSTEM_RULE }])
  })
})
