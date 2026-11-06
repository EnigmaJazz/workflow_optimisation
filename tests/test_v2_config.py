"""Canonical config for the OpenCode V2 move (queue Q43), valid on V1 and V2 at once.

Evidence (isolated runs on V1 1.19.5 and V2 2.2.0, 2026-10-29): V1 ignores experimental.subagent_depth
and keeps the top-level one; V2 ignores the top-level one and reads experimental.subagent_depth; V2
normalises the V1 `plugin` key and maps permission.task onto ordered `subagent` rules (last match wins).
A plugin cannot amend a config-defined agent's permissions on V2, so the Astra dispatch right lives here.
"""
import json
import unittest
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "global-config"
# TUI plugins that cannot load on V2 today (V1-only shape, single-file path, or upstream peer cap).
V2_BLOCKED = ("opencode-subagent-statusline", "opencode-usage-total", "gentle-logo", "opencode-plugin-auto-update",
              "opencode-sdd-engram-manage", "opencode-plugin-auto-update-local")


def blocked(entries):
    return [e for e in entries if any(name in str(e) for name in V2_BLOCKED) or str(e).startswith(("file:", "/", "./"))]


class ServerConfig(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads((CONFIG / "opencode.json").read_text())

    def test_depth_is_set_for_both_hosts_and_agrees(self):
        self.assertEqual(self.cfg["subagent_depth"], 4)
        self.assertEqual(self.cfg["experimental"]["subagent_depth"], self.cfg["subagent_depth"])

    def test_orchestrator_may_dispatch_astra_aliases_and_the_rule_comes_last(self):
        task = self.cfg["agent"]["gentle-orchestrator"]["permission"]["task"]
        keys = list(task)
        self.assertEqual(task["*-astra"], "allow")
        self.assertEqual(keys[-1], "*-astra")
        self.assertEqual(keys[0], "*")

    def test_no_explicit_task_rule_can_shadow_an_astra_alias(self):
        # Aliases are generated, never listed; an explicit *-astra deny elsewhere would defeat the wildcard.
        for name, agent in self.cfg["agent"].items():
            task = agent.get("permission", {}).get("task", {})
            if isinstance(task, dict) and name != "gentle-orchestrator":
                self.assertNotIn("*-astra", task, name)

    def test_the_v1_plugin_key_is_used_and_the_v2_key_is_absent(self):
        self.assertIn("plugin", self.cfg)
        self.assertNotIn("plugins", self.cfg)

    def test_pinned_plugins_stay_exact(self):
        for entry in self.cfg["plugin"]:
            if not entry.startswith("file:"):
                self.assertRegex(entry, r"@\d+\.\d+\.\d+$", entry)


class CliJson(unittest.TestCase):
    def setUp(self):
        self.path = CONFIG / "cli.json"
        self.cli = json.loads(self.path.read_text())

    def test_schema_and_shape(self):
        self.assertEqual(self.cli["$schema"], "https://opencode.ai/v2/cli.json")
        self.assertIsInstance(self.cli["plugins"], list)
        self.assertNotIn("plugin", self.cli)

    def test_it_carries_no_plugin_that_cannot_load_on_v2(self):
        self.assertEqual(blocked(self.cli["plugins"]), [])

    def test_v1_only_tui_plugins_exist_in_tui_json_so_the_guard_is_not_vacuous(self):
        tui = json.loads((CONFIG / "tui.json").read_text())["plugin"]
        self.assertTrue(blocked(tui), "tui.json should still hold V1-only entries; they must never reach cli.json")

    def test_detector_positive_control(self):
        self.assertEqual(blocked(["opencode-subagent-statusline@1.3.1", "file:///x/y.js", "ok-plugin@1.0.0"]),
                         ["opencode-subagent-statusline@1.3.1", "file:///x/y.js"])


if __name__ == "__main__":
    unittest.main()
