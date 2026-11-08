import json
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ADAPTER = REPO / "verify" / "checkers" / "v2-runtime-config.py"
DERIVE = REPO / "scripts" / "derive-v2-config.py"
SPEC = importlib.util.spec_from_file_location("derive_v2_config", DERIVE)
DERIVATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DERIVATION)


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
        config = self.derived_agent_inventory()
        worker = config["agent"]["gentle-ai-worker"]
        result = self.run_adapter(config)
        self.assertEqual(result.returncode, 0, result.stderr)
        projected_agents = json.loads(result.stdout)["agent"]
        self.assertIn("gentle-ai-worker", projected_agents)
        self.assertEqual(projected_agents["gentle-ai-worker"], worker)
        for target in DERIVATION.ACCESS_MIRRORS:
            self.assertNotIn(target, projected_agents)
        for name in config["agent"]:
            if name.endswith(DERIVATION.ASTRA_SUFFIX):
                self.assertNotIn(name, projected_agents)

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
        source = json.loads((REPO / "global-config" / "opencode.json").read_text())
        config = json.loads(json.dumps(GOOD))
        agents = {"gentle-orchestrator": config["agent"]["gentle-orchestrator"]}
        agents.update({name: json.loads(json.dumps(entry)) for name, entry in source["agent"].items()})
        derived = {"agent": agents}
        DERIVATION.mirror_agent_access(derived)
        DERIVATION.add_v2_astra_aliases(derived)
        config["agent"] = agents
        return config

    def assert_stays_projected(self, config, name):
        result = self.run_adapter(config)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(name, json.loads(result.stdout)["agent"])

    def test_prefix_only_reported_host_review_grant_nonmirror_stays_projected(self):
        """Non-mirror host_review_acknowledge_approved grant must reach the checker."""
        config = json.loads(json.dumps(GOOD))
        config["agent"]["correctness-reviewer"] = {
            "permission": {"host_review_acknowledge_approved": "allow"},
            "tools": {"host_review_acknowledge_approved": True},
        }
        self.assert_stays_projected(config, "correctness-reviewer")

    def test_other_nonmirror_grant_and_mirror_added_host_grant_stay_projected(self):
        """Non-mirror host_plan_write and extended mirror grants remain visible."""
        config = self.derived_agent_inventory()
        config["agent"]["custom-reviewer"] = {"permission": {"host_plan_write": "allow"}}
        config["agent"]["systematic-implementer"]["permission"]["host_review_acknowledge_approved"] = "allow"
        self.assert_stays_projected(config, "custom-reviewer")
        self.assert_stays_projected(config, "systematic-implementer")

    def test_altered_mirror_grant_value_stays_projected(self):
        """A mirror-named entry that changes sandbox_write authority remains visible."""
        config = self.derived_agent_inventory()
        config["agent"]["systematic-implementer"]["permission"]["sandbox_write"] = "deny"
        self.assert_stays_projected(config, "systematic-implementer")

    def test_reordered_permission_map_stays_projected(self):
        """Set-equal reordered mirror rules remain visible because last-match wins."""
        config = self.derived_agent_inventory()
        reference = config["agent"]["gentle-ai-worker"]
        reference["permission"]["host_review_acknowledge_*"] = "allow"
        reference["permission"]["host_review_acknowledge_approved"] = "deny"
        rules = {key: value for key, value in reference["permission"].items()
                 if key.startswith(DERIVATION.MIRRORED_PREFIXES)}
        config["agent"]["systematic-implementer"]["permission"] = dict(reversed(list(rules.items())))
        self.assert_stays_projected(config, "systematic-implementer")

    def test_ineligible_and_altered_astra_aliases_stay_projected(self):
        """Primary-mode bases and aliases with changed model/variant/hidden are not derivations."""
        config = self.derived_agent_inventory()
        base = json.loads(json.dumps(config["agent"]["gentle-ai-worker"]))
        base.update({"model": DERIVATION.ASTRA_SOL_MODEL, "mode": "primary"})
        config["agent"]["primary-base"] = base
        config["agent"]["primary-base-astra"] = {"model": DERIVATION.ASTRA_MODEL, "hidden": True}
        alias_name = next(name for name in config["agent"] if name.endswith(DERIVATION.ASTRA_SUFFIX))
        self.assert_stays_projected(config, "primary-base-astra")
        for field, value in (("model", "altered/model"), ("variant", "altered"), ("hidden", False)):
            altered = json.loads(json.dumps(config))
            altered["agent"][alias_name][field] = value
            self.assert_stays_projected(altered, alias_name)

    def test_real_derived_mirror_and_alias_are_removed_with_bases_unchanged(self):
        """Exact real derivation entries are removed while their source agents remain."""
        config = self.derived_agent_inventory()
        originals = json.loads(json.dumps(config["agent"]))
        result = self.run_adapter(config)
        self.assertEqual(result.returncode, 0, result.stderr)
        projected = json.loads(result.stdout)["agent"]
        for name, reference in DERIVATION.ACCESS_MIRRORS.items():
            self.assertNotIn(name, projected)
            self.assertEqual(projected[reference], originals[reference])
            self.assertIn(f"skipped (V2): {name} = mirror of {reference}", result.stderr)
        aliases = [name for name in originals if name.endswith(DERIVATION.ASTRA_SUFFIX)]
        self.assertTrue(aliases)
        for name in aliases:
            self.assertNotIn(name, projected)
            base = name[:-len(DERIVATION.ASTRA_SUFFIX)]
            self.assertEqual(projected[base], originals[base])
            self.assertIn(f"skipped (V2): {name} = Astra alias of {base}", result.stderr)

    def test_malformed_astra_and_mirror_candidates_stay_visible(self):
        """Non-derived alias and mirror-shaped entries remain visible instead of being dropped."""
        config = self.derived_agent_inventory()
        config["agent"]["systematic-implementer"].update(permission={}, tools={})
        result = self.run_adapter(config)
        self.assertEqual(result.returncode, 0, result.stderr)
        agents = json.loads(result.stdout)["agent"]
        self.assertIn("systematic-implementer", agents)

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
