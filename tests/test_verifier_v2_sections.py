import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ADAPTER = REPO / "verify/checkers/v2-runtime-config.py"
GOOD = {"plugins": ["@cortexkit/opencode-magic-context@~0.49.34", "file:///plugins/opencode-rate-limit-fallback-mapped/index.ts"], "permission": {"grep": "deny"}, "agent": {"gentle-orchestrator": {"permission": {"grep": "allow"}}}, "mcp": {"github_ro": {}}, "tools": {"github_ro_*": False}}

class RuntimeConfigValidation(unittest.TestCase):
    def run_adapter(self, config):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "opencode.json"
            path.write_text(json.dumps(config))
            return subprocess.run([sys.executable, str(ADAPTER), str(path)], capture_output=True, text=True)

    def test_success_has_empty_stdout_and_stderr_note(self):
        result = self.run_adapter(GOOD)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("V2 runtime invariants passed", result.stderr)

    def test_magic_plugin_requires_scoped_pin(self):
        for ref in ("opencode-magic-context@~1.2.3", "@foreign/opencode-magic-context@~1.2.3"):
            config = json.loads(json.dumps(GOOD)); config["plugins"][0] = ref
            result = self.run_adapter(config)
            self.assertEqual(result.returncode, 1); self.assertIn("V2_RUNTIME_CONFIG_INVALID:", result.stderr)
        self.assertEqual(self.run_adapter(GOOD).returncode, 0)

    def test_fallback_reference_forms(self):
        for ref in ("file:///plugins/opencode-rate-limit-fallback-mapped", "file:///plugins/opencode-rate-limit-fallback-mapped/index.ts"):
            config = json.loads(json.dumps(GOOD)); config["plugins"][1] = ref
            self.assertEqual(self.run_adapter(config).returncode, 0)
        config = json.loads(json.dumps(GOOD)); config["plugins"][1] += "/other"
        result = self.run_adapter(config)
        self.assertEqual(result.returncode, 1); self.assertIn("V2_RUNTIME_CONFIG_INVALID:", result.stderr)

    def test_each_config_invariant_rejects_a_mutation(self):
        mutations = (lambda c: c["plugins"].pop(), lambda c: c["plugins"].append(c["plugins"][0]), lambda c: c["plugins"].__setitem__(1, "file:///bad"), lambda c: c["permission"].update(grep="allow"), lambda c: c["agent"]["gentle-orchestrator"]["permission"].update(grep="deny"), lambda c: c["mcp"].update(github_ro=[]), lambda c: c["tools"].update({"github_ro_*": True}))
        for mutate in mutations:
            config = json.loads(json.dumps(GOOD)); mutate(config); result = self.run_adapter(config)
            self.assertEqual(result.returncode, 1); self.assertEqual(result.stdout, ""); self.assertIn("V2_RUNTIME_CONFIG_INVALID:", result.stderr)

class VerifierSkipBehavior(unittest.TestCase):
    def test_env_initializes_skipped_messages_for_set_u_summary(self):
        source = (REPO / "verify/10-env.sh").read_text()
        self.assertIn("SKIPPED_MESSAGES=()", source,
                      "the summary expands SKIPPED_MESSAGES under set -u")

    def test_skip_helper_records_and_prints(self):
        source = (REPO / "verify/20-helpers.sh").read_text(); start = source.index("skip() {"); function = source[start:source.index("\n}", start)+3]
        script = function + '\nSKIPPED_MESSAGES=(); skip "sample"; printf "COUNT=%s MESSAGE=%s\\n" "${#SKIPPED_MESSAGES[@]}" "${SKIPPED_MESSAGES[0]}"\n'
        result = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0); self.assertIn("SKIPPED (V2: sample)", result.stdout); self.assertIn("COUNT=1 MESSAGE=sample", result.stdout)

    def test_extracted_section_9_v2_and_v1_controls(self):
        source = (REPO / "verify/59-section-8-9-config-runtime.sh").read_text(); start = source.index('      RUNTIME_CHECK_CONFIG="$RUNTIME_CONFIG_FILE"'); end = source.index("\n    fi", start); branch = source[start:end]
        v2 = 'OC_MAJOR=2; RUNTIME_CONFIG_FILE=config; TMP_DIR=/tmp; VERIFY_MODULE_DIR=verify; SYSTEMATIC_NODE_MODULES=; JS_RUNTIME=node; RUNTIME_AGENT_CHECKER=checker; SYSTEMATIC_CONFIG=x; ACTIVE_AGENTS=x; AGENT_LIST_OUT=x; DEBUG_AGENT_DIR=x; FALLBACK_POLICY_SOURCE=x; WORKSPACE=x; FAIL=0; FAIL_MESSAGES=(); SKIPPED_MESSAGES=(); python3() { return 0; }; node() { echo CHECKER_INVOKED; }; sed() { :; }; fail() { FAIL=1; }; skip() { printf "   SKIPPED (V2: %s)\\n" "$*"; }; ' + branch.replace('if ! python3 "$VERIFY_MODULE_DIR/checkers/v2-runtime-config.py" "$RUNTIME_CONFIG_FILE" >"$RUNTIME_CHECK_CONFIG" 2>"$TMP_DIR/v2-runtime-config-notes"; then', 'if ! true; then').replace('sed \'s/^/   info: /\' "$TMP_DIR/v2-runtime-config-notes"', ':')
        result = subprocess.run(["bash", "-c", v2], capture_output=True, text=True, cwd=REPO)
        self.assertEqual(result.returncode, 0); self.assertEqual(result.stdout.count("SKIPPED (V2: SECTION_9_RUNTIME_AGENT_CHECKER_NOT_RUN"), 1); self.assertNotIn("ok: runtime agent registration", result.stdout)
        self.assertNotIn("CHECKER_INVOKED", result.stdout)
        v1 = 'OC_MAJOR=1; RUNTIME_CONFIG_FILE=config; TMP_DIR=/tmp; VERIFY_MODULE_DIR=verify; SYSTEMATIC_NODE_MODULES=; JS_RUNTIME=echo; RUNTIME_AGENT_CHECKER=CHECKER_INVOKED; SYSTEMATIC_CONFIG=x; ACTIVE_AGENTS=x; AGENT_LIST_OUT=x; DEBUG_AGENT_DIR=x; FALLBACK_POLICY_SOURCE=x; WORKSPACE=x; FAIL=0; FAIL_MESSAGES=(); SKIPPED_MESSAGES=(); fail() { FAIL=1; }; skip() { echo "SKIPPED (V2: $*)"; }; ' + branch
        result = subprocess.run(["bash", "-c", v1], capture_output=True, text=True, cwd=REPO)
        self.assertIn("CHECKER_INVOKED", result.stdout); self.assertNotIn("SKIPPED (V2:", result.stdout)

    def test_summary_failure_only_preserves_exact_v1_prune_message(self):
        result = self.run_summary('1', '()')
        self.assertEqual(result.returncode, 1)
        self.assertIn("   skipped: workflow health has failures; no cleanup approval issued", result.stdout)
        self.assertNotIn("required checks were skipped; no cleanup approval issued", result.stdout)
        self.assertNotIn("CACHE_PRUNE_APPROVED", result.stdout)

    def test_summary_failures_and_skips_report_failure_as_dominant_without_approval(self):
        result = self.run_summary('1', '("sample skip")')
        self.assertEqual(result.returncode, 1)
        self.assertIn("Failed checks (1):", result.stdout)
        self.assertIn("sample failure", result.stdout)
        self.assertIn("VERIFICATION_INCOMPLETE", result.stdout)
        self.assertIn("   skipped: workflow health has failures; no cleanup approval issued", result.stdout)
        self.assertNotIn("required checks were skipped; no cleanup approval issued", result.stdout)
        self.assertNotIn("All checks passed", result.stdout)
        self.assertNotIn("CACHE_PRUNE_APPROVED", result.stdout)

    def test_summary_skips_only_are_incomplete_without_approval(self):
        result = self.run_summary('0', '("sample skip")')
        self.assertEqual(result.returncode, 3)
        self.assertIn("   skipped: required checks were skipped; no cleanup approval issued", result.stdout)
        self.assertNotIn("workflow health has failures; no cleanup approval issued", result.stdout)
        self.assertIn("VERIFICATION_INCOMPLETE", result.stdout)
        self.assertNotIn("All checks passed", result.stdout)
        self.assertNotIn("CACHE_PRUNE_APPROVED", result.stdout)

    def test_summary_empty_run_keeps_exact_v1_success_banner(self):
        result = self.run_summary('0', '()')
        self.assertEqual(result.returncode, 0)
        self.assertIn("== All checks passed — workflow setup intact ==", result.stdout)

    def test_health_plugin_classifies_exit_three_as_incomplete(self):
        source = (REPO / "global-config/plugins/workflow-health-check.ts").read_text()
        start = source.index("  } catch (err) {")
        end = source.index("\n  }\n}", start) + 5
        catch_block = source[start:end]
        self.assertIn("if (e.code === 3)", catch_block)
        self.assertIn('state: "incomplete"', catch_block)
        self.assertIn("VERIFICATION_INCOMPLETE", catch_block)
        self.assertNotIn('state: "failed"', catch_block[:catch_block.index("const fallback")])
        self.assertIn("state: \"failed\"", catch_block[catch_block.index("const fallback"):])

    def run_summary(self, fail, skips):
        source = (REPO / "verify/62-section-11-summary.sh").read_text()
        script = (f'FAIL={fail}; FAIL_MESSAGES=(); [ "$FAIL" -eq 0 ] || FAIL_MESSAGES+=("sample failure"); '
                  f'AUTO_REPAIRED=0; SKIPPED_MESSAGES={skips}; C_BOLD_RED=; C_RESET=; '
                  'write_cache_prune_approval() { echo CACHE_PRUNE_APPROVED; return 0; }; ' + source)
        return subprocess.run(["bash", "-c", script], capture_output=True, text=True)

class GithubResultClassification(unittest.TestCase):
    def test_github_probe_classification_stays_wired(self):
        source = (REPO / "verify/60-section-9a-9b-secure-service.sh").read_text()
        self.assertIn('2>"$TMP_DIR/github-ro-checker.stderr"', source)
        self.assertNotIn("2>&1", source[source.index("# --- 9b."):])

class ManifestHasNoBytecode(unittest.TestCase):
    def test_manifest_has_no_python_bytecode_row(self):
        source = (REPO / "verify-workflow.sh").read_text(); block = source[source.index("# BEGIN VERIFY_MODULES"):source.index("# END VERIFY_MODULES")]
        self.assertIn('"checkers/v2-runtime-config.py ', block); self.assertNotIn("__pycache__", block); self.assertNotIn(".pyc", block)

if __name__ == "__main__": unittest.main()
