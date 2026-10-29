"""astra-sol-upgrade is dual-mode: V1 config hook via server(), V2 aliases via setup().

V2 facts (B1 probe, OpenCode 2.2.0): a plugin's agent.transform editor only holds built-in agents;
config-defined agents are layered afterwards, so the full list comes from ctx.agent.list()
({location, data}); editor.update() on a new id creates an agent; ctx.agent.reload() re-runs the
transform; a plugin cannot amend a config-defined agent's permissions."""
import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "global-config" / "plugins" / "astra-sol-upgrade.ts"
SOL = {"providerID": "openai", "id": "gpt-6.1-sol"}
ASTRA = {"providerID": "openai", "id": "gpt-6-astra", "variant": "xhigh"}

RUNNER = """
const mod = await import(%s)
const plugin = mod.default
const config = JSON.parse(process.argv[1])           // agents defined in config (visible via the API only)
const out = { id: plugin.id, setup: typeof plugin.setup, server: typeof plugin.server,
  named: Object.entries(mod).filter(([k, v]) => typeof v === "function").map(([k]) => k), errors: [] }
const origError = console.error
console.error = (...a) => out.errors.push(a.join(" "))
const builtin = [{ id: "build", permissions: [] }]
const created = new Map()
let transformCb, reloads = 0, disposed = 0, closed = 0
const editor = {
  list: () => [...builtin, ...created.values()],
  get: (id) => created.get(id) ?? builtin.find((a) => a.id === id),
  update: (id, fn) => { if (!created.has(id)) created.set(id, { id, permissions: [] }); fn(created.get(id)) },
}
const all = () => [...builtin, ...config.filter((c) => !created.has(c.id)), ...created.values()]
// events: the host emits agent.updated at startup and after every reload
const queue = []
let wake
const emit = () => { queue.push({ type: "agent.updated" }); wake?.() }
const ctx = { agent: {
  transform: async (cb) => { transformCb = cb; return { dispose: async () => { disposed++ } } },
  list: async () => ({ location: {}, data: JSON.parse(JSON.stringify(all())) }),
  reload: async () => { reloads++; transformCb(editor); emit() },
}, event: { subscribe: () => ({ [Symbol.asyncIterator]() { return {
  next: () => new Promise((resolve) => { const go = () => { if (stopped) return resolve({ done: true }); if (queue.length) return resolve({ value: queue.shift(), done: false }); wake = go } ; go() }),
  return: async () => { closed++; stopped = true; wake?.(); return { done: true } },
} } }) } }
let stopped = false
const cleanup = await plugin.setup(ctx)
emit()
await new Promise((r) => setTimeout(r, 150))
await cleanup()
out.reloads = reloads; out.disposed = disposed; out.closed = closed
out.created = JSON.parse(JSON.stringify(Object.fromEntries(created)))
const al = created.get("planner-astra"), src = config.find((c) => c.id === "planner")
if (al && src) { al.permissions.push("mutated"); out.sourceMutated = src.permissions.includes("mutated") }
console.error = origError
console.log(JSON.stringify(out))
""" % json.dumps(str(PLUGIN))


def agent(id, mode="subagent", model=None, permissions=None):
    a = {"id": id, "name": id.title(), "mode": mode, "hidden": False, "description": f"{id} agent",
         "request": {"settings": {}, "headers": {}, "body": {}}, "permissions": permissions or [{"action": "*", "resource": "*", "effect": "allow"}]}
    if model:
        a["model"] = model
    return a


def run(config_agents):
    out = subprocess.run(["bun", "-e", RUNNER, json.dumps(config_agents)], cwd=str(REPO), capture_output=True, text=True,
                         stdin=subprocess.DEVNULL, timeout=60, env={**os.environ, "WORKFLOW_HEALTH_CHECK_PROBE": "1"})
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


def orchestrator():
    return agent("gentle-orchestrator", "primary", {"providerID": "x", "id": "y"},
                 [{"action": "subagent", "resource": "*", "effect": "deny"}])


@unittest.skipUnless(shutil.which("bun"), "bun is required to execute the plugin")
class AstraDualMode(unittest.TestCase):
    def test_shape_is_a_plain_dual_object_with_no_other_function_exports(self):
        r = run([orchestrator()])
        self.assertEqual((r["id"], r["setup"], r["server"], r["named"]), ("astra-sol-upgrade", "function", "function", []))

    def test_v2_creates_an_alias_for_an_eligible_config_defined_sol_subagent(self):
        r = run([orchestrator(), agent("planner", model=SOL)])
        alias = r["created"]["planner-astra"]
        self.assertTrue(alias["hidden"])
        self.assertEqual(alias["mode"], "subagent")
        self.assertEqual(alias["model"], ASTRA)
        self.assertEqual(alias["permissions"], agent("planner")["permissions"])
        self.assertIn("selectable Astra upgrade", alias["description"])
        self.assertEqual(r["errors"], [])

    def test_v2_skips_primary_implementation_review_and_non_sol_agents(self):
        agents = [orchestrator(), agent("planner", model=SOL), agent("boss", "primary", SOL),
                  agent("systematic-implementer", model=SOL), agent("jd-fix-agent", model=SOL),
                  agent("asi-review-risk", model=SOL), agent("review-refuter", model=SOL),
                  agent("cheap", model={"providerID": "openai", "id": "gpt-5-mini"}), agent("nomodel")]
        r = run(agents)
        self.assertEqual(sorted(r["created"]), ["planner-astra"])

    def test_v2_is_idempotent_one_reload_even_though_the_alias_triggers_another_event(self):
        r = run([orchestrator(), agent("planner", model=SOL)])
        self.assertEqual(r["reloads"], 1)

    def test_v2_never_touches_the_orchestrator(self):
        r = run([orchestrator(), agent("planner", model=SOL)])
        self.assertNotIn("gentle-orchestrator", r["created"])

    def test_v2_no_eligible_agents_means_no_reload(self):
        r = run([orchestrator(), agent("cheap", model={"providerID": "openai", "id": "gpt-5-mini"})])
        self.assertEqual((r["reloads"], r["created"]), (0, {}))

    def test_v2_foreign_alias_is_not_overwritten_and_is_reported(self):
        r = run([orchestrator(), agent("planner", model=SOL), agent("planner-astra", model={"providerID": "x", "id": "y"})])
        self.assertEqual(r["created"], {})
        self.assertTrue(any("refusing to overwrite agent planner-astra" in e for e in r["errors"]), r["errors"])

    def test_v2_missing_orchestrator_is_reported_and_creates_nothing(self):
        r = run([agent("planner", model=SOL)])
        self.assertEqual(r["created"], {})
        self.assertTrue(any("gentle-orchestrator is missing" in e for e in r["errors"]), r["errors"])

    def test_cleanup_disposes_the_registration_and_closes_the_event_stream(self):
        r = run([orchestrator()])
        self.assertEqual((r["disposed"], r["closed"]), (1, 1))

    def test_alias_does_not_alias_the_source_objects(self):
        r = run([orchestrator(), agent("planner", model=SOL)])
        self.assertIn("sourceMutated", r)
        self.assertFalse(r["sourceMutated"])


if __name__ == "__main__":
    unittest.main()
