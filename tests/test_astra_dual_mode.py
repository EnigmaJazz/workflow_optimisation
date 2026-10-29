"""astra-sol-upgrade is dual-mode: V1 config hook via server(), V2 agent.transform via setup().
The V2 shapes (Agent.Info, ordered permissions, model {id, providerID, variant}) come from the
B1 probe on OpenCode V2 2.2.0."""
import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "global-config" / "plugins" / "astra-sol-upgrade.ts"
SOL = {"providerID": "openai", "id": "gpt-6.1-sol"}

RUNNER = """
const mod = await import(%s)
const plugin = mod.default
const agents = JSON.parse(process.argv[1])
const out = { id: plugin.id, setup: typeof plugin.setup, server: typeof plugin.server,
  named: Object.entries(mod).filter(([k, v]) => typeof v === "function").map(([k]) => k) }
const store = new Map(agents.map((a) => [a.id, a]))
const editor = {
  list: () => [...store.values()],
  get: (id) => store.get(id),
  update: (id, fn) => { if (!store.has(id)) store.set(id, { id, permissions: [] }); fn(store.get(id)) },
}
let disposed = 0
let transform
const ctx = { agent: { transform: async (cb) => { transform = cb; return { dispose: async () => { disposed++ } } } } }
const cleanup = await plugin.setup(ctx)
try { transform(editor); out.error = null } catch (e) { out.error = String(e.message || e) }
await cleanup()
out.disposed = disposed
const al = store.get("planner-astra"), src = store.get("planner")
if (al && src) { al.permissions.push("mutated"); out.sourceMutated = src.permissions.includes("mutated") }
out.agents = Object.fromEntries(store)
console.log(JSON.stringify(out))
""" % json.dumps(str(PLUGIN))


def agent(id, mode="subagent", model=None, permissions=None):
    a = {"id": id, "name": id.title(), "mode": mode, "hidden": False, "description": f"{id} agent",
         "request": {"settings": {}, "headers": {}, "body": {}}, "permissions": permissions or [{"action": "*", "resource": "*", "effect": "allow"}]}
    if model:
        a["model"] = model
    return a


def run(agents):
    out = subprocess.run(["bun", "-e", RUNNER, json.dumps(agents)], cwd=str(REPO), capture_output=True, text=True,
                         stdin=subprocess.DEVNULL, timeout=60, env={**os.environ, "WORKFLOW_HEALTH_CHECK_PROBE": "1"})
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


def orchestrator(extra=None):
    return agent("gentle-orchestrator", "primary", {"providerID": "x", "id": "y"},
                 [{"action": "subagent", "resource": "*", "effect": "deny"}] + (extra or []))


@unittest.skipUnless(shutil.which("bun"), "bun is required to execute the plugin")
class AstraDualMode(unittest.TestCase):
    def test_shape_is_a_plain_dual_object_with_no_other_function_exports(self):
        r = run([orchestrator()])
        self.assertEqual((r["id"], r["setup"], r["server"], r["named"]), ("astra-sol-upgrade", "function", "function", []))

    def test_v2_adds_an_alias_for_an_eligible_sol_subagent(self):
        r = run([orchestrator(), agent("planner", model=SOL)])
        alias = r["agents"]["planner-astra"]
        self.assertTrue(alias["hidden"])
        self.assertEqual(alias["mode"], "subagent")
        self.assertEqual(alias["model"], {"providerID": "openai", "id": "gpt-6-astra", "variant": "xhigh"})
        self.assertEqual(alias["permissions"], r["agents"]["planner"]["permissions"])
        self.assertIn("selectable Astra upgrade", alias["description"])
        self.assertEqual(r["agents"]["planner"]["model"], SOL)

    def test_v2_orchestrator_may_dispatch_the_alias_and_the_allow_comes_last(self):
        r = run([orchestrator(), agent("planner", model=SOL)])
        rules = r["agents"]["gentle-orchestrator"]["permissions"]
        self.assertEqual(rules[-1], {"action": "subagent", "resource": "planner-astra", "effect": "allow"})
        self.assertEqual(rules[0], {"action": "subagent", "resource": "*", "effect": "deny"})

    def test_v2_skips_primary_implementation_review_and_non_sol_agents(self):
        agents = [orchestrator(), agent("planner", model=SOL), agent("boss", "primary", SOL),
                  agent("systematic-implementer", model=SOL), agent("jd-fix-agent", model=SOL),
                  agent("asi-review-risk", model=SOL), agent("review-refuter", model=SOL),
                  agent("cheap", model={"providerID": "openai", "id": "gpt-5-mini"}), agent("nomodel")]
        r = run(agents)
        self.assertEqual(sorted(k for k in r["agents"] if k.endswith("-astra")), ["planner-astra"])

    def test_v2_refuses_to_overwrite_an_existing_alias(self):
        r = run([orchestrator(), agent("planner", model=SOL), agent("planner-astra", model=SOL)])
        self.assertIn("refusing to overwrite agent planner-astra", r["error"])

    def test_v2_missing_orchestrator_is_an_error(self):
        r = run([agent("planner", model=SOL)])
        self.assertIn("gentle-orchestrator is missing", r["error"])

    def test_cleanup_disposes_the_transform_registration(self):
        self.assertEqual(run([orchestrator()])["disposed"], 1)

    def test_alias_does_not_alias_the_source_objects(self):
        r = run([orchestrator(), agent("planner", model=SOL)])
        self.assertIn("sourceMutated", r)
        self.assertFalse(r["sourceMutated"])


if __name__ == "__main__":
    unittest.main()
