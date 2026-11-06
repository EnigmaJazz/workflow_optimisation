"""Verifier V2 mode (queue Q44): section 0 checks the V2 config root against a derive dry run instead of repairing V1 files."""
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHECKER = REPO / "verify" / "checkers" / "v2-config-check.py"
SECTION = REPO / "verify" / "50-section-0-recover.sh"


class Fixture:
    """A fake workspace whose derive script prints chosen output, records its argv and exits with a chosen code."""

    def __init__(self, output="", code=0, with_root=True, with_derive=True):
        self.dir = Path(tempfile.mkdtemp())
        self.workspace = self.dir / "ws"
        (self.workspace / "scripts").mkdir(parents=True)
        (self.workspace / "global-config").mkdir()
        self.root = self.dir / "v2root"
        if with_root:
            self.root.mkdir()
        self.argv_log = self.dir / "argv.log"
        if with_derive:
            body = f"import sys\nopen({str(self.argv_log)!r}, 'w').write(' '.join(sys.argv[1:]))\nprint({output!r})\nsys.exit({code})\n"
            (self.workspace / "scripts" / "derive-v2-config.py").write_text(body)

    def run(self):
        proc = subprocess.run([sys.executable, str(CHECKER), str(self.workspace), str(self.dir / "sandbox"), str(self.root)],
                              capture_output=True, text=True)
        return proc.returncode, proc.stdout.strip()


class Checker(unittest.TestCase):
    def test_a_matching_root_is_clean(self):
        code, out = Fixture("[derive-v2] note: x\n[derive-v2] dry-run - nothing was written. Re-run with --apply to write.").run()
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("clean\t"), out)

    def test_drift_is_an_error_naming_files_and_the_fix(self):
        code, out = Fixture("[derive-v2] would replace /r/opencode.json\n[derive-v2] would create /r/plugins/a.ts\n[derive-v2] dry-run - nothing was written.").run()
        self.assertTrue(out.startswith("error\t"), out)
        self.assertIn("2 V2 config file(s) differ", out)
        self.assertIn("opencode.json", out)
        self.assertIn("derive --apply", out)

    def test_the_dry_run_line_is_not_counted_as_drift(self):
        _, out = Fixture("[derive-v2] dry-run - nothing was written. Re-run with --apply to write.").run()
        self.assertTrue(out.startswith("clean\t"), out)

    def test_a_note_that_merely_contains_the_word_would_is_not_drift(self):
        marker = "[derive-v2] dry-run - nothing was written. Re-run with --apply to write."
        _, out = Fixture("[derive-v2] note: native grep: a global ask would expose it to plugin-owned agents\n" + marker).run()
        self.assertTrue(out.startswith("clean\t"), out)
        _, out = Fixture("[derive-v2] note: it would expose x\n[derive-v2] would replace /r/opencode.json\n" + marker).run()
        self.assertIn("1 V2 config file(s) differ", out)
        self.assertIn("opencode.json", out)

    def test_a_change_line_in_an_unknown_shape_is_an_error_never_clean(self):
        marker = "[derive-v2] dry-run - nothing was written. Re-run with --apply to write."
        _, out = Fixture("[derive-v2] would-replace /r/opencode.json\n" + marker).run()
        self.assertTrue(out.startswith("error\tderive printed a change line this check cannot parse"), out)
        _, out = Fixture("[derive-v2] would /r/opencode.json\n" + marker).run()
        self.assertTrue(out.startswith("error\t"), out)

    def test_output_without_the_completion_marker_is_never_clean(self):
        for output in ("", "[derive-v2] note: dropped 1 legacy setting"):
            _, out = Fixture(output).run()
            self.assertTrue(out.startswith("error\tderive gave no dry-run completion marker"), out)

    def test_notes_about_moved_or_kept_settings_are_shown_on_a_clean_result(self):
        marker = "[derive-v2] dry-run - nothing was written."
        _, out = Fixture("[derive-v2] note: moved subagent_depth to experimental.subagent_depth\n[derive-v2] note: agent x mirrored\n" + marker).run()
        self.assertTrue(out.startswith("clean\t"), out)
        self.assertIn("note: moved subagent_depth", out)
        self.assertNotIn("mirrored", out)

    def test_a_derive_failure_is_an_error_with_its_last_line(self):
        _, out = Fixture("[derive-v2] error: plugin entry needs a decision", code=2).run()
        self.assertTrue(out.startswith("error\tderive failed (2)"), out)
        self.assertIn("needs a decision", out)

    def test_a_missing_root_or_script_is_an_error_not_a_pass(self):
        self.assertTrue(Fixture(with_root=False).run()[1].startswith("error\tthe V2 config root does not exist"))
        self.assertTrue(Fixture(with_derive=False).run()[1].startswith("error\tthe derive script is missing"))

    def test_it_never_asks_derive_to_write(self):
        fixture = Fixture("")
        fixture.run()
        argv = fixture.argv_log.read_text()
        self.assertNotIn("--apply", argv)
        self.assertIn(f"--target {fixture.root}", argv)
        self.assertIn(f"--source {fixture.workspace / 'global-config'}", argv)

    def test_the_real_derive_dry_run_is_understood(self):
        # Against the real script and a temp root: an empty root differs from global-config, which must read as drift (not a crash).
        root = Path(tempfile.mkdtemp())
        sandbox = Path.home() / "agent-sandbox-integration"
        if not sandbox.is_dir():
            self.skipTest("the sandbox repository is not present")
        proc = subprocess.run([sys.executable, str(CHECKER), str(REPO), str(sandbox), str(root)], capture_output=True, text=True)
        self.assertTrue(proc.stdout.startswith("error\t"), proc.stdout)
        self.assertIn("differ from global-config", proc.stdout)
        self.assertEqual(list(root.iterdir()), [])  # read-only: nothing was written


class Wiring(unittest.TestCase):
    text = SECTION.read_text()

    def test_the_script_parses(self):
        self.assertEqual(subprocess.run(["bash", "-n", str(SECTION)]).returncode, 0)

    def test_v2_runs_the_checker_and_v1_keeps_every_recovery(self):
        v2, _, v1 = self.text.partition('else\nmkdir -p "$OPENCODE_CONFIG_DIR"')
        self.assertIn('[ "${OC_MAJOR:-0}" = "2" ]', v2)
        self.assertIn("v2-config-check.py", v2)
        self.assertNotIn("recover_opencode_config", v2)
        for call in ("recover_opencode_config", "recover_tui_config", "recover-cli-config.py", "recover_agents_file",
                     "recover_reviewed_router_skills", "recover_systematic_config", "recover_fallback_policy", "LOCAL_AUTO_UPDATE_SURFACE_INVALID"):
            self.assertIn(call, v1, call)
            self.assertEqual(len(re.findall(re.escape(call), self.text)), len(re.findall(re.escape(call), v1)), call)

    def test_the_v1_body_closes_before_the_shared_checks(self):
        self.assertRegex(self.text, r"\nfi\n\n# Muse and pre-V4\.1 DeepSeek models")


if __name__ == "__main__":
    unittest.main()
