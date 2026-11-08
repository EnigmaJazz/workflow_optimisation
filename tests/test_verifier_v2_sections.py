import json
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
