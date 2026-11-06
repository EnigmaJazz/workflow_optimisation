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
        out, _ = self.derive(["@fro.bot/systematic@3.27.2", "@cortexkit/opencode-magic-context@0.49.29", "plain-pkg@1.2.3"])
        self.assertEqual(out, ["@fro.bot/systematic@~3.27.2", "@cortexkit/opencode-magic-context@~0.49.29", "plain-pkg@~1.2.3"])

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

    def test_an_intended_allow_is_not_reported_but_any_other_still_is(self):
        config = {"permission": {"tool_plain": "deny", "tool_asks": "deny"},
                  "agent": {"orch": {"permission": {"tool_asks": "allow"}}, "worker": {"permission": {"tool_asks": "allow"}}}}
        warnings = self.m.check_rules(config, {"tool_plain": False, "tool_asks": True}, intended={("orch", "tool_asks")})
        self.assertEqual(len(warnings), 1)
        self.assertIn("worker", warnings[0])

    def test_the_real_intended_allow_is_the_orchestrators_review_start(self):
        self.assertEqual(self.m.INTENDED_APPROVAL_ALLOWS, {("gentle-orchestrator", "host_review_start")})

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
        derive = load()
        mirrored = derive.ACCESS_MIRRORS
        got = json.loads((self.out / "opencode.json").read_text())
        expected = json.loads(json.dumps(self.src))
        derive.apply_v2_grep_policy(expected)  # intended difference: V2's grep policy (global deny, orchestrator ask)
        derive.apply_v2_secret_read_policy(expected)  # secret-file denies re-applied after agent-level read allows
        derive.add_v2_astra_aliases(expected)  # the Astra aliases of config-defined agents
        derive.drop_v2_unsupported(expected)  # and keys V2 reports as unsupported and ignores
        for key, value in expected.items():
            if key == "plugin":
                continue
            if key == "mcp":  # only the vision bridge moves; the rest are carried over, plus V2's codemode=false on every server
                for name, server in value.items():
                    if name != "vision-bridge":
                        self.assertEqual(got["mcp"][name], {**server, "codemode": False}, name)
                    self.assertIs(got["mcp"][name]["codemode"], False, name)
                self.assertEqual(set(got["mcp"]), set(value))
                continue
            if key == "agent":  # carried over, plus the one plugin-owned agent whose sandbox access is mirrored in (V2 only)
                self.assertEqual({k: v for k, v in got["agent"].items() if k not in mirrored}, value)
                self.assertEqual(set(got["agent"]) - set(value), set(mirrored))
                continue
            self.assertEqual(got[key], value, key)
        self.assertNotIn("plugin", got)
        # What the run must have removed, asserted on the derived file itself and not through the function under test.
        self.assertEqual(got["permission"]["grep"], "deny")  # asserted on the derived file, not through the function under test
        self.assertEqual(got["agent"]["gentle-orchestrator"]["permission"]["grep"], "ask")
        self.assertTrue(all(a.get("permission", {}).get("grep") in (None, "deny") for n, a in got["agent"].items() if n != "gentle-orchestrator"))
        self.assertNotIn("subagent_depth", got)
        self.assertEqual(got["experimental"]["subagent_depth"], self.src.get("experimental", {}).get("subagent_depth", self.src.get("subagent_depth")))
        self.assertNotIn("prune", got.get("compaction", {}))
        for provider in got.get("provider", {}).values():
            for model in (provider.get("models") or {}).values():
                for flag in ("temperature", "reasoning", "attachment"):
                    self.assertNotIn(flag, model)
        self.assertTrue(all(agent.get("variant") != "" for agent in got["agent"].values()))
        aliases = [n for n in got["agent"] if n.endswith("-astra")]
        self.assertGreaterEqual(len(aliases), 2)  # planner and frontend-dev-premium; the verifier and spec advisors left Sol (2026-11-01)
        self.assertEqual(len(got["agent"]), 48 + len(mirrored) + len(aliases))
        # Secret files are unreadable for every agent, asserted on the derived file: no agent-level read rule may allow them.
        denies = {p for p, e in self.src["permission"]["read"].items() if e == "deny"}
        for name, agent in got["agent"].items():
            read = (agent.get("permission") or {}).get("read")
            self.assertNotEqual(read, "allow", name)
            if isinstance(read, dict):
                self.assertTrue(all(read.get(p) == "deny" for p in denies), name)
                self.assertEqual(list(read)[-len(denies):] and set(list(read)[-len(denies):]), denies, name)  # and they come last
        mirrored = got["agent"]["systematic-implementer"]
        reference = got["agent"]["gentle-ai-worker"]
        self.assertEqual(mirrored["permission"]["sandbox_bash"], "allow")
        self.assertEqual({k: v for k, v in mirrored["permission"].items()}, {k: v for k, v in reference["permission"].items() if k.startswith(("sandbox_", "host_"))})

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

    def test_no_prompt_is_taken_from_the_live_root_any_more(self):
        self.assertNotIn("copied from the live V1 root", self.run1.stdout)

    def test_the_vision_bridge_runs_from_the_v2_root_with_its_own_credential_and_log_paths(self):
        bridge = json.loads((self.out / "opencode.json").read_text())["mcp"]["vision-bridge"]
        root = "/home/james/.local/share/opencode-v2/config/opencode"
        self.assertEqual(bridge["command"], ["python3", f"{root}/mcp/vision-bridge/server.py"])
        env = bridge["environment"]
        self.assertNotIn("VISION_BRIDGE_AUTH_FILE", env)  # the bridge has no direct OpenAI leg and so no login file
        self.assertNotIn("VISION_BRIDGE_AUTH_DB", env)
        self.assertTrue(env["VISION_BRIDGE_LEG_LOG"].startswith("/home/james/.local/share/opencode-v2/data/"))
        self.assertTrue((self.out / "mcp/vision-bridge/server.py").is_file())
        self.assertNotIn("under /home/james/.config/opencode", self.run1.stdout)
        # the V1 credential store is not referenced anywhere in the derived config
        self.assertNotIn(".local/share/opencode/auth.json", json.dumps(bridge))


class McpPaths(unittest.TestCase):
    def setUp(self):
        self.m = load()
        self.src = Path(tempfile.mkdtemp())
        (self.src / "mcp/tool").mkdir(parents=True)
        (self.src / "mcp/tool/server.py").write_text("x")
        self.v1 = str(Path.home() / ".config/opencode")
        self.root = Path("/r/config/opencode")

    def test_a_command_under_the_v1_root_that_the_repo_holds_is_rewritten_into_the_v2_root(self):
        config = {"mcp": {"t": {"type": "local", "command": ["python3", f"{self.v1}/mcp/tool/server.py"]}}}
        notes = self.m.rewrite_mcp(config, self.src, self.root, {"t": {"A": "{data}/a"}})
        self.assertEqual(config["mcp"]["t"]["command"], ["python3", "/r/config/opencode/mcp/tool/server.py"])
        self.assertEqual(config["mcp"]["t"]["environment"], {"A": "/r/data/a"})
        self.assertEqual(len(notes), 1)

    def test_a_command_the_repo_does_not_hold_is_left_alone_and_reported(self):
        config = {"mcp": {"t": {"type": "local", "command": ["python3", f"{self.v1}/mcp/other/server.py"]}}}
        warnings = self.m.check_v1_paths(config)
        self.m.rewrite_mcp(config, self.src, self.root, {})
        self.assertEqual(config["mcp"]["t"]["command"][1], f"{self.v1}/mcp/other/server.py")
        self.assertEqual(len(warnings), 1)

    def test_remote_servers_and_existing_environment_are_untouched_or_merged(self):
        config = {"mcp": {"r": {"type": "remote", "url": "https://x"},
                          "t": {"type": "local", "command": ["python3", f"{self.v1}/mcp/tool/server.py"], "environment": {"KEEP": "1"}}}}
        self.m.rewrite_mcp(config, self.src, self.root, {"t": {"A": "{data}/a"}})
        self.assertEqual(config["mcp"]["r"], {"type": "remote", "url": "https://x"})
        self.assertEqual(config["mcp"]["t"]["environment"], {"KEEP": "1", "A": "/r/data/a"})


class McpCodeMode(unittest.TestCase):
    def setUp(self):
        self.m = load()

    def test_every_server_is_exposed_directly_and_reported(self):
        config = {"mcp": {"a": {"type": "remote", "url": "https://x"}, "b": {"type": "local", "command": ["c"]}}}
        notes = self.m.expose_mcp_directly(config)
        self.assertEqual([config["mcp"]["a"]["codemode"], config["mcp"]["b"]["codemode"]], [False, False])
        self.assertEqual(len(notes), 1)
        self.assertIn("a, b", notes[0])

    def test_an_explicit_choice_in_the_source_is_kept(self):
        config = {"mcp": {"a": {"type": "remote", "url": "https://x", "codemode": True}}}
        self.assertEqual(self.m.expose_mcp_directly(config), [])
        self.assertIs(config["mcp"]["a"]["codemode"], True)

    def test_no_servers_is_a_no_op(self):
        self.assertEqual(self.m.expose_mcp_directly({}), [])


class AccessMirror(unittest.TestCase):
    def setUp(self):
        self.m = load()
        self.config = {"agent": {"ref": {"permission": {"sandbox_bash": "allow", "sandbox_apply": "ask", "edit": "deny"}, "tools": {"sandbox_bash": True, "grep": False}}}}

    def test_only_sandbox_and_host_rules_are_copied(self):
        notes = self.m.mirror_agent_access(self.config, {"target": "ref"})
        self.assertEqual(self.config["agent"]["target"], {"permission": {"sandbox_bash": "allow", "sandbox_apply": "ask"}, "tools": {"sandbox_bash": True}})
        self.assertEqual(len(notes), 1)

    def test_existing_target_settings_are_kept_and_mirrored_rules_win(self):
        self.config["agent"]["target"] = {"permission": {"sandbox_bash": "deny", "edit": "deny"}, "model": "m"}
        self.m.mirror_agent_access(self.config, {"target": "ref"})
        self.assertEqual(self.config["agent"]["target"]["permission"], {"sandbox_bash": "allow", "edit": "deny", "sandbox_apply": "ask"})
        self.assertEqual(self.config["agent"]["target"]["model"], "m")

    def test_a_missing_reference_agent_is_skipped_and_reported(self):
        config = {"agent": {}}
        notes = self.m.mirror_agent_access(config, {"target": "ref"})
        self.assertEqual(config["agent"], {})
        self.assertIn("skipped", notes[0])

    def test_every_overlay_agent_that_allows_sandbox_mutation_is_mirrored(self):
        # An overlay allow alone loses to the category denies on V2, so each such agent needs the mirror. This catches a new one.
        import re
        text = re.sub(r"^\s*//.*$", "", (REPO / "global-config" / "systematic.jsonc").read_text(), flags=re.M)
        agents = json.loads(text)["agents"]
        mutating = {n for n, a in agents.items() if (a.get("permission") or {}).get("sandbox_bash") == "allow"}
        self.assertEqual(mutating, set(self.m.ACCESS_MIRRORS))

    def test_the_real_mapping_points_at_an_agent_in_the_real_config(self):
        real = json.loads((REPO / "global-config" / "opencode.json").read_text())
        for reference in self.m.ACCESS_MIRRORS.values():
            self.assertIn(reference, real["agent"])


class V2SecretReadPolicy(unittest.TestCase):
    """`.env`, keys and credentials stay unreadable for every agent: V2 uses the last matching rule, so an agent-level
    `read: allow` that comes after the global denies used to win."""

    GLOBAL = {"*": "allow", "**/.env": "deny", "*.env": "deny", "**/*.key": "deny", "**/.env.example": "allow"}

    def setUp(self):
        self.m = load()

    def config(self, **agents):
        return {"permission": {"read": dict(self.GLOBAL)}, "agent": agents}

    def test_an_agent_with_read_allow_gets_the_global_map_with_the_denies_last(self):
        config = self.config(a={"permission": {"read": "allow"}})
        notes = self.m.apply_v2_secret_read_policy(config)
        read = config["agent"]["a"]["permission"]["read"]
        self.assertEqual(read["**/.env"], "deny")
        self.assertEqual(read["*"], "allow")
        self.assertEqual(list(read)[-3:], ["**/.env", "*.env", "**/*.key"])
        self.assertIn("1 agent(s): a", notes[0])

    def test_an_agent_read_map_keeps_its_entries_and_a_conflicting_allow_becomes_deny(self):
        config = self.config(a={"permission": {"read": {"docs/**": "allow", "**/.env": "allow", "*": "allow"}}})
        self.m.apply_v2_secret_read_policy(config)
        read = config["agent"]["a"]["permission"]["read"]
        self.assertEqual(read["docs/**"], "allow")
        self.assertEqual(read["**/.env"], "deny")
        self.assertEqual(list(read)[-3:], ["**/.env", "*.env", "**/*.key"])  # after the wildcard allow

    def test_agents_without_a_read_rule_or_with_read_deny_are_untouched_and_the_run_is_idempotent(self):
        config = self.config(a={"permission": {"edit": "deny"}}, b={"permission": {"read": "deny"}}, c={"mode": "subagent"}, d={"permission": {"read": "allow"}})
        self.m.apply_v2_secret_read_policy(config)
        self.assertEqual(config["agent"]["a"], {"permission": {"edit": "deny"}})
        self.assertEqual(config["agent"]["b"]["permission"]["read"], "deny")
        before = json.loads(json.dumps(config))
        self.assertEqual(self.m.apply_v2_secret_read_policy(config), [])
        self.assertEqual(config, before)

    def test_a_config_without_a_global_read_map_is_left_alone(self):
        config = {"permission": {"read": "allow"}, "agent": {"a": {"permission": {"read": "allow"}}}}
        self.assertEqual(self.m.apply_v2_secret_read_policy(config), [])
        self.assertEqual(config["agent"]["a"]["permission"]["read"], "allow")


class V2AstraAliases(unittest.TestCase):
    """Config-defined Astra aliases are written by derive, so V2 composes them like their bases."""

    def setUp(self):
        self.m = load()

    def agent(self, model="openai/gpt-6.1-sol", **extra):
        return {"model": model, "mode": "subagent", "description": "d", "permission": {"sandbox_write": "allow"}, **extra}

    def test_a_sol_subagent_gets_a_hidden_alias_on_the_astra_model_with_its_own_rules(self):
        config = {"agent": {"advisor": self.agent()}}
        notes = self.m.add_v2_astra_aliases(config)
        alias = config["agent"]["advisor-astra"]
        self.assertEqual((alias["model"], alias["variant"], alias["hidden"]), ("openai/gpt-6-astra", "xhigh", True))
        self.assertEqual(alias["permission"], {"sandbox_write": "allow"})  # the base's grant survives
        self.assertIsNot(alias["permission"], config["agent"]["advisor"]["permission"])  # a copy, not a shared object
        self.assertEqual(alias["description"], "d — selectable Astra upgrade")
        self.assertEqual(config["agent"]["advisor"]["model"], "openai/gpt-6.1-sol")
        self.assertIn("advisor-astra", notes[0])

    def test_the_same_agents_are_excluded_as_by_the_plugin(self):
        agents = {"adv": self.agent(), "orch": self.agent(mode="primary"), "other": self.agent(model="openai/gpt-6.1-luna"), "general": self.agent(),
                  "frontend-apply": self.agent(), "the-implementer": self.agent(), "review-risk": self.agent(), "asi-review-refuter": self.agent(),
                  "x-astra": self.agent(), "systematic-implementer": self.agent(), "bug-reproduction-validator": self.agent()}
        config = {"agent": agents}
        self.m.add_v2_astra_aliases(config)
        self.assertEqual(sorted(n for n in config["agent"] if n.endswith("-astra") and n != "x-astra"), ["adv-astra"])

    def test_an_existing_alias_is_never_overwritten_and_a_second_run_adds_nothing(self):
        config = {"agent": {"adv": self.agent(), "adv-astra": {"model": "x/y"}}}
        self.assertEqual(self.m.add_v2_astra_aliases(config), [])
        self.assertEqual(config["agent"]["adv-astra"], {"model": "x/y"})
        config = {"agent": {"adv": self.agent()}}
        self.m.add_v2_astra_aliases(config)
        before = json.loads(json.dumps(config))
        self.assertEqual(self.m.add_v2_astra_aliases(config), [])
        self.assertEqual(config, before)

    def test_the_v2_object_model_shape_is_understood(self):
        config = {"agent": {"adv": self.agent(model={"providerID": "openai", "id": "gpt-6.1-sol"})}}
        self.m.add_v2_astra_aliases(config)
        self.assertIn("adv-astra", config["agent"])

    def test_the_selection_rules_match_the_plugin_source(self):
        ts = (REPO / "global-config" / "plugins" / "astra-sol-upgrade.ts").read_text()
        import re
        for name, value in (("SOL_MODEL", self.m.ASTRA_SOL_MODEL), ("ASTRA_MODEL", self.m.ASTRA_MODEL), ("ASTRA_VARIANT", self.m.ASTRA_VARIANT), ("ASTRA_SUFFIX", self.m.ASTRA_SUFFIX)):
            self.assertEqual(re.search(rf'const {name} = "([^"]+)"', ts).group(1), value, name)
        block = re.search(r"function isImplementationRoute.*?\n}\n", ts, re.S).group(0)
        self.assertEqual(tuple(re.findall(r'name === "([^"]+)"', block)), self.m.ASTRA_IMPLEMENTATION_NAMES)
        self.assertEqual(tuple(re.findall(r"test\(name\)", block)).__len__(), len(self.m.ASTRA_IMPLEMENTATION_PATTERNS))
        for pattern in self.m.ASTRA_IMPLEMENTATION_PATTERNS:
            self.assertIn("/" + pattern + "/", block)
        self.assertIn("/" + self.m.ASTRA_REVIEW_ACTOR + "/", ts)


class V2PluginVersions(unittest.TestCase):
    """V2 can run a newer plugin than the shared source pins, so V1 (the rollback path) is untouched."""

    def setUp(self):
        self.m = load()

    def test_v2_runs_aft_0635_while_v1_keeps_the_shared_pin(self):
        # 0.63.4 exited in the V2 nono profile (storage lease opened "/"); 0.63.5 starts there (cortexkit/aft#1245).
        self.assertEqual(self.m.V2_PLUGIN_VERSIONS, {"@cortexkit/aft-opencode": "0.63.5"})
        out, notes = self.m.derive_plugins(["@cortexkit/aft-opencode@0.62.0", "@fro.bot/systematic@3.27.2"])
        self.assertEqual(out, ["@cortexkit/aft-opencode@~0.63.5", "@fro.bot/systematic@~3.27.2"])
        self.assertTrue(any("aft-opencode: V2 runs 0.63.5" in n and "0.62.0 for V1" in n for n in notes))

    def test_an_override_still_moves_v2_ahead_of_the_shared_pin_on_v2_only(self):
        self.m.V2_PLUGIN_VERSIONS = {"@cortexkit/aft-opencode": "0.63.4"}
        out, notes = self.m.derive_plugins(["@cortexkit/aft-opencode@0.62.0", "@fro.bot/systematic@3.27.2"])
        self.assertEqual(out, ["@cortexkit/aft-opencode@~0.63.4", "@fro.bot/systematic@~3.27.2"])
        self.assertTrue(any("aft-opencode: V2 runs 0.63.4" in n and "0.62.0 for V1" in n for n in notes))

    def test_a_source_pin_already_at_the_override_adds_no_note(self):
        self.m.V2_PLUGIN_VERSIONS = {"@cortexkit/aft-opencode": "0.63.4"}
        out, notes = self.m.derive_plugins(["@cortexkit/aft-opencode@0.63.4"])
        self.assertEqual((out, notes), (["@cortexkit/aft-opencode@~0.63.4"], []))

    def test_the_shared_v1_source_still_pins_the_old_aft(self):
        source = json.loads((REPO / "global-config" / "opencode.json").read_text())
        self.assertIn("@cortexkit/aft-opencode@0.62.0", source["plugin"])  # V1 rollback keeps the version it was proven with


class V2GrepPolicy(unittest.TestCase):
    """Native grep: orchestrator ask, everything else deny. V2 applies the last matching rule, so the global rule must not be ask."""

    def setUp(self):
        self.m = load()

    def config(self, **extra):
        return {"permission": {"grep": "ask", "ctx_memory": "deny"}, "agent": {"gentle-orchestrator": {"mode": "primary"}, "general": {"permission": {"grep": "deny"}}}, **extra}

    def test_global_becomes_deny_and_the_orchestrator_carries_the_ask(self):
        config = self.config()
        notes = self.m.apply_v2_grep_policy(config)
        self.assertEqual(config["permission"]["grep"], "deny")
        self.assertEqual(config["agent"]["gentle-orchestrator"]["permission"], {"grep": "ask"})
        self.assertEqual(config["agent"]["general"]["permission"], {"grep": "deny"})
        self.assertEqual(config["permission"]["ctx_memory"], "deny")  # nothing else is touched
        self.assertEqual(len(notes), 1)

    def test_an_existing_orchestrator_permission_map_keeps_its_other_rules(self):
        config = self.config()
        config["agent"]["gentle-orchestrator"]["permission"] = {"host_git_commit": "ask", "grep": "allow"}
        self.m.apply_v2_grep_policy(config)
        self.assertEqual(config["agent"]["gentle-orchestrator"]["permission"], {"host_git_commit": "ask", "grep": "ask"})

    def test_it_is_idempotent_and_ignores_a_config_whose_global_grep_is_not_ask(self):
        config = self.config()
        self.m.apply_v2_grep_policy(config)
        before = json.loads(json.dumps(config))
        self.assertEqual(self.m.apply_v2_grep_policy(config), [])
        self.assertEqual(config, before)

    def test_without_a_usable_orchestrator_derive_refuses_instead_of_leaving_the_global_ask(self):
        for config, fragment in (
            ({"permission": {"grep": "ask"}, "agent": {}}, "no gentle-orchestrator agent"),
            ({"permission": {"grep": "ask"}, "agent": {"gentle-orchestrator": {"permission": "ask"}}}, "is not an object"),
        ):
            with self.assertRaises(self.m.DeriveError) as raised:
                self.m.apply_v2_grep_policy(config)
            self.assertIn(fragment, str(raised.exception))
            self.assertEqual(config["permission"]["grep"], "ask")  # nothing half-applied

    def test_a_global_that_is_not_ask_needs_no_orchestrator(self):
        self.assertEqual(self.m.apply_v2_grep_policy({"permission": {"grep": "deny"}, "agent": {}}), [])


class V2Unsupported(unittest.TestCase):
    """Keys OpenCode V2 reports as 'omitted unsupported legacy ...' on every config load (thousands of repeated warnings that
    drown real ones). Each is dead on V2, so the derived config simply does not carry it."""

    def setUp(self):
        self.m = load()

    def test_a_top_level_subagent_depth_is_dropped_when_the_experimental_one_exists(self):
        config = {"subagent_depth": 4, "experimental": {"subagent_depth": 4}}
        self.m.drop_v2_unsupported(config)
        self.assertEqual(config, {"experimental": {"subagent_depth": 4}})

    def test_a_top_level_subagent_depth_moves_to_experimental_when_it_is_the_only_one(self):
        # V2 reads experimental.subagent_depth ("Increase experimental.subagent_depth to allow nested subagents"), so the
        # limit must not be lost just because only the legacy spelling was set.
        config = {"subagent_depth": 3}
        self.m.drop_v2_unsupported(config)
        self.assertEqual(config, {"experimental": {"subagent_depth": 3}})

    def test_the_experimental_value_wins_when_the_two_disagree(self):
        config = {"subagent_depth": 9, "experimental": {"subagent_depth": 2}}
        self.m.drop_v2_unsupported(config)
        self.assertEqual(config["experimental"]["subagent_depth"], 2)
        self.assertNotIn("subagent_depth", config)

    def test_a_null_experimental_does_not_abort_the_run(self):
        config = {"subagent_depth": 3, "experimental": None}
        self.m.drop_v2_unsupported(config)
        self.assertEqual(config, {"experimental": {"subagent_depth": 3}})

    def test_a_non_object_experimental_keeps_the_legacy_key_and_says_so(self):
        config = {"subagent_depth": 3, "experimental": "x"}
        notes = self.m.drop_v2_unsupported(config)
        self.assertEqual(config, {"subagent_depth": 3, "experimental": "x"})
        self.assertIn("nowhere to move", notes[0])

    def test_the_notes_say_what_moved_and_what_was_dropped(self):
        moved = self.m.drop_v2_unsupported({"subagent_depth": 3})
        self.assertEqual(len(moved), 1)
        self.assertTrue(moved[0].startswith("moved subagent_depth to experimental.subagent_depth"))
        self.assertNotIn("ignores", moved[0])  # a moved setting still takes effect
        one = self.m.drop_v2_unsupported({"compaction": {"prune": False}})
        self.assertEqual(one, ["dropped 1 legacy setting that V2 reports as unsupported and ignores (1 compaction.prune)"])
        both = self.m.drop_v2_unsupported({"subagent_depth": 3, "compaction": {"prune": False}})
        self.assertEqual(len(both), 2)
        self.assertIn("dropped 1 legacy setting", both[0])
        self.assertTrue(both[1].startswith("moved subagent_depth"))

    def test_compaction_prune_goes_and_compaction_auto_stays(self):
        config = {"compaction": {"auto": False, "prune": False}}
        self.m.drop_v2_unsupported(config)
        self.assertEqual(config["compaction"], {"auto": False})

    def test_model_flags_are_dropped_and_real_model_settings_stay(self):
        config = {"provider": {"p": {"models": {"m": {"name": "M", "temperature": True, "reasoning": True, "attachment": False,
                                                      "limit": {"context": 1}, "variants": {"high": {}}}}}}}
        self.m.drop_v2_unsupported(config)
        self.assertEqual(config["provider"]["p"]["models"]["m"], {"name": "M", "limit": {"context": 1}, "variants": {"high": {}}})

    def test_an_empty_agent_variant_goes_and_a_real_one_stays(self):
        config = {"agent": {"a": {"variant": "", "model": "x/y"}, "b": {"variant": "max", "model": "x/y"}}}
        self.m.drop_v2_unsupported(config)
        self.assertEqual(config["agent"]["a"], {"model": "x/y"})
        self.assertEqual(config["agent"]["b"]["variant"], "max")

    def test_it_is_idempotent_and_reports_only_what_it_removed(self):
        config = {"subagent_depth": 4, "experimental": {"subagent_depth": 4}, "compaction": {"prune": False},
                  "provider": {"p": {"models": {"m": {"reasoning": True}}}}, "agent": {"a": {"variant": ""}}}
        first = self.m.drop_v2_unsupported(config)
        self.assertEqual(len(first), 1)
        self.assertRegex(first[0], r"\b4 legacy")  # subagent_depth, compaction.prune, reasoning and the empty variant
        self.assertEqual(self.m.drop_v2_unsupported(config), [])

    def test_a_config_with_none_of_them_is_untouched(self):
        config = {"agent": {"a": {"variant": "max"}}, "provider": {"p": {"models": {"m": {"name": "M"}}}}, "compaction": {"auto": True}}
        before = json.loads(json.dumps(config))
        self.assertEqual(self.m.drop_v2_unsupported(config), [])
        self.assertEqual(config, before)


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

    def test_apply_also_places_the_systematic_overlay_in_the_server_home(self):
        self.run_script("--target", str(self.target), "--apply")
        home_copy = self.tmp / "home/.config/opencode/systematic.jsonc"
        self.assertEqual(home_copy.read_text(), "systematic.jsonc")
        self.assertEqual((self.target / "systematic.jsonc").read_text(), "systematic.jsonc")

    def test_a_dry_run_does_not_create_the_server_home(self):
        self.run_script("--target", str(self.target))
        self.assertFalse((self.tmp / "home").exists())

    def test_apply_refuses_a_v1_root(self):
        r = self.run_script("--target", str(Path.home() / ".config/opencode"), "--apply")
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
