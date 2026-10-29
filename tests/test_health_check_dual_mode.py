"""workflow-health-check.ts is dual-mode (V1 server + V2 setup) with identical notice text.
The B1 probe (OpenCode V2 2.2.0) showed V2 loads only a plain-object default export."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "global-config" / "plugins" / "workflow-health-check.ts"

RUNNER = """
const mod = await import(%s)
const plugin = mod.default
const out = { id: plugin.id, hasSetup: typeof plugin.setup, hasServer: typeof plugin.server,
  namedFunctionExports: Object.entries(mod).filter(([k, v]) => typeof v === "function").map(([k]) => k) }
const v1 = await plugin.server({})
const output = { system: ["base"] }
await v1["experimental.chat.system.transform"]({}, output)
out.v1System = output.system
const hooks = {}
let disposed = 0
const ctx = { session: { hook: async (name, cb) => { hooks[name] = cb; return { dispose: async () => { disposed++ } } } } }
const cleanup = await plugin.setup(ctx)
const v2 = { system: [{ type: "text", text: "base" }] }
hooks.context(v2)
out.v2System = v2.system
out.registered = Object.keys(hooks)
await cleanup()
out.disposed = disposed
console.log(JSON.stringify(out))
""" % json.dumps(str(PLUGIN))


def run(health=None):
    import os
    env = {**os.environ, "WORKFLOW_HEALTH_CHECK_PROBE": "1"}
    if health is not None:
        env["WORKFLOW_HEALTH_CHECK_TEST_HEALTH"] = json.dumps(health)
    out = subprocess.run(["bun", "-e", RUNNER], env=env, cwd=str(REPO), capture_output=True, text=True,
                         stdin=subprocess.DEVNULL, timeout=60)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


@unittest.skipUnless(shutil.which("bun"), "bun is required to execute the plugin")
class HealthCheckDualMode(unittest.TestCase):
    def test_shape_is_a_plain_dual_object_with_no_other_function_exports(self):
        r = run()
        self.assertEqual((r["id"], r["hasSetup"], r["hasServer"]), ("workflow-health-check", "function", "function"))
        self.assertEqual(r["namedFunctionExports"], [])

    def test_clean_state_injects_nothing_on_either_host(self):
        r = run({"state": "clean", "tail": ""})
        self.assertEqual(r["v1System"], ["base"])
        self.assertEqual(r["v2System"], [{"type": "text", "text": "base"}])

    def test_no_state_injects_nothing(self):
        r = run()
        self.assertEqual(r["v1System"], ["base"])

    def test_failed_notice_is_identical_text_on_both_hosts(self):
        r = run({"state": "failed", "tail": "boom line"})
        self.assertEqual(len(r["v1System"]), 2)
        notice = r["v1System"][1]
        self.assertIn("## Workflow health check FAILED", notice)
        self.assertIn("boom line", notice)
        self.assertIn("verify-workflow.sh", notice)
        self.assertEqual(r["v2System"][1], {"type": "text", "text": notice})

    def test_repaired_notice_is_identical_text_on_both_hosts(self):
        r = run({"state": "repaired", "tail": "fixed it"})
        notice = r["v1System"][1]
        self.assertIn("## Workflow health check SELF-REPAIRED", notice)
        self.assertIn("recommend restarting OpenCode", notice)
        self.assertEqual(r["v2System"][1], {"type": "text", "text": notice})

    def test_setup_registers_the_context_hook_and_cleanup_disposes_it(self):
        r = run({"state": "clean", "tail": ""})
        self.assertEqual(r["registered"], ["context"])
        self.assertEqual(r["disposed"], 1)

    def test_probe_guard_text_is_still_present_for_the_verifier(self):
        self.assertIn("WORKFLOW_HEALTH_CHECK_PROBE", PLUGIN.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
