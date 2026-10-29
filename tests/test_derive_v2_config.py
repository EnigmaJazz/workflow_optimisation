"""scripts/derive-v2-config.py: derive the V2 config root from global-config/ (queue Q46, item "V2 config source").

The V1 config stays the single source of truth. The V2 root differs only where V2 requires it: the plugin list (V2 key
`plugins`; `~x.y.z` patch ranges for registry packages; the rate-limit fork as a DIRECTORY entry because V2 does not load
a single-file path; the auto-update fork and V1-only packages dropped) and the files V2 does not use are left out.
Permissions are NOT rewritten (the V1 policy denies the sandbox and host tools globally and grants them per agent; the
V2 fragment would weaken that), but the V2 rule "a tool with no rule is silently allowed" is enforced as a check.
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "derive-v2-config.py"
SANDBOX = Path.home() / "agent-sandbox-integration"


def load():
    spec = importlib.util.spec_from_file_location("derive_v2", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["derive_v2"] = mod
    spec.loader.exec_module(mod)
    return mod


FORK_FILE = "file:///home/james/.config/opencode/plugins/opencode-rate-limit-fallback-mapped/index.ts"
AUTO = "file:///home/james/.local/share/opencode-plugin-auto-update-local/dist/index.js"


class PluginList(unittest.TestCase):
    def setUp(self):
        self.m = load()
        self.fork = Path(tempfile.mkdtemp()) / "opencode-rate-limit-fallback-mapped"
        self.fork.mkdir()
        (self.fork / "package.json").write_text(json.dumps({"name": "x", "exports": "./index.ts"}))

    def derive(self, plugins):
        return self.m.derive_plugins(plugins, fork_dir=self.fork)

    def test_registry_pins_become_patch_ranges(self):
        out, _ = self.derive(["@fro.bot/systematic@3.27.2", "@cortexkit/aft-opencode@0.62.0", "plain-pkg@1.2.3"])
        self.assertEqual(out, ["@fro.bot/systematic@~3.27.2", "@cortexkit/aft-opencode@~0.62.0", "plain-pkg@~1.2.3"])

    def test_the_fork_becomes_a_directory_entry(self):
        out, _ = self.derive([FORK_FILE])
        self.assertEqual(out, [f"file://{self.fork}"])

    def test_the_fork_directory_must_declare_exports(self):
        (self.fork / "package.json").write_text(json.dumps({"name": "x", "main": "index.ts"}))
        with self.assertRaisesRegex(self.m.DeriveError, "exports"):
            self.derive([FORK_FILE])

    def test_auto_update_and_v1_only_packages_are_dropped_and_reported(self):
        out, notes = self.derive([AUTO, "opencode-usage-total@0.3.0", "@fro.bot/systematic@3.27.2"])
        self.assertEqual(out, ["@fro.bot/systematic@~3.27.2"])
        self.assertEqual(len(notes), 2)

    def test_an_unknown_local_path_or_unversioned_spec_needs_a_decision(self):
        for spec in ("file:///somewhere/else.js", "unpinned-package", "pkg@^1.0.0", "pkg@latest"):
            with self.assertRaises(self.m.DeriveError, msg=spec):
                self.derive([spec])

    def test_order_is_preserved(self):
        out, _ = self.derive(["b@1.0.0", "a@2.0.0"])
        self.assertEqual(out, ["b@~1.0.0", "a@~2.0.0"])


class Checks(unittest.TestCase):
    def setUp(self):
        self.m = load()
        self.sandbox = Path(tempfile.mkdtemp())
        lib = self.sandbox / "opencode/plugins/lib"
        lib.mkdir(parents=True)
        (lib / "tool-specs-x.ts").write_text(
            "export const x = {\n  tool_plain: defineTool({\n    execute: async () => 'x',\n  }),\n"
            "  tool_asks: defineTool({\n    execute: async (a, ctx) => { await ctx.ask({}); },\n  }),\n};\n"
        )

    def test_scan_finds_tools_and_which_ask(self):
        self.assertEqual(self.m.scan_tools(self.sandbox), {"tool_plain": False, "tool_asks": True})

    def test_every_tool_needs_an_explicit_rule(self):
        with self.assertRaisesRegex(self.m.DeriveError, "tool_asks"):
            self.m.check_rules({"permission": {"tool_plain": "deny"}, "agent": {}}, {"tool_plain": False, "tool_asks": True})

    def test_an_agent_override_that_allows_an_approval_tool_is_reported_not_fatal(self):
        config = {"permission": {"tool_plain": "deny", "tool_asks": "deny"}, "agent": {"worker": {"permission": {"tool_asks": "allow"}}}}
        warnings = self.m.check_rules(config, {"tool_plain": False, "tool_asks": True})
        self.assertEqual(len(warnings), 1)
        self.assertIn("worker", warnings[0])
        self.assertIn("tool_asks", warnings[0])

    def test_ask_or_deny_for_approval_tools_gives_no_warning(self):
        config = {"permission": {"tool_plain": "deny", "tool_asks": "deny"}, "agent": {"a": {"permission": {"tool_asks": "ask"}}}}
        self.assertEqual(self.m.check_rules(config, {"tool_plain": False, "tool_asks": True}), [])

    def test_v1_root_paths_in_mcp_commands_are_reported(self):
        config = {"mcp": {"vision": {"type": "local", "command": ["python3", str(Path.home() / ".config/opencode/mcp/v/server.py")]}}}
        self.assertEqual(len(self.m.check_v1_paths(config)), 1)
        self.assertEqual(self.m.check_v1_paths({"mcp": {"ok": {"type": "remote", "url": "https://x"}}}), [])


@unittest.skipUnless(SANDBOX.exists(), "needs the agent-sandbox-integration checkout for the tool table")
class RealConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = Path(tempfile.mkdtemp()) / "root"
        cls.run1 = subprocess.run([sys.executable, str(SCRIPT), "--source", str(REPO / "global-config"), "--sandbox-repo", str(SANDBOX), "--out", str(cls.out)],
                                  capture_output=True, text=True)
        cls.src = json.loads((REPO / "global-config/opencode.json").read_text())

    def test_it_succeeds_on_the_real_config(self):
        self.assertEqual(self.run1.returncode, 0, self.run1.stdout + self.run1.stderr)

    def test_everything_except_the_plugin_list_is_carried_over_unchanged(self):
        got = json.loads((self.out / "opencode.json").read_text())
        for key, value in self.src.items():
            if key == "plugin":
                continue
            self.assertEqual(got[key], value, key)
        self.assertNotIn("plugin", got)
        self.assertEqual(len(got["agent"]), 46)

    def test_the_plugin_list_is_v2_shaped(self):
        plugins = json.loads((self.out / "opencode.json").read_text())["plugins"]
        self.assertTrue(all("auto-update" not in p and "usage-total" not in p for p in plugins))
        self.assertTrue(any(p.startswith("@fro.bot/systematic@~") for p in plugins))
        self.assertTrue(any(p.endswith("opencode-rate-limit-fallback-mapped") for p in plugins))

    def test_the_root_has_the_files_v2_reads_and_not_the_ones_it_ignores(self):
        names = {p.relative_to(self.out).as_posix() for p in self.out.rglob("*") if p.is_file()}
        for needed in ("opencode.json", "cli.json", "AGENTS.md", "systematic.jsonc", "rate-limit-fallback.json",
                       "plugins/systematic-routing-guard.ts", "plugins/workflow-health-check.ts", "plugins/astra-sol-upgrade.ts",
                       "plugins/lib/routing-guard-helpers.ts"):
            self.assertIn(needed, names)
        self.assertNotIn("tui.json", names)

    def test_every_file_reference_in_the_config_resolves_inside_the_root(self):
        import re
        text = (self.out / "opencode.json").read_text()
        refs = re.findall(r"\{file:(\./[^}]+)\}", text)
        self.assertGreater(len(refs), 0)
        for ref in refs:
            self.assertTrue((self.out / ref).is_file(), ref)

    def test_it_is_deterministic(self):
        again = Path(tempfile.mkdtemp()) / "root"
        subprocess.run([sys.executable, str(SCRIPT), "--source", str(REPO / "global-config"), "--sandbox-repo", str(SANDBOX), "--out", str(again)], check=True, capture_output=True)
        for p in self.out.rglob("*"):
            if p.is_file():
                self.assertEqual(p.read_bytes(), (again / p.relative_to(self.out)).read_bytes(), p.name)

    def test_the_report_lists_what_was_dropped_and_what_needs_attention(self):
        self.assertIn("usage-total", self.run1.stdout)
        self.assertIn("auto-update", self.run1.stdout)


class FileRefs(unittest.TestCase):
    def setUp(self):
        self.m = load()
        self.tmp = Path(tempfile.mkdtemp())
        self.src, self.live, self.stage = self.tmp / "src", self.tmp / "live", self.tmp / "stage"
        for d in (self.src / "prompts", self.live / "prompts", self.stage):
            d.mkdir(parents=True)

    def test_a_reference_found_in_the_source_needs_nothing(self):
        (self.src / "prompts/a.md").write_text("A")
        self.assertEqual(self.m.resolve_file_refs('{"p": "{file:./prompts/a.md}"}', self.src, self.live, self.stage), [])

    def test_a_live_only_file_is_copied_and_reported(self):
        (self.live / "prompts/b.md").write_text("B")
        notes = self.m.resolve_file_refs('{"p": "{file:./prompts/b.md}"}', self.src, self.live, self.stage)
        self.assertEqual((self.stage / "prompts/b.md").read_text(), "B")
        self.assertEqual(len(notes), 1)
        self.assertIn("live", notes[0])

    def test_a_reference_found_nowhere_is_an_error(self):
        with self.assertRaisesRegex(self.m.DeriveError, "prompts/missing.md"):
            self.m.resolve_file_refs('{"p": "{file:./prompts/missing.md}"}', self.src, self.live, self.stage)

    def test_a_reference_that_escapes_the_root_is_refused(self):
        with self.assertRaises(self.m.DeriveError):
            self.m.resolve_file_refs('{"p": "{file:./../../etc/passwd}"}', self.src, self.live, self.stage)


class Apply(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "gc"
        (self.src / "plugins").mkdir(parents=True)
        (self.src / "opencode.json").write_text(json.dumps({"plugin": ["a@1.0.0"], "permission": {}, "agent": {}}))
        (self.src / "cli.json").write_text('{"plugins": []}')
        for name in ("AGENTS.md", "systematic.jsonc", "rate-limit-fallback.json"):
            (self.src / name).write_text(name)
        self.sandbox = self.tmp / "sb"
        (self.sandbox / "opencode/plugins/lib").mkdir(parents=True)
        self.target = self.tmp / "target"

    def run_script(self, *extra):
        return subprocess.run([sys.executable, str(SCRIPT), "--source", str(self.src), "--sandbox-repo", str(self.sandbox), *extra], capture_output=True, text=True)

    def test_apply_defaults_to_a_dry_run(self):
        r = self.run_script("--target", str(self.target))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(self.target.exists())
        self.assertIn("dry-run", r.stdout)

    def test_apply_writes_backs_up_differences_and_never_deletes(self):
        self.run_script("--target", str(self.target), "--apply")
        self.assertEqual(json.loads((self.target / "opencode.json").read_text())["plugins"], ["a@~1.0.0"])
        (self.target / "opencode.json").write_text("edited")
        (self.target / "extra.txt").write_text("keep me")
        self.run_script("--target", str(self.target), "--apply")
        self.assertTrue(list(self.target.glob("opencode.json.bak-*")))
        self.assertEqual((self.target / "extra.txt").read_text(), "keep me")

    def test_apply_refuses_a_v1_root(self):
        r = self.run_script("--target", str(Path.home() / ".config/opencode"), "--apply")
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
