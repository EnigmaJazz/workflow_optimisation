"""Verifier V2 mode (queue Q44): version detection and the probe wrapper.

Facts from the B1 probe on OpenCode V2 2.2.0: `opencode run` hangs unless stdin is closed, a plain call
joins a shared background service on a fixed port (use --standalone), `agent list` / `debug agent`
do not exist. V1 behaviour must stay exactly as it was."""
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MODULES = REPO / "verify"
VERSION_MODULE = MODULES / "21-opencode-major.sh"
PROBE = MODULES / "checkers" / "oc-probe.sh"


class Stub:
    """A fake `opencode` on PATH that records argv and stdin and prints a chosen version."""

    def __init__(self, version_output):
        self.dir = Path(tempfile.mkdtemp())
        self.log = self.dir / "calls.log"
        script = self.dir / "opencode"
        script.write_text(
            "#!/usr/bin/env bash\n"
            f'if [ "${{1:-}}" = "--version" ]; then printf %s\\\\n {version_output!r}; exit 0; fi\n'
            f'printf "ARGS:%s\\n" "$*" >> "{self.log}"\n'
            f'if [ -t 0 ]; then echo "STDIN:tty" >> "{self.log}"; else printf "STDIN:%s\\n" "$(timeout 2 cat | head -c 40)" >> "{self.log}"; fi\n'
        )
        script.chmod(script.stat().st_mode | stat.S_IEXEC)

    def env(self, **extra):
        return {**os.environ, "PATH": f"{self.dir}:{os.environ['PATH']}", **extra}

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def detect(version_output=None, env_major=None):
    stub = Stub(version_output) if version_output is not None else None
    try:
        env = stub.env() if stub else {**os.environ, "PATH": "/nonexistent-dir"}
        if env_major is not None:
            env["WORKFLOW_VERIFY_OPENCODE_MAJOR"] = env_major
        script = f'VERIFY_MODULE_DIR="{MODULES}"\nsource "{VERSION_MODULE}"\necho "MAJOR=$OC_MAJOR"\n'
        r = subprocess.run([shutil.which("bash"), "-c", script], capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL)
        return r.returncode, r.stdout.strip(), r.stderr
    finally:
        if stub:
            stub.close()


class VersionDetection(unittest.TestCase):
    def test_v1_plain_version(self):
        self.assertEqual(detect("1.19.5")[:2], (0, "MAJOR=1"))

    def test_v2_prefixed_version(self):
        self.assertEqual(detect("opencode v2.2.0")[:2], (0, "MAJOR=2"))

    def test_unparseable_output_is_unknown_not_a_guess(self):
        self.assertEqual(detect("garbage")[:2], (0, "MAJOR=0"))

    def test_a_missing_opencode_is_unknown(self):
        self.assertEqual(detect(None)[:2], (0, "MAJOR=0"))

    def test_the_override_wins_for_fixtures(self):
        self.assertEqual(detect("1.19.5", env_major="2")[:2], (0, "MAJOR=2"))

    def test_a_non_numeric_override_is_ignored(self):
        self.assertEqual(detect("1.19.5", env_major="two")[:2], (0, "MAJOR=1"))


def probe(major, version="1.19.5", stdin_data=b"piped-input", args=("run", "--format", "json", "hello")):
    stub = Stub(version)
    try:
        env = stub.env(OC_MAJOR=major)
        r = subprocess.run(["bash", str(PROBE), *args], input=stdin_data, capture_output=True, env=env)
        return r.returncode, stub.calls()
    finally:
        stub.close()


class ProbeWrapper(unittest.TestCase):
    def test_v1_call_is_unchanged_and_stdin_is_inherited(self):
        rc, calls = probe("1")
        self.assertEqual(rc, 0)
        self.assertEqual(calls[0], "ARGS:run --format json hello")
        self.assertEqual(calls[1], "STDIN:piped-input")

    def test_v2_call_is_standalone_with_closed_stdin(self):
        rc, calls = probe("2")
        self.assertEqual(rc, 0)
        self.assertEqual(calls[0], "ARGS:--standalone run --format json hello")
        self.assertEqual(calls[1], "STDIN:")

    def run_env_stub(self, major, base=None):
        d = Path(tempfile.mkdtemp())
        stub = d / "opencode"
        stub.write_text('#!/usr/bin/env bash\nprintf "%s|%s|%s|%s|%s|%s\\n" "$HOME" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$XDG_STATE_HOME" "$XDG_CACHE_HOME" "$*"\n')
        stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
        env = {**os.environ, "PATH": f"{d}:{os.environ['PATH']}", "OC_MAJOR": major, "HOME": "/home/v1", "XDG_CONFIG_HOME": "/v1/config"}
        env.pop("V2_BASE_DIR", None)
        if base:
            env["V2_BASE_DIR"] = base
        r = subprocess.run(["bash", str(PROBE), "debug", "agents"], capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL)
        return r.stdout.strip()

    def test_a_v2_probe_runs_with_the_v2_roots_and_overlay_home_when_the_base_is_known(self):
        out = self.run_env_stub("2", "/v2")
        self.assertEqual(out, "/v2/config/home|/v2/config|/v2/data|/v2/state|/v2/cache|--standalone debug agents")

    def test_without_the_base_a_v2_probe_keeps_the_caller_environment(self):
        self.assertEqual(self.run_env_stub("2"), "/home/v1|/v1/config||||--standalone debug agents".replace("||||", "|" + os.environ.get("XDG_DATA_HOME", "") + "|" + os.environ.get("XDG_STATE_HOME", "") + "|" + os.environ.get("XDG_CACHE_HOME", "") + "|"))

    def test_v1_never_gets_the_v2_environment_even_if_the_base_is_set(self):
        out = self.run_env_stub("1", "/v2")
        self.assertTrue(out.startswith("/home/v1|/v1/config|"), out)
        self.assertTrue(out.endswith("|debug agents"), out)

    def test_unknown_major_behaves_as_v1(self):
        self.assertEqual(probe("0")[1][0], "ARGS:run --format json hello")

    def test_the_exit_status_of_opencode_is_preserved(self):
        stub = Stub("1.19.5")
        try:
            (stub.dir / "opencode").write_text('#!/usr/bin/env bash\nexit 7\n')
            r = subprocess.run(["bash", str(PROBE), "run"], capture_output=True, env=stub.env(OC_MAJOR="1"), stdin=subprocess.DEVNULL)
            self.assertEqual(r.returncode, 7)
        finally:
            stub.close()


class Wiring(unittest.TestCase):
    def test_no_module_calls_opencode_directly_for_probes(self):
        import re
        for module in sorted(MODULES.glob("*.sh")):
            for number, line in enumerate(module.read_text().splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#") or "command_exists" in stripped or "echo " in stripped or "fail " in stripped:
                    continue
                self.assertIsNone(re.search(r"\bopencode (agent|debug|run)\b", stripped), f"{module.name}:{number}: {stripped}")

    def test_probes_go_through_the_wrapper(self):
        text = (MODULES / "61-section-10-behavioural.sh").read_text()
        self.assertGreaterEqual(text.count('bash "$OC_PROBE" run'), 3)

    def test_the_version_module_runs_before_the_sections(self):
        names = sorted(p.name for p in MODULES.glob("*.sh"))
        self.assertLess(names.index("21-opencode-major.sh") if "21-opencode-major.sh" in names else 99, names.index("50-section-0-recover.sh"))


SHIM = MODULES / "checkers" / "v2-agents-shim.cjs"
V2_AGENTS = [
    {"id": "zed", "name": "zed", "model": {"id": "claude-x", "providerID": "anthropic"},
     "request": {"settings": {}, "headers": {}, "body": {"foo": 1, "temperature": 0.3}},
     "system": "hello", "description": "d", "mode": "subagent", "hidden": False, "steps": 7,
     "permissions": [{"action": "shell", "resource": "git *", "effect": "allow"},
                     {"action": "edit", "resource": "*", "effect": "deny"}]},
    {"id": "build", "name": "Build", "mode": "primary", "hidden": False,
     "request": {"settings": {}, "headers": {}, "body": {}}, "permissions": []},
]


def run_shim(payload, stdin_text=None):
    import json
    out = Path(tempfile.mkdtemp())
    listing, debug_dir = out / "list.txt", out / "debug"
    r = subprocess.run(["node", str(SHIM), str(listing), str(debug_dir)],
                       input=stdin_text if stdin_text is not None else json.dumps(payload),
                       capture_output=True, text=True)
    return r, listing, debug_dir


class AgentsShimDerived(unittest.TestCase):
    """The V1-shaped `tools` map and the variant, both derived from what V2 does report."""

    def debug(self, agent):
        import json
        r, _, debug_dir = run_shim([agent])
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads((debug_dir / f"{agent['id']}.json").read_text())

    def agent(self, rules, model=None):
        base = {"id": "a", "name": "a", "mode": "subagent", "hidden": False, "request": {"settings": {}, "headers": {}, "body": {}}, "permissions": rules}
        if model:
            base["model"] = model
        return base

    def rule(self, action, effect, resource="*"):
        return {"action": action, "resource": resource, "effect": effect}

    def test_a_tool_is_true_when_its_last_star_rule_allows_or_asks_and_false_when_it_denies(self):
        tools = self.debug(self.agent([self.rule("grep", "deny"), self.rule("sandbox_read", "allow"), self.rule("sandbox_apply", "ask")]))["tools"]
        self.assertEqual(tools, {"grep": False, "sandbox_read": True, "sandbox_apply": True})

    def test_the_last_rule_wins_so_a_later_ask_overrides_an_earlier_deny(self):
        # This is V2's own semantics, and the reason a global `grep: ask` listed after an agent's deny exposes native grep.
        self.assertEqual(self.debug(self.agent([self.rule("grep", "deny"), self.rule("grep", "ask")]))["tools"], {"grep": True})
        self.assertEqual(self.debug(self.agent([self.rule("ctx_memory", "allow"), self.rule("ctx_memory", "deny")]))["tools"], {"ctx_memory": False})

    def test_unnamed_narrow_and_wildcard_rules_never_become_entries(self):
        tools = self.debug(self.agent([self.rule("*", "allow"), self.rule("read", "ask", "*.env"), self.rule("edit", "bogus")]))["tools"]
        self.assertEqual(tools, {})  # not configured is never read as enabled

    def test_the_shell_rule_is_named_bash_in_the_tools_map_as_in_the_permission_list(self):
        self.assertEqual(self.debug(self.agent([self.rule("shell", "allow")]))["tools"], {"bash": True})

    def test_the_model_variant_is_emitted_at_the_top_level_where_the_checker_reads_it(self):
        debug = self.debug(self.agent([], {"id": "gpt-6.1-sol", "providerID": "openai", "variant": "high"}))
        self.assertEqual(debug["variant"], "high")
        self.assertEqual(debug["model"], {"providerID": "openai", "modelID": "gpt-6.1-sol"})
        self.assertNotIn("variant", self.debug(self.agent([], {"id": "m", "providerID": "p"})))


class AgentsShim(unittest.TestCase):
    """V2 has `debug agents` (one JSON array) instead of `agent list` + `debug agent <name>`; the shim
    rewrites it into the V1 shapes the runtime checker reads."""

    def test_listing_uses_the_v1_line_format_keyed_by_id(self):
        r, listing, _ = run_shim(V2_AGENTS)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(listing.read_text().splitlines(), ["zed (subagent)", "build (primary)"])

    def test_per_agent_file_has_v1_field_names(self):
        import json
        _, _, debug_dir = run_shim(V2_AGENTS)
        zed = json.loads((debug_dir / "zed.json").read_text())
        self.assertEqual(zed["name"], "zed")
        self.assertEqual(zed["mode"], "subagent")
        self.assertEqual(zed["model"], {"providerID": "anthropic", "modelID": "claude-x"})
        self.assertEqual(zed["prompt"], "hello")
        self.assertEqual(zed["steps"], 7)
        self.assertEqual(zed["options"], {"foo": 1})
        self.assertEqual(zed["temperature"], 0.3)
        self.assertEqual(zed["permission"], [
            {"permission": "bash", "pattern": "git *", "action": "allow"},
            {"permission": "edit", "pattern": "*", "action": "deny"}])
        self.assertEqual(zed["tools"], {"edit": False})  # derived from the edit deny rule; the narrower shell rule adds nothing

    def test_status_file_marks_each_agent_probed_ok(self):
        _, _, debug_dir = run_shim(V2_AGENTS)
        self.assertEqual((debug_dir / "zed.status").read_text().strip(), "0")
        self.assertEqual((debug_dir / "build.status").read_text().strip(), "0")
        self.assertTrue((debug_dir / "build.stderr").exists())

    def test_plugin_chatter_before_the_array_is_tolerated(self):
        import json
        r, listing, _ = run_shim(None, "plugin loaded\n" + json.dumps(V2_AGENTS))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("zed (subagent)", listing.read_text())

    def test_garbage_input_fails_closed(self):
        r, listing, _ = run_shim(None, "not json")
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(listing.exists())

    def test_unsafe_agent_ids_are_rejected_before_anything_is_written(self):
        for bad in ("../escape", "a/b", "", ".hidden", "x y"):
            with self.subTest(bad=bad):
                agents = [V2_AGENTS[0], {**V2_AGENTS[1], "id": bad}]
                r, listing, debug_dir = run_shim(agents)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("unsafe agent id", r.stderr)
                self.assertNotIn("Error:", r.stderr.split("unsafe agent id")[0])  # clear message, not a stack trace
                self.assertFalse(listing.exists())
                self.assertFalse(debug_dir.exists())

    def test_duplicate_ids_are_rejected(self):
        r, listing, _ = run_shim([V2_AGENTS[0], V2_AGENTS[0]])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("duplicate agent id", r.stderr)
        self.assertFalse(listing.exists())

    def test_a_write_failure_is_a_clear_message_not_a_stack_trace(self):
        import json
        out = Path(tempfile.mkdtemp())
        blocker = out / "debug"
        blocker.write_text("a file where the directory should go")
        r = subprocess.run(["node", str(SHIM), str(out / "list.txt"), str(blocker)],
                           input=json.dumps(V2_AGENTS), capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("v2-agents-shim: cannot write", r.stderr)
        self.assertNotIn("    at ", r.stderr)


class AgentsShimWiring(unittest.TestCase):
    text = (MODULES / "59-section-8-9-config-runtime.sh").read_text()

    def test_v2_branch_uses_debug_agents_and_the_shim(self):
        self.assertIn('debug agents', self.text)
        self.assertIn("v2-agents-shim.cjs", self.text)

    def test_a_probe_name_v2_does_not_register_gets_a_clear_message(self):
        self.assertIn("is not registered by OpenCode V2", self.text)

    def test_the_two_shim_steps_report_which_one_failed(self):
        self.assertIn("exited non-zero", self.text)

    def test_v1_branch_still_calls_agent_list(self):
        self.assertIn('"$OC_PROBE" agent list', self.text)


CHECKER = MODULES / "checkers" / "check-parallel-dispatch.py"


def parallel(tool, key, agents=("explore", "general")):
    import json
    lines = []
    for i, name in enumerate(agents):
        lines.append(json.dumps({"part": {"tool": tool, "callID": f"c{i}", "messageID": "m1",
                                           "state": {"input": {key: name}, "status": "completed",
                                                     "time": {"start": 1, "end": 5}}}}))
    path = Path(tempfile.mkdtemp()) / "events.ndjson"
    path.write_text("\n".join(lines))
    return subprocess.run(["python3", str(CHECKER), str(path)], capture_output=True, text=True)


class BehaviouralParsers(unittest.TestCase):
    """V2 renamed the task tool to `subagent` (input key `agent`) and bash to `shell`."""

    def test_v1_task_events_still_pass(self):
        self.assertEqual(parallel("task", "subagent_type").returncode, 0)

    def test_v2_subagent_events_pass(self):
        r = parallel("subagent", "agent")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_positive_control_a_missing_agent_still_fails(self):
        self.assertEqual(parallel("subagent", "agent", agents=("explore",)).returncode, 1)

    def test_the_read_only_probe_treats_shell_and_non_explore_subagents_as_mutation(self):
        text = (MODULES / "61-section-10-behavioural.sh").read_text()
        self.assertIn('"shell"', text)
        self.assertIn('tool in {"task", "subagent"}', text)
        self.assertIn('launch.get("agent")', text)


class SecureServiceProbes(unittest.TestCase):
    text = (MODULES / "60-section-9a-9b-secure-service.sh").read_text()

    def test_the_v1_agent_catalog_probe_is_skipped_on_v2_and_the_github_mcp_probe_is_replaced(self):
        self.assertIn('"${OC_MAJOR:-0}" = "2"', self.text)
        self.assertEqual(self.text.count("skipped: OpenCode V2"), 1)  # 9a: section 9 covers agent registration on V2
        self.assertIn("v2-github-mcp-check.py", self.text)         # 9b: checked against the V2 config and server


class LoaderAndProbeWrapper(unittest.TestCase):
    """Regression: the loader sourced checkers/oc-probe.sh as if it were a section, and its `exec opencode "$@"` replaced
    the finished verifier with a bare `opencode` (the TUI)."""

    def run_loader(self, entries, files):
        entry = (REPO / "verify-workflow.sh").read_text()
        block = entry[entry.index("# BEGIN VERIFY_LOADER"):entry.index("# END VERIFY_LOADER")]
        # drop the digest and unlisted-file checks (the fixture has no manifest); keep the sourcing loop
        loop = block[block.index("for verify_module_entry in \"${VERIFY_MODULES[@]}\"; do\n  case"):]
        root = Path(tempfile.mkdtemp())
        for rel, text in files.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text)
        names = " ".join(f'"{e} x"' for e in entries)
        script = f'VERIFY_MODULE_DIR="{root}"\nVERIFY_MODULES=({names})\n{loop}\n'
        subprocess.run([shutil.which("bash"), "-c", script], capture_output=True, text=True, stdin=subprocess.DEVNULL)
        return root

    def test_sections_are_sourced(self):
        root = self.run_loader(["10-a.sh"], {"10-a.sh": f'touch "{{VERIFY_MODULE_DIR}}/ran-a"\n'.replace("{VERIFY_MODULE_DIR}", "$VERIFY_MODULE_DIR")})
        self.assertTrue((root / "ran-a").exists())

    def test_checker_scripts_are_never_sourced(self):
        root = self.run_loader(
            ["10-a.sh", "checkers/probe.sh"],
            {"10-a.sh": "true\n", "checkers/probe.sh": 'touch "$VERIFY_MODULE_DIR/ran-checker"\n'},
        )
        self.assertFalse((root / "ran-checker").exists())

    def test_the_wrapper_refuses_to_run_without_arguments(self):
        stub = Stub("1.19.5")
        try:
            r = subprocess.run([shutil.which("bash"), str(PROBE)], capture_output=True, text=True, env=stub.env(OC_MAJOR="1"), stdin=subprocess.DEVNULL)
            self.assertNotEqual(r.returncode, 0)
            self.assertEqual([c for c in stub.calls() if c.startswith("ARGS:")], [])  # opencode was not started
        finally:
            stub.close()

    def test_sourcing_the_wrapper_cannot_replace_the_calling_shell(self):
        stub = Stub("1.19.5")
        try:
            script = f'source "{PROBE}"; echo STILL_HERE'
            r = subprocess.run([shutil.which("bash"), "-c", script], capture_output=True, text=True, env=stub.env(OC_MAJOR="1"), stdin=subprocess.DEVNULL)
            self.assertEqual([c for c in stub.calls() if c.startswith("ARGS:")], [])
        finally:
            stub.close()


if __name__ == "__main__":
    unittest.main()
