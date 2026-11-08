import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ADAPTER = REPO / "verify" / "checkers" / "v2-runtime-config.py"


GOOD = {
    "plugins": [
        "opencode-magic-context@~1.2.3",
        "file:///plugins/opencode-rate-limit-fallback-mapped/index.ts",
    ],
    "permission": {"grep": "deny"},
    "agent": {"gentle-orchestrator": {"permission": {"grep": "allow"}}},
    "mcp": {"github_ro": {"url": "https://api.githubcopilot.com/mcp/readonly"}},
    "tools": {"github_ro_*": False},
}


class RuntimeProjection(unittest.TestCase):
    def run_adapter(self, config):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "opencode.json"
            path.write_text(json.dumps(config))
            return subprocess.run([sys.executable, str(ADAPTER), str(path)], capture_output=True, text=True)

    def test_valid_v2_config_projects_for_the_v1_checker(self):
        result = self.run_adapter(GOOD)
        self.assertEqual(result.returncode, 0, result.stderr)
        projected = json.loads(result.stdout)
        self.assertEqual(projected["plugin"], [
            "opencode-magic-context@1.2.3",
            "file:///plugins/opencode-rate-limit-fallback-mapped/index.ts",
        ])
        self.assertNotIn("plugins", projected)
        self.assertEqual(projected["permission"]["grep"], "ask")
        self.assertEqual(projected["agent"]["gentle-orchestrator"]["permission"]["grep"], "allow")

    def test_real_derived_worker_and_access_mirrors_project_without_dropping_base(self):
        source = json.loads((REPO / "global-config" / "opencode.json").read_text())
        worker = source["agent"]["gentle-ai-worker"]
        access_mirrors = {
            "systematic-implementer": "gentle-ai-worker",
            "bug-reproduction-validator": "gentle-ai-worker",
            "pr-comment-resolver": "gentle-ai-worker",
            "design-iterator": "gentle-ai-worker",
        }
        config = json.loads(json.dumps(GOOD))
        agents = {"gentle-ai-worker": json.loads(json.dumps(worker))}
        for target, reference in access_mirrors.items():
            ref = agents[reference]
            mirror = {}
            for field in ("permission", "tools"):
                rules = {key: value for key, value in (ref.get(field) or {}).items()
                         if key.startswith(("sandbox_", "host_"))}
                if rules:
                    mirror[field] = rules
            agents[target] = mirror
        alias = json.loads(json.dumps(worker))
        alias.update({
            "description": f"{worker.get('description') or 'gentle-ai-worker'} — selectable Astra upgrade",
            "hidden": True,
            "model": "openai/gpt-6-astra",
            "variant": "high",
        })
        agents["gentle-ai-worker-astra"] = alias
        agents["gentle-orchestrator"] = config["agent"]["gentle-orchestrator"]
        config["agent"] = agents

        result = self.run_adapter(config)
        self.assertEqual(result.returncode, 0, result.stderr)
        projected = json.loads(result.stdout)
        projected_agents = projected["agent"]
        self.assertIn("gentle-ai-worker", projected_agents)
        for target in access_mirrors:
            self.assertNotIn(target, projected_agents)
        self.assertNotIn("gentle-ai-worker-astra", projected_agents)
        self.assertEqual(projected_agents["gentle-ai-worker"], worker)

    def test_real_derived_plugin_refs_project_to_v1_shapes(self):
        source = json.loads((REPO / "global-config" / "opencode.json").read_text())
        plugins = source["plugin"]
        derived = []
        for ref in plugins:
            if "opencode-magic-context@" in ref:
                name, version = ref.rsplit("@", 1)
                derived.append(f"{name}@~{version}")
            elif "opencode-rate-limit-fallback-mapped" in ref:
                derived.append(f"file://{REPO}/vendor/opencode-rate-limit-fallback-mapped")
            else:
                derived.append(ref)
        config = dict(GOOD)
        config["plugins"] = [ref for ref in derived if "opencode-magic-context@" in ref or "opencode-rate-limit-fallback-mapped" in ref]
        result = self.run_adapter(config)
        self.assertEqual(result.returncode, 0, result.stderr)
        projected = json.loads(result.stdout)
        self.assertEqual(projected["plugin"], [
            "@cortexkit/opencode-magic-context@0.49.34",
            f"file://{REPO}/vendor/opencode-rate-limit-fallback-mapped/index.ts",
        ])

    def test_each_v2_runtime_invariant_has_a_failing_mutation_control(self):
        mutations = (
            lambda config: config["plugins"].pop(),
            lambda config: config["plugins"].append("opencode-magic-context@~1.2.3"),
            lambda config: config["plugins"].__setitem__(1, "file:///plugins/opencode-rate-limit-fallback-mapped/elsewhere"),
            lambda config: config["permission"].update(grep="allow"),
            lambda config: config["agent"]["gentle-orchestrator"]["permission"].update(grep="deny"),
            lambda config: config["mcp"].pop("github_ro"),
            lambda config: config["tools"].update({"github_ro_*": True}),
        )
        for mutate in mutations:
            config = json.loads(json.dumps(GOOD))
            mutate(config)
            result = self.run_adapter(config)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertIn("V2_RUNTIME_CONFIG_", result.stderr)


    def derived_agent_inventory(self):
        config = json.loads(json.dumps(GOOD))
        config["agent"].update({
            "worker": {"model": "openai/gpt-6.1-sol", "permission": {"read": "allow"}, "tools": {"read": True}},
            "worker-astra": {"hidden": True, "model": "openai/gpt-6-astra", "permission": {"read": "allow"}, "tools": {"read": True}},
            "systematic-implementer": {"description": "V2 access mirror", "permission": {"sandbox_read": "allow", "host_review_status": "deny"}, "tools": {"sandbox_read": True, "host_review_status": False}},
            "systematic-pinned": {"permission": {"read": "allow"}, "tools": {"read": True}},
        })
        return config

    def test_complete_derived_agent_inventory_is_projected_without_v2_only_entries(self):
        result = self.run_adapter(self.derived_agent_inventory())
        self.assertEqual(result.returncode, 0, result.stderr)
        agents = json.loads(result.stdout)["agent"]
        self.assertIn("worker", agents)
        self.assertIn("systematic-pinned", agents)
        self.assertNotIn("worker-astra", agents)
        self.assertNotIn("systematic-implementer", agents)
        self.assertIn("skipped (V2): Astra aliases (1): worker-astra", result.stderr)
        self.assertIn("skipped (V2): Systematic access mirrors (1): systematic-implementer", result.stderr)

    def test_mirror_shaped_entry_with_nonprefixed_rule_stays_in_projection(self):
        config = self.derived_agent_inventory()
        config["agent"]["systematic-implementer"]["tools"]["read"] = True
        result = self.run_adapter(config)
        self.assertEqual(result.returncode, 0, result.stderr)
        projected = json.loads(result.stdout)
        self.assertIn("systematic-implementer", projected["agent"])
        self.assertTrue(projected["agent"]["systematic-implementer"]["tools"]["read"])

    def test_invalid_v2_agent_constructs_fail_with_named_errors(self):
        mutations = (
            (lambda c: c["agent"].__setitem__("orphan-astra", {"hidden": True, "model": "m", "permission": {}, "tools": {}}), "base agent"),
            (lambda c: c["agent"]["worker-astra"]["permission"].update(read="deny"), "permission"),
            (lambda c: c["agent"]["systematic-implementer"].update(permission={}, tools={}), "at least one rule"),
        )
        for mutate, detail in mutations:
            with self.subTest(detail=detail):
                config = self.derived_agent_inventory()
                mutate(config)
                result = self.run_adapter(config)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn("V2_RUNTIME_CONFIG_INVALID:", result.stderr)

    def test_real_runtime_checker_retains_pinned_systematic_positive_control_when_node_can_spawn(self):
        config = self.derived_agent_inventory()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "opencode.json"
            path.write_text(json.dumps(config))
            projection = self.run_adapter(config)
            self.assertEqual(projection.returncode, 0, projection.stderr)
            projected_path = Path(tmp) / "projected.json"
            projected_path.write_text(projection.stdout)
            agents_root = Path(tmp) / "agents"
            (agents_root / "workflow").mkdir(parents=True)
            (agents_root / "workflow" / "systematic-pinned.md").write_text("---\ntools: read\n---\n")
            agent_list = Path(tmp) / "agents.txt"
            agent_list.write_text("")
            debug_dir = Path(tmp) / "debug"
            debug_dir.mkdir()
            systematic_config = Path(tmp) / "systematic.jsonc"
            systematic_config.write_text("{}")
            fallback_policy = Path(tmp) / "fallback.json"
            fallback_policy.write_text("{}")
            node_modules = Path(tmp) / "node_modules"
            parser = node_modules / "jsonc-parser"
            parser.mkdir(parents=True)
            (parser / "index.js").write_text("exports.parse = (text) => JSON.parse(text)\n")
            env = {**os.environ, "SYSTEMATIC_NODE_MODULES": str(node_modules)}
            try:
                result = subprocess.run([
                    "node", str(REPO / "verify/checkers/check-runtime-agents.cjs"),
                    str(systematic_config), str(agents_root), str(agent_list), str(debug_dir),
                    str(projected_path), str(fallback_policy), tmp,
                ], capture_output=True, text=True, env=env)
            except OSError as exc:
                if isinstance(exc, PermissionError) and exc.errno == 13:
                    self.skipTest(f"node could not be spawned: {exc}")
                raise
        output = result.stdout + result.stderr
        self.assertNotIn("ASTRA_ALIAS_MUST_NOT_BE_PINNED_IN_OPENCODE_CONFIG", output)
        self.assertIn("SYSTEMATIC_AGENT_SHADOWED", output)


class ManifestHasNoBytecode(unittest.TestCase):
    def test_manifest_lists_checkers_but_never_python_bytecode(self):
        entry = (REPO / "verify-workflow.sh").read_text()
        block = entry[entry.index("# BEGIN VERIFY_MODULES"):entry.index("# END VERIFY_MODULES")]
        self.assertIn('"checkers/v2-runtime-config.py ', block)
        self.assertNotIn("__pycache__", block)
        self.assertNotIn(".pyc", block)


class GithubResultClassification(unittest.TestCase):
    def test_clean_survives_noise_and_a_real_error_still_fails(self):
        source = (REPO / "verify" / "60-section-9a-9b-secure-service.sh").read_text()
        start = source.index("classify_github_mcp_result() {")
        end = source.index("\n}\n", start) + 3
        function = source[start:end]
        script = function + '\nFAIL=0; FAIL_MESSAGES=(); C_RED=; C_RESET=; fail() { FAIL=1; FAIL_MESSAGES+=("$*"); }; classify_github_mcp_result "$1"; printf "FAIL=%s\\n" "$FAIL"\n'
        clean = subprocess.run(["bash", "-c", script, "classify", "clean\tconnected"], capture_output=True, text=True)
        self.assertEqual(clean.returncode, 0, clean.stderr)
        self.assertIn("FAIL=0", clean.stdout)
        error = subprocess.run(["bash", "-c", script, "classify", "error\tGITHUB_RO_NOT_CONNECTED"], capture_output=True, text=True)
        self.assertEqual(error.returncode, 0, error.stderr)
        self.assertIn("FAIL=1", error.stdout)
        section = source[source.index("# --- 9b."):]
        wiring = section[section.index('elif [ "${OC_MAJOR:-0}" = "2" ]; then'):section.index("\nelse\n", section.index('elif [ "${OC_MAJOR:-0}" = "2" ]; then'))]
        self.assertIn('2>"$TMP_DIR/github-ro-checker.stderr"', wiring)
        self.assertNotIn("2>&1", wiring)


if __name__ == "__main__":
    unittest.main()
