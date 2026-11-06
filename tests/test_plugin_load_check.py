"""verify-workflow.sh plugin load check: V1 shapes keep passing, the V1+V2 dual shape is accepted,
and malformed shapes still fail (OpenCode V2 prep; shapes proven by the B1 probe on V2 2.2.0)."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOKS = '{ "experimental.chat.system.transform": async () => {} }'


def run_check(source, mode="factory", name="workflow-health-check.ts"):
    d = Path(tempfile.mkdtemp())
    try:
        (d / name).write_text(source, encoding="utf-8")
        env = {**os.environ, "WORKFLOW_VERIFY_PLUGIN_LOADS_ONLY": "1", "WORKFLOW_VERIFY_PLUGIN_LOAD_MODE": mode,
               "WORKFLOW_VERIFY_PLUGIN_LOAD_DIR": str(d)}
        out = subprocess.run(["bash", str(REPO / "verify-workflow.sh")], env=env, cwd=str(REPO), stdin=subprocess.DEVNULL,
                             capture_output=True, text=True, timeout=120)
        return out.stdout + out.stderr
    finally:
        shutil.rmtree(d, ignore_errors=True)


def passed(output):
    return "OK plugin" in output and "plugin load check failed" not in output


@unittest.skipUnless(shutil.which("bun"), "bun is required to execute plugins")
class LoadCheckShapes(unittest.TestCase):
    def test_v1_default_function_still_passes(self):
        self.assertTrue(passed(run_check(f"export default async () => ({HOOKS})")))

    def test_v1_named_factory_still_passes(self):
        self.assertTrue(passed(run_check(f"export const SamplePlugin = async () => ({HOOKS})")))

    def test_dual_object_passes_and_reports_the_v1_hooks(self):
        out = run_check(f'export default {{ id: "x", async setup() {{}}, async server() {{ return {HOOKS} }} }}')
        self.assertTrue(passed(out), out)
        self.assertIn("recognized hooks: experimental.chat.system.transform", out)

    def test_dual_object_passes_in_import_mode(self):
        self.assertTrue(passed(run_check('export default { id: "x", setup() {}, server: async () => ({}) }', mode="import")))

    def test_object_without_id_fails(self):
        out = run_check(f"export default {{ async setup() {{}}, async server() {{ return {HOOKS} }} }}")
        self.assertFalse(passed(out))
        self.assertIn("needs a string id", out)

    def test_object_with_id_but_no_entry_points_fails(self):
        out = run_check('export default { id: "x" }')
        self.assertFalse(passed(out))
        self.assertIn("both setup and server", out)

    def test_v2_only_object_fails_because_v1_would_break(self):
        out = run_check('export default { id: "x", async setup() {} }')
        self.assertFalse(passed(out))
        self.assertIn("both setup and server", out)

    def test_dual_object_whose_server_has_no_recognized_hooks_fails(self):
        out = run_check('export default { id: "x", async setup() {}, async server() { return {} } }')
        self.assertFalse(passed(out))
        self.assertIn("factory returned no recognized hooks: default.server", out)

    def test_extra_function_export_next_to_a_dual_default_fails(self):
        out = run_check(f'export default {{ id: "x", async setup() {{}}, async server() {{ return {HOOKS} }} }}\nexport function helper() {{}}')
        self.assertFalse(passed(out))
        self.assertIn("unexpected function-valued plugin exports", out)

    def test_dual_default_plus_a_named_factory_fails_because_v1_would_load_both(self):
        out = run_check(f'export default {{ id: "x", async setup() {{}}, async server() {{ return {HOOKS} }} }}\nexport const SamplePlugin = async () => ({HOOKS})')
        self.assertFalse(passed(out))
        self.assertIn("must not be combined with named Plugin factory exports", out)

    def test_untracked_plugin_with_a_bad_shape_is_report_only(self):
        out = run_check('export default { id: "x" }', name="someone-elses-plugin.ts")
        self.assertIn("PLUGIN_LOAD_REPORT_ONLY", out)


if __name__ == "__main__":
    unittest.main()
